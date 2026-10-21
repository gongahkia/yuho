{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Presumption.Validate
  ( validatePresumptionDocument, validatePresumptionBindings, requiredPresumptionInputs
  , proofSliceDocument ) where

import qualified Data.ByteString as BS
import Data.List (find, group, nub, sort)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Presumption.Types
import Yuho.Authoring.Projection.Inspect (recoverSourceReference)
import Yuho.Authoring.Types
import Yuho.Authoring.Validate
import qualified Yuho.SuppliedProofStatus.Types as P

validatePresumptionDocument :: PresumptionDocument -> [AuthoringDiagnostic]
validatePresumptionDocument d = validateDocument base ++ version ++ identities ++ limits
  ++ concatMap registration regs ++ concatMap cycles (documentAnalyses base)
  where
    base = presumptionProofDocument d
    regs = presumptionRegistrations d
    allConditions = concatMap (\r -> conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r)) regs
    baseIds = documentId base : lawId law : map nodeId (lawNodes law) ++ map edgeId (lawEdges law)
      ++ map sourceId (documentSources base) ++ map assertionId (documentAssertions base)
      ++ map assessmentId (documentAssessments base) ++ map analysisId (documentAnalyses base)
      ++ map relationshipId (documentRelationships base) ++ map annotationId (documentAnnotations base)
    law = documentLaw base
    newIds = presumptionDocumentId d : map registeredId regs ++ map registeredConditionId allConditions
    named = newIds ++ baseIds
    version = [issue "PAVERSION" "/presumptionDocumentFormat" [] "expected explicit v0.4 presumption wrapper"
        | presumptionDocumentFormat d /= presumptionAuthoringFormat]
      ++ [issue "PAPROFILE" "/presumptionProofDocument/documentFormat" [documentId base]
        "presumption profile currently wraps v0.1 proof trees only; linked definitions and typed expressions are unsupported combinations"
        | documentFormat base /= authoringFormat]
    identities = [issue "PAID" "/presumptionRegistrations" [key] "ID must be nonempty and at most 128 UTF-8 bytes"
      | key <- newIds, T.null key || BS.length (UTF8.encodeUtf8 key) > 128]
      ++ [issue "PADUPLICATE" "/presumptionRegistrations" [key] "authored identities must be globally distinct"
        | (key:_:_) <- group (sort named)]
    limits = [issue "PALIMIT" "/" [presumptionDocumentId d]
      "presumption document exceeds one MiB or 4096 authored objects"
      | BS.length (encodeRecord d) > 1048576 || length named > 4096]
    primitive key = any (\n -> nodeId n == key && nodeKind n == "input") (lawNodes law)
    refs owner sources = concat [case recoverSourceReference (documentSources base) ref of
      Left errors -> [e {diagnosticLocation="/presumptionRegistrations",diagnosticObjects=owner:diagnosticObjects e} | e <- errors]
      Right _ -> [] | ref <- sources]
    registration r =
      [issue "PATARGET" "/presumptionRegistrations/registeredTarget" [registeredId r,registeredTarget r]
        "registration target must be an existing primitive legal input" | not (primitive (registeredTarget r))]
      ++ [issue "PAANALYSIS" "/presumptionRegistrations/registeredAnalyses" (registeredId r:registeredAnalyses r)
        "registration requires distinct, existing analysis IDs" | null (registeredAnalyses r)
          || length (nub (registeredAnalyses r)) /= length (registeredAnalyses r)
          || any (\key -> findAnalysis base key == Nothing) (registeredAnalyses r)]
      ++ [issue "PAMETADATA" "/presumptionRegistrations/registeredLabel" [registeredId r] "registration label required" | T.null (T.strip (registeredLabel r))]
      ++ refs (registeredId r) (registeredSources r)
      ++ checkCondition (registeredId r) 1 (registeredTrigger r)
      ++ checkCondition (registeredId r) 1 (registeredRebuttal r)
    checkCondition owner depth c =
      let key = registeredConditionId c
          kind = registeredConditionKind c
          children = registeredConditionMembers c
          shape = case kind of
            "leaf_effective" -> null children && maybe False primitive (registeredConditionLeaf c)
            "all_of" -> length children >= 2 && registeredConditionLeaf c == Nothing
            "any_of" -> length children >= 2 && registeredConditionLeaf c == Nothing
            _ -> False
      in [issue "PACONDITION" "/presumptionRegistrations/conditions" (owner:key:maybe [] (:[]) (registeredConditionLeaf c))
            "expected effective primitive leaf, or all_of/any_of with 2+ children and no leaf; burden effects are unsupported" | not shape]
        ++ [issue "PADEPTH" "/presumptionRegistrations/conditions" [owner,key] "backend condition depth exceeds 16" | depth > (16 :: Int)]
        ++ refs key (registeredConditionSources c)
        ++ concatMap (checkCondition owner (depth+1)) children
    cycles a = case walk Set.empty Set.empty targets of
      Left path -> [issue "PACYCLE" "/presumptionRegistrations" (analysisId a:path)
        "effective-leaf derivation cycle (registration and condition relationships identified)"]
      Right _ -> []
      where
        selected = registrationsFor d (analysisId a)
        targets = map registeredTarget selected
        dependencies leaf = [(registeredId r,registeredConditionId c,target) | r <- selected, registeredTarget r == leaf,
          c <- conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r), Just target <- [registeredConditionLeaf c]]
        walk _ done [] = Right done
        walk active done (leaf:rest)
          | Set.member leaf active = Left [leaf]
          | Set.member leaf done = walk active done rest
          | otherwise = do
              next <- children (Set.insert leaf active) done (dependencies leaf)
              walk active (Set.insert leaf next) rest
        children _ done [] = Right done
        children active done ((reg,cond,leaf):rest) = case walk active done [leaf] of
          Left path -> Left (reg:cond:path)
          Right next -> children active next rest

