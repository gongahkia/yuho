{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Compile
  ( CompiledAnalysis, compileAnalysis, compiledRequest, compiledSnapshot
  , compiledRequirements, compiledIdentities, compiledSources, compiledSourceMappings
  , compiledValidated, byteSpan ) where

import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Types
import Yuho.Authoring.Snapshot (makeSnapshot)
import Yuho.Authoring.Validate
import qualified Yuho.Core.Types as Core
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Types (ValidatedProof, suppliedStatusJson)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

-- Constructor intentionally hidden: callers cannot replace an artifact's
-- request while keeping its validated representation or immutable snapshot.
data CompiledAnalysis = CompiledAnalysis BS.ByteString Snapshot [RequirementMapping]
  [IdentityMapping] [GeneratedSource] [SourceMapping] ValidatedProof

compiledRequest :: CompiledAnalysis -> BS.ByteString
compiledRequest (CompiledAnalysis value _ _ _ _ _ _) = value
compiledSnapshot :: CompiledAnalysis -> Snapshot
compiledSnapshot (CompiledAnalysis _ value _ _ _ _ _) = value
compiledRequirements :: CompiledAnalysis -> [RequirementMapping]
compiledRequirements (CompiledAnalysis _ _ value _ _ _ _) = value
compiledIdentities :: CompiledAnalysis -> [IdentityMapping]
compiledIdentities (CompiledAnalysis _ _ _ value _ _ _) = value
compiledSources :: CompiledAnalysis -> [GeneratedSource]
compiledSources (CompiledAnalysis _ _ _ _ value _ _) = value
compiledSourceMappings :: CompiledAnalysis -> [SourceMapping]
compiledSourceMappings (CompiledAnalysis _ _ _ _ _ value _) = value
compiledValidated :: CompiledAnalysis -> ValidatedProof
compiledValidated (CompiledAnalysis _ _ _ _ _ _ value) = value

byteSpan :: Text -> Int -> Int -> TextSpan
byteSpan content first lastOffset = TextSpan first lastOffset line column lastLine lastColumn
  where
    bytes = Encoding.encodeUtf8 content
    position offset = BS.foldl' (\(l,c) b -> if b == 10 then (l+1,1) else (l,c+1))
      (1,1) (BS.take offset bytes)
    (line,column) = position first
    (lastLine,lastColumn) = position lastOffset

spanJson :: TextSpan -> J
spanJson s = JObj [("start",number (start s)),("end",number (end s)),
  ("start_line",number (startLine s)),("start_col",number (startColumn s)),
  ("end_line",number (endLine s)),("end_col",number (endColumn s))]
  where number = JNum . toInteger

compileAnalysis :: AuthoringDocument -> Text -> Either [AuthoringDiagnostic] CompiledAnalysis
compileAnalysis doc key = do
  let validation = validateBindings doc key
  if analysisReady validation then pure () else Left (validationDiagnostics validation)
  analysis <- maybe (Left [issue "ATARGET" "/documentAnalyses" [key] "analysis not found"])
    Right (findAnalysis doc key)
  let law = documentLaw doc
      occurrences = selectedOccurrences doc analysis
      selected = [a | ref <- analysisAssessments analysis,
        a <- documentAssessments doc, assessmentId a == ref]
      rules = nub (analysisTarget analysis : map occurrenceRule occurrences)
      indexedRules = zip rules [0 :: Int ..]
      namespace = if documentFormat doc == linkedAuthoringFormat
        then "linked-" <> Text.take 20 (snapshotId snapshot) <> "-" else ""
      ruleIds = Map.fromList [(r,namespace <> "rule:" <> decimal i) | (r,i) <- indexedRules]
      branchIds = Map.fromList [(r,namespace <> "branch:" <> decimal i) | (r,i) <- indexedRules]
      ruleIdFor r = Map.findWithDefault "invalid:rule" r ruleIds
      branchIdFor r = Map.findWithDefault "invalid:branch" r branchIds
      selectedFor o = find ((== nodeId (occurrenceNode o)) . assessmentInput) selected
      mappings = [RequirementMapping (nodeId (occurrenceNode o)) (occurrencePath o)
        (occurrenceRule o) (namespace <> "requirement:" <> decimal i) (ruleIdFor (occurrenceRule o))
        (branchIdFor (occurrenceRule o)) (assessmentId <$> selectedFor o)
        ((const (namespace <> "assignment:" <> decimal i)) <$> selectedFor o)
        | (o,i) <- zip occurrences [0 :: Int ..]]
      -- Each record is generated compiler material. Original anchors are only
      -- in the sidecar; none are claimed as positions in these generated texts.
      lawChunks = [(nodeId n <> "\n" <> maybe "" id (nodeQuotation n) <> "\n", n)
        | o <- occurrences, let n = occurrenceNode o]
      statusChunks = [(Encoding.decodeUtf8 (encodeRecord a) <> "\n",a) | a <- selected]
      lawText = Text.concat (map fst lawChunks)
      statusText = Text.concat (map fst statusChunks)
      lawSpans = chunkSpans lawText lawChunks (nodeId . snd)
      statusSpans = chunkSpans statusText statusChunks (assessmentId . snd)
      whole = byteSpan lawText 0 (BS.length (Encoding.encodeUtf8 lawText))
      lawSpanFor o = Map.findWithDefault whole (nodeId (occurrenceNode o)) lawSpans
      statusSpanFor a = Map.findWithDefault (byteSpan statusText 0 0) (assessmentId a) statusSpans
      lawSource = GeneratedSource "source:authoring-law" "generated_law_projection" lawText
        (map (nodeId . occurrenceNode) occurrences)
      statusSource = GeneratedSource "source:authoring-assessments" "generated_assessment_projection"
        statusText (map assessmentId selected)
      generated = [lawSource,statusSource]
      paired = zip occurrences mappings
      requirementValue o mapping =
        let n = occurrenceNode o
            kind = if nodeKind n == "input" then "leaf" else nodeKind n
            children = [(child,m) | (child,m) <- paired,
              occurrenceRule child == occurrenceRule o,
              parentOccurrence occurrences child == Just o]
        in JObj ([("id",JStr (mappedKernelRequirement mapping)),("kind",JStr kind),
          ("path",JArr [JStr (branchIdFor (occurrenceRule o))]),
          ("span",spanJson (if kind == "leaf" then lawSpanFor o else whole))]
          ++ if kind == "leaf" then [] else
            [("members",JArr [requirementValue child m | (child,m) <- children])])
      guards = [e | e <- lawEdges law, edgeFrom e == analysisTarget analysis,
        edgeKind e == "exception"]
      guardId e = namespace <> "guard:" <> sha256Text (Encoding.encodeUtf8 (edgeId e))
      registry = [JObj [("id",JStr (ruleIdFor r)),("source_id",JStr (generatedSourceId lawSource)),
        ("program",JObj [("id",JStr (branchIdFor r)),
          ("path",JArr [JStr (branchIdFor r)]),("span",spanJson whole),
          ("definitions",JBool False),("children",JArr []),("penalties",JArr []),
          ("requirements",JArr [requirementValue o m | (o,m) <- paired,
            occurrenceRule o == r, parentOccurrence occurrences o == Nothing])]),
        ("exceptions",JArr [JObj [("id",JStr (guardId e)),
          ("branch_id",JStr (branchIdFor r)),("source_id",JStr (generatedSourceId lawSource)),
          ("span",spanJson whole),("effect",JStr "defeat"),
          ("guard",JObj [("kind",JStr "is_infringed"),("target",JStr (ruleIdFor (edgeTo e)))])]
          | e <- guards, edgeFrom e == r])]
        | r <- rules]
      facts = JObj [(mappedKernelRequirement m,JObj
        [("proof_status",suppliedStatusJson (classificationStatus (assessmentClassification a))),
         ("status_source",JObj [("assignment_id",JStr assignment),
           ("issuer_label",JStr (assessmentIssuer a)),("origin",JStr (assessmentOrigin a)),
           ("source_id",JStr (generatedSourceId statusSource)),("span",spanJson (statusSpanFor a))])])
        | (o,m) <- paired, Just a <- [selectedFor o], Just assignment <- [mappedAssignment m]]
      request = JObj [("protocol",JStr "yuho.kernel-protocol/v1"),("request_id",JStr "A00"),
        ("operation",JStr "evaluate"),("input_schema",JStr "yuho.kernel-input/v1"),
        ("fragment",JStr evaluatorProfile),("root_rule",JStr (ruleIdFor (analysisTarget analysis))),
        ("policy",JObj [("max_nodes",JNum 1024),
          ("reference_date",JStr (Text.pack (show (analysisReferenceDate analysis))))]),
        ("sources",JArr (map sourceValue generated)),("registry",JArr registry),("facts",facts)]
      identities = concat
        [[IdentityMapping (ruleIdFor r) "rule" [r],IdentityMapping (branchIdFor r) "branch" [r]] | r <- rules]
        ++ [IdentityMapping (mappedKernelRequirement m) "requirement"
          (mappedNode m : mappedOccurrence m ++ map nodeId (occurrenceDefinitions doc (mappedOccurrence m))) | m <- mappings]
        ++ [IdentityMapping assignment "assignment" [a] | m <- mappings,
             Just assignment <- [mappedAssignment m], Just a <- [mappedAssessment m]]
        ++ [IdentityMapping (guardId e) "exception" [edgeId e,edgeFrom e,edgeTo e] | e <- guards]
        ++ [IdentityMapping (generatedSourceId s) "source" (generatedSourceObjects s) | s <- generated]
      sourceMappings = [SourceMapping (mappedKernelRequirement m) (generatedSourceId lawSource)
        (if nodeKind (occurrenceNode o) == "input" then lawSpanFor o else whole)
        (mappedNode m : map nodeId (occurrenceDefinitions doc (mappedOccurrence m)))
        (nodeSources (occurrenceNode o) ++ concatMap nodeSources
          (occurrenceDefinitions doc (mappedOccurrence m))) | (o,m) <- paired]
        ++ [SourceMapping assignment (generatedSourceId statusSource) (statusSpanFor a)
          [assessmentId a] (assessmentSources a) | (o,m) <- paired,
          Just a <- [selectedFor o], Just assignment <- [mappedAssignment m]]
        ++ [SourceMapping generatedId (generatedSourceId lawSource) whole [r]
            (maybe [] nodeSources (find ((== r) . nodeId) (lawNodes law)))
          | r <- rules, generatedId <- [ruleIdFor r,branchIdFor r]]
        ++ [SourceMapping (guardId e) (generatedSourceId lawSource) whole
          [edgeId e,edgeFrom e,edgeTo e] [] | e <- guards]
      snapshot = makeSnapshot doc analysis
      kernelFailure d = Left [issue ("AKERNEL/" <> Core.diagCode d) "/documentAnalyses"
        (nub (key : concat [identityAuthoredIds i | i <- identities,
          identityKernelId i `elem` (Text.splitOn "/" (Core.diagPath d) ++ map snd (Core.diagParameters d))]))
        ("existing kernel rejected compiled input: " <> Text.pack (show d))]
      bytes = encodeJson request
  -- Exercise the same closed wire decoder and span/metadata checks as callers
  -- of the existing protocol, including its byte and nesting limits.
  decodedJson <- either (\reason -> Left [issue "AKERNEL/JSON" "/" [key] reason]) Right (decodeJson bytes)
  decoded <- either kernelFailure Right (decodeProofRequest decodedJson)
  validated <- either kernelFailure Right (validateProofRequest decoded)
  pure (CompiledAnalysis bytes snapshot mappings identities generated sourceMappings validated)
  where
    decimal = Text.pack . show

chunkSpans :: Text -> [(Text,a)] -> ((Text,a) -> Text) -> Map.Map Text TextSpan
chunkSpans content chunks key = Map.fromList (snd (foldl add (0,[]) chunks))
  where
    add (offset,rows) chunk@(text,_) =
      let next = offset + BS.length (Encoding.encodeUtf8 text)
      in (next,rows ++ [(key chunk,byteSpan content offset next)])

sourceValue :: GeneratedSource -> J
sourceValue s = JObj [("id",JStr (generatedSourceId s)),
  ("path",JStr ("generated/" <> generatedSourceKind s <> ".txt")),
  ("text",JStr (generatedSourceText s)),
  ("sha256",JStr (sha256Text (Encoding.encodeUtf8 (generatedSourceText s))))]
