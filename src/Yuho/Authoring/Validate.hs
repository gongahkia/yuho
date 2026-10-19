{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Validate
  ( validateDocument, validateBindings, Occurrence(..), selectedOccurrences
  , findAnalysis, toCoreSpan, issue ) where

import Data.List (find, group, sort)
import qualified Data.Map.Strict as Map
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import qualified Data.ByteString as BS
import qualified Data.Set as Set
import Yuho.Authoring.Codec (encodeDocument)
import Yuho.Authoring.Types
import qualified Yuho.Core.Types as Core
import Yuho.Core.Source (validateSpan)
import qualified Yuho.SuppliedProofStatus.Types as Proof

issue :: Text -> Text -> [Text] -> Text -> AuthoringDiagnostic
issue = AuthoringDiagnostic

toCoreSpan :: TextSpan -> Core.Span
toCoreSpan s = Core.Span (start s) (end s) (startLine s) (startColumn s)
  (endLine s) (endColumn s)

-- | A node occurrence and the authored edges from the selected rule to it.
data Occurrence = Occurrence
  { occurrenceNode :: LawNode, occurrencePath :: [Text], occurrenceRule :: Text }
  deriving (Eq, Show)

findAnalysis :: AuthoringDocument -> Text -> Maybe Analysis
findAnalysis doc key = find ((== key) . analysisId) (documentAnalyses doc)

-- Safe even for malformed drafts: cycles stop at the active path. Validation
-- must pass before these occurrences can be used for compilation.
selectedOccurrences :: AuthoringDocument -> Analysis -> [Occurrence]
selectedOccurrences doc analysis = take 1025 (walk Set.empty [] (analysisTarget analysis))
  where
    law = documentLaw doc
    nodes = Map.fromList [(nodeId n,n) | n <- lawNodes law]
    outgoing key = filter ((== key) . edgeFrom) (lawEdges law)
    walk seen path key
      | Set.member key seen = []
      | otherwise = case Map.lookup key nodes of
          Nothing -> []
          Just n ->
            let next = Set.insert key seen
                children kind = [e | e <- outgoing key, edgeKind e == kind]
                follow rule e = descend next (path ++ [edgeId e]) rule (edgeTo e)
            in if nodeKind n == "rule"
              then concatMap (follow key) (children "requires") ++
                concat [walk next (path ++ [edgeId e]) (edgeTo e)
                  | e <- children "exception"]
              else []
    descend seen path rule key
      | Set.member key seen = []
      | otherwise = case Map.lookup key nodes of
          Nothing -> []
          Just n -> Occurrence n path rule : concat
            [descend (Set.insert key seen) (path ++ [edgeId e]) rule (edgeTo e)
              | e <- outgoing key, edgeKind e == "member"]

validateDocument :: AuthoringDocument -> [AuthoringDiagnostic]
validateDocument doc = versionErrors ++ sizeErrors ++ identities ++ nodeErrors
  ++ edgeErrors ++ sharingErrors ++ cycleErrors ++ sourceErrors ++ assertionErrors
  ++ assessmentErrors ++ analysisErrors ++ retainedErrors
  where
    law = documentLaw doc
    nodes = lawNodes law
    edges = lawEdges law
    nodeMap = Map.fromList [(nodeId n,n) | n <- nodes]
    sources = Map.fromList [(sourceId s,s) | s <- documentSources doc]
    assertions = Map.fromList [(assertionId a,a) | a <- documentAssertions doc]
    assessments = Map.fromList [(assessmentId a,a) | a <- documentAssessments doc]
    named = [(documentId doc,"/documentId"),(lawId law,"/documentLaw/lawId")]
      ++ [(nodeId n,"/documentLaw/lawNodes") | n <- nodes]
      ++ [(edgeId e,"/documentLaw/lawEdges") | e <- edges]
      ++ [(sourceId s,"/documentSources") | s <- documentSources doc]
      ++ [(assertionId a,"/documentAssertions") | a <- documentAssertions doc]
      ++ [(assessmentId a,"/documentAssessments") | a <- documentAssessments doc]
      ++ [(analysisId a,"/documentAnalyses") | a <- documentAnalyses doc]
      ++ [(relationshipId r,"/documentRelationships") | r <- documentRelationships doc]
      ++ [(annotationId a,"/documentAnnotations") | a <- documentAnnotations doc]
    allIds = Set.fromList (map fst named)
    objectLocation owner = maybe "/" id (lookup owner named)
    duplicateIds = [key | (key:_:_) <- group (sort (map fst named))]
    versionErrors = [issue "AVERSION" "/documentFormat" [] "unsupported authoring format"
      | documentFormat doc /= authoringFormat]
    sizeErrors = [issue "ALIMIT" "/" [] "document exceeds one MiB or 4096 objects"
      | BS.length (encodeDocument doc) > 1048576 || length named > 4096]
    identities = [issue "AID" path [key] "ID must be nonempty and at most 128 UTF-8 bytes"
      | (key,path) <- named, not (bounded 128 key)] ++
      [issue "ADUPLICATE" "/" [key] "duplicate authored identity" | key <- duplicateIds]
    outgoing key kind = [e | e <- edges, edgeFrom e == key, edgeKind e == kind]
    nodeErrors = concatMap checkNode nodes ++
      [issue "AMETADATA" "/documentLaw/lawRevision" [lawId law] "law revision required"
      | Text.null (lawRevision law)]
    checkNode n =
      let key = nodeId n
          kind = nodeKind n
          bad message = issue "ASHAPE" "/documentLaw/lawNodes" [key] message
          requirements = outgoing key "requires"
          members = outgoing key "member"
          guards = outgoing key "exception"
      in [issue "AUNSUPPORTED" "/documentLaw/lawNodes" [key] "unsupported executable node kind"
         | kind `notElem` ["rule","input","all","any"]]
        ++ [bad "a rule needs exactly one requires edge and at most one exception"
           | kind == "rule", length requirements /= 1 || length guards > 1]
        ++ [bad "all/any needs at least two explicitly connected members"
           | kind `elem` ["all","any"], length members < 2]
        ++ refs key (nodeSources n)
    edgeErrors = concatMap checkEdge edges
    checkEdge e =
      let key = edgeId e
          kind = edgeKind e
          fromKind = nodeKind <$> Map.lookup (edgeFrom e) nodeMap
          toKind = nodeKind <$> Map.lookup (edgeTo e) nodeMap
          correct = case kind of
            "requires" -> fromKind == Just "rule" && toKind `elem` map Just ["input","all","any"]
            "member" -> fromKind `elem` map Just ["all","any"] && toKind `elem` map Just ["input","all","any"]
            "exception" -> fromKind == Just "rule" && toKind == Just "rule"
            _ -> False
      in [issue "AREFERENCE" "/documentLaw/lawEdges" [key,ref] "dangling law endpoint"
          | ref <- [edgeFrom e,edgeTo e], Map.notMember ref nodeMap]
        ++ [issue "AUNSUPPORTED" "/documentLaw/lawEdges" [key] "unsupported executable relationship kind"
          | kind `notElem` ["requires","member","exception"]]
        ++ [issue "ASHAPE" "/documentLaw/lawEdges" [key,edgeFrom e,edgeTo e]
          "relationship endpoints have incompatible executable kinds"
          | kind `elem` ["requires","member","exception"], not correct]
        ++ [issue "AUNSUPPORTED" "/documentLaw/lawEdges" [key,edgeTo e]
          "nested exception guards are outside this fragment"
          | kind == "exception", not (null (outgoing (edgeTo e) "exception"))]
    sharingErrors = [issue "ASHARING" "/documentLaw/lawEdges"
        (nodeId n : map edgeId incoming) "shared requirement structures are unsupported"
      | n <- nodes, nodeKind n /= "rule",
        let incoming = [e | e <- edges, edgeTo e == nodeId n,
              edgeKind e `elem` ["requires","member"]], length incoming > 1]
    -- Global DFS covers unrelated malformed executable material too.
    cycleErrors = case cyclePath Set.empty Set.empty (map nodeId nodes) of
      Just path -> [issue "ACYCLE" "/documentLaw/lawEdges" path "executable cycle"]
      Nothing -> []
    cyclePath _ _ [] = Nothing
    cyclePath active complete (key:rest)
      | Set.member key active = Just [key]
      | Set.member key complete = cyclePath active complete rest
      | otherwise = case visit active complete key of
          Left path -> Just path
          Right next -> cyclePath active next rest
    visit active complete key
      | Set.member key active = Left [key]
      | Set.member key complete = Right complete
      | otherwise = foldChildren (Set.insert key active) complete
          [e | e <- edges, edgeFrom e == key]
      where
        foldChildren _ done [] = Right (Set.insert key done)
        foldChildren stack done (e:rest) = case visit stack done (edgeTo e) of
          Left path -> Left (edgeId e:path)
          Right next -> foldChildren stack next rest
    sourceErrors = [issue "AMETADATA" "/documentSources" [sourceId s] "unsupported original source kind"
      | s <- documentSources doc, sourceKind s `notElem` ["law","case","other","synthetic"]]
    refs owner = concatMap (checkRef owner)
    checkRef owner ref = case Map.lookup (referenceSource ref) sources of
      Nothing -> [issue "ASOURCE" (objectLocation owner) [owner,referenceSource ref] "source reference not found"]
      Just s -> case referenceSpan ref of
        Nothing -> []
        Just anchor -> case sourceText s of
          Nothing -> [issue "ASPAN" (objectLocation owner) [owner,sourceId s] "anchor requires retained source text"]
          Just content -> [issue "ASPAN" (objectLocation owner) [owner,sourceId s] "invalid original UTF-8 span"
            | not (validateSpan (Core.Source "original" content (Encoding.encodeUtf8 content) "")
                (toCoreSpan anchor))]
    scopeErrors owner s = [issue "ASCOPE" (objectLocation owner) [owner] "actor and context IDs required"
      | not (bounded 128 (scopeActor s) && bounded 128 (scopeContext s))]
    assertionErrors = concat [refs (assertionId a) (assertionSources a)
      ++ scopeErrors (assertionId a) (assertionScope a)
      ++ [issue "AMETADATA" "/documentAssertions" [assertionId a] "assertion description required"
         | Text.null (assertionDescription a)] | a <- documentAssertions doc]
    assessmentErrors = concatMap checkAssessment (documentAssessments doc)
    checkAssessment a =
      let key = assessmentId a in refs key (assessmentSources a)
        ++ scopeErrors key (assessmentScope a)
        ++ [issue "ATARGET" "/documentAssessments" [key,assessmentInput a] "assessment must target a legal input"
           | (nodeKind <$> Map.lookup (assessmentInput a) nodeMap) /= Just "input"]
        ++ [issue "AMETADATA" "/documentAssessments" [key] "reason and issuer required; issuer limited to 256 UTF-8 bytes"
           | Text.null (assessmentReason a) || not (bounded 256 (assessmentIssuer a))]
        ++ [issue "AMETADATA" "/documentAssessments" [key] "origin must distinguish external assertion from synthetic fixture"
           | assessmentOrigin a `notElem` ["external_assertion","synthetic_fixture"]]
        ++ [issue "AMETADATA" "/documentAssessments" [key] "basis must be case_material or assumption; case_material needs assertions"
           | assessmentBasis a `notElem` ["case_material","assumption"]
             || (assessmentBasis a == "case_material" && null (assessmentAssertions a))]
        ++ [issue "AREFERENCE" "/documentAssessments" [key,ref] "case assertion reference not found"
           | ref <- assessmentAssertions a, Map.notMember ref assertions]
    analysisErrors = concatMap checkAnalysis (documentAnalyses doc)
    checkAnalysis a = scopeErrors (analysisId a) (analysisScope a)
      ++ [issue "ATARGET" "/documentAnalyses" [analysisId a,analysisTarget a] "selected target must be a rule"
         | (nodeKind <$> Map.lookup (analysisTarget a) nodeMap) /= Just "rule"]
      ++ [issue "AREFERENCE" "/documentAnalyses" [analysisId a,ref] "selected assessment not found"
         | ref <- analysisAssessments a, Map.notMember ref assessments]
    retainedErrors = concat
      [[issue "AREFERENCE" "/documentRelationships" [relationshipId r,ref] "relationship endpoint not found"
        | ref <- [relationshipFrom r,relationshipTo r], Set.notMember ref allIds]
       ++ [issue "AUNSUPPORTED" "/documentRelationships" [relationshipId r] "unsupported non-executable relationship kind"
          | relationshipKind r `notElem` ["chronology","support","challenge"]]
       | r <- documentRelationships doc]
      ++ concat [[issue "AREFERENCE" "/documentAnnotations" [annotationId a,ref] "annotation target not found"
        | ref <- annotationAbout a, Set.notMember ref allIds]
        ++ [issue "AMETADATA" "/documentAnnotations" [annotationId a] "annotation state must be draft or retained"
           | annotationState a `notElem` ["draft","retained"]] | a <- documentAnnotations doc]
      ++ [issue "AREFERENCE" "/documentPresentation" [presentationObject p] "presentation target not found"
         | p <- documentPresentation doc, Set.notMember (presentationObject p) allIds]

bounded :: Int -> Text -> Bool
bounded maximumBytes text = not (Text.null (Text.strip text))
  && BS.length (Encoding.encodeUtf8 text) <= maximumBytes

validateBindings :: AuthoringDocument -> Text -> ValidationReport
validateBindings doc key = case findAnalysis doc key of
  Nothing -> ValidationReport (null errors) False
    (errors ++ [issue "ATARGET" "/documentAnalyses" [key] "analysis not found"]) []
  Just analysis ->
    let occurrences = selectedOccurrences doc analysis
        leaves = filter ((== "input") . nodeKind . occurrenceNode) occurrences
        selected = mapMaybe (\ref -> find ((== ref) . assessmentId)
          (documentAssessments doc)) (analysisAssessments analysis)
        active o = filter ((== nodeId (occurrenceNode o)) . assessmentInput) selected
        inventory o = case active o of
          [] -> [open o "missing" Nothing]
          [a] | Proof.Unresolved _ <- classificationStatus (assessmentClassification a) ->
            [open o "unresolved" (Just (assessmentId a))]
          _ -> []
        open o state assessment = OpenInput (nodeId (occurrenceNode o))
          (occurrencePath o) (occurrenceRule o) (analysisScope analysis) state assessment
        missing = [issue "AMISSING" "/documentAnalyses" [key,nodeId (occurrenceNode o)]
          "required input has no selected assessment" | o <- leaves, null (active o)]
        ambiguous = [issue "AAMBIGUOUS" "/documentAnalyses"
          (key : nodeId (occurrenceNode o) : map assessmentId (active o))
          "more than one active assessment for input/context" | o <- leaves, length (active o) > 1]
        bindingErrors = concat
          [[issue "ASCOPE" "/documentAnalyses" [key,assessmentId a]
              "selected assessment actor/context differs from analysis"
            | assessmentScope a /= analysisScope analysis]
           ++ [issue "ATARGET" "/documentAnalyses" [key,assessmentId a,assessmentInput a]
              "selected assessment is outside the executable slice"
             | assessmentInput a `notElem` map (nodeId . occurrenceNode) leaves]
          | a <- selected]
        diagnostics = errors ++ missing ++ ambiguous ++ bindingErrors
    in ValidationReport (null errors) (null diagnostics) diagnostics (concatMap inventory leaves)
  where errors = validateDocument doc