requiredPresumptionInputs :: PresumptionDocument -> Analysis -> [Text]
requiredPresumptionInputs d a = nub
  ([nodeId (occurrenceNode o) | o <- selectedOccurrences base a, nodeKind (occurrenceNode o) == "input"]
    ++ concat [[registeredTarget r] ++ conditionLeaves (registeredTrigger r) ++ conditionLeaves (registeredRebuttal r)
      | r <- registrationsFor d (analysisId a)])
  where base = presumptionProofDocument d

-- | Internal compilation view: original document is retained in the outer
-- snapshot. Only selections outside the ordinary proof slice are filtered here.
proofSliceDocument :: PresumptionDocument -> Text -> AuthoringDocument
proofSliceDocument d key = base {documentAnalyses=map restrict (documentAnalyses base)}
  where
    base = presumptionProofDocument d
    restrict a | analysisId a /= key = a
               | otherwise = a {analysisAssessments=[ref | ref <- analysisAssessments a,
                   Just x <- [find ((== ref) . assessmentId) (documentAssessments base)],
                   assessmentInput x `elem` [nodeId (occurrenceNode o) | o <- selectedOccurrences base a]]}

validatePresumptionBindings :: PresumptionDocument -> Text -> PresumptionValidation
validatePresumptionBindings d key = case findAnalysis base key of
  Nothing -> PresumptionValidation (null errors) False (errors ++ [issue "PAANALYSIS" "/documentAnalyses" [key] "analysis not found"]) []
  Just a ->
    let required = requiredPresumptionInputs d a
        selected = [x | ref <- analysisAssessments a, x <- documentAssessments base, assessmentId x == ref]
        active input = filter ((== input) . assessmentInput) selected
        missing = [issue "PAMISSING" "/documentAnalyses" [key,input] "required direct classification has no selected assessment (including trigger/rebuttal inputs)" | input <- required, null (active input)]
        ambiguous = [issue "PAAMBIGUOUS" "/documentAnalyses" (key:input:map assessmentId (active input)) "ambiguous active direct assessments" | input <- required, length (active input) > 1]
        bindings = concat [[issue "PASCOPE" "/documentAnalyses" [key,assessmentId x,assessmentInput x] "selected direct assessment scope differs from analysis" | assessmentScope x /= analysisScope a]
          ++ [issue "PATARGET" "/documentAnalyses" [key,assessmentId x] "selected assessment is outside proof and registration inputs" | assessmentInput x `notElem` required] | x <- selected]
        structural = filter (\e -> diagnosticCode e `notElem` ["AMISSING","ASCOPE"] && e `notElem` validateDocument base)
          (validationDiagnostics (validateBindings (proofSliceDocument d key) key))
        diagnostics = errors ++ structural ++ missing ++ ambiguous ++ bindings
        inventory = [OpenInput input [] (analysisTarget a) (analysisScope a) state assessment
          | input <- required, (state,assessment) <- case active input of
              [] -> [("missing",Nothing)]
              [x] | P.Unresolved _ <- classificationStatus (assessmentClassification x) -> [("unresolved",Just (assessmentId x))]
              _ -> []]
    in PresumptionValidation (null errors) (null diagnostics) diagnostics inventory
  where base=presumptionProofDocument d; errors=validatePresumptionDocument d
