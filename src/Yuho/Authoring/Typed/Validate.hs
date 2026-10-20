{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Typed.Validate
  ( validateTypedDocument, validateTypedBindings, typedOccurrences, typedAnalysisById ) where

import qualified Data.ByteString as BS
import Data.List (find, group, nub, sort)
import qualified Data.Map.Strict as Map
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Projection.Inspect (recoverSourceReference)
import Yuho.Authoring.Types
import Yuho.Authoring.Typed.Types
import Yuho.Authoring.Validate (issue)

typedAnalysisById :: TypedDocument -> Text -> Maybe TypedAnalysis
typedAnalysisById d key = find ((== key) . typedAnalysisId) (typedAnalyses d)

-- A defensive, bounded traversal. Readiness rejects cycles/overflow; no prefix
-- returned by this function can be compiled as a successfully truncated graph.
typedOccurrences :: TypedDocument -> TypedAnalysis -> [(TypedExpression,[Text])]
typedOccurrences d a = take 513 (concat [walk [] [typedLinkId e] (typedLinkTo e)
  | e <- typedLinks d, typedLinkFrom e == typedAnalysisRule a, typedLinkKind e == "typed_body"])
  where
    index = Map.fromList [(typedId (expressionMeta e),e) | e <- typedExpressions d]
    walk seen path key | key `elem` seen = []
                       | otherwise = case Map.lookup key index of
      Nothing -> []
      Just x -> (x,path) : concat [walk (key:seen) (path ++ [typedLinkId edge]) (typedLinkTo edge)
        | edge <- typedLinks d, typedLinkFrom edge == key, typedLinkKind edge == "typed_member"]

validateTypedDocument :: TypedDocument -> [AuthoringDiagnostic]
validateTypedDocument d = version ++ limits ++ identities ++ declarations ++ applications
  ++ expressions ++ links ++ cycles ++ supplied ++ analyses ++ originals ++ retained
  where
    objects = typedObjects d
    ids = [typedDocumentId d,typedLawId d] ++ map (typedId . snd) objects
      ++ map typedLinkId (typedLinks d) ++ map typedAnalysisId (typedAnalyses d)
      ++ map sourceId (typedOriginalSources d) ++ map assertionId (typedCaseAssertions d)
      ++ map annotationId (typedAnnotations d)
    bad code owner message = issue code "/typedDocument" [owner] message
    exists key = key `elem` ids
    blank = T.null . T.strip
    bounded x = not (blank x) && BS.length (UTF8.encodeUtf8 x) <= 128
    version = [issue "TVERSION" "/typedDocumentFormat" [] "use the explicit v0.3 typed profile; proof/linked constructs cannot be mixed"
      | typedDocumentFormat d /= typedAuthoringFormat]
    limits = [bad "TLIMIT" (typedDocumentId d) "typed document exceeds one MiB / 4096 authored objects"
      | BS.length (encodeRecord d) > 1048576 || length ids > 4096]
      ++ [bad "TLIMIT" (typedDocumentId d) "typed declaration limit exceeded"
        | length (typedEntityTypes d) > 32 || length (typedEntities d) > 256 || length (typedPredicates d) > 128
          || length (typedScalars d) > 256 || length (typedExpressions d) > 512 || length (typedRules d) > 128
          || length (typedPropositions d) > 256 || length (typedApplications d) > 1024]
    identities = [bad "TID" key "nonempty authored ID required, at most 128 UTF-8 bytes" | key <- ids, not (bounded key)]
      ++ [bad "TDUPLICATE" key "duplicate document-wide authored identity" | (key:_:_) <- group (sort ids)]
      ++ [bad "TMETADATA" (typedId m) "display label required" | (_,m) <- objects, blank (typedLabel m)]
      ++ [bad "TMETADATA" (typedLawId d) "revision and explicit limitations required"
        | blank (typedLawRevision d) || null (typedLimitations d) || any blank (typedLimitations d)]
    types = map (typedId . entityTypeMeta) (typedEntityTypes d)
    entityTypes = Map.fromList [(typedId (entityMeta e),entityNominalType e) | e <- typedEntities d]
    predicates = Map.fromList [(typedId (predicateMeta p),p) | p <- typedPredicates d]
    apps = Map.fromList [(typedId (applicationMeta a),a) | a <- typedApplications d]
    scalars = Map.fromList [(typedId (scalarMeta s),s) | s <- typedScalars d]
    exprs = Map.fromList [(typedId (expressionMeta e),e) | e <- typedExpressions d]
    rules = map (typedId . typedRuleMeta) (typedRules d)
    props = map (typedId . propositionMeta) (typedPropositions d)
    groundSafe key = not (T.any (`elem` (",()" :: String)) key)
    declarations = concat
      [[bad "TTYPE" (typedId (entityMeta e)) "entity has unknown nominal type" | entityNominalType e `notElem` types]
        ++ [bad "TGROUNDKEY" (typedId (entityMeta e)) "entity IDs cannot contain comma/parentheses used by the backend tuple key"
          | not (groundSafe (typedId (entityMeta e)))] | e <- typedEntities d]
      ++ [bad "TLIMIT" key "more than 64 concrete entities in one nominal type"
        | key <- types, length (filter (== key) (Map.elems entityTypes)) > 64]
      ++ concat [[bad "TARITY" key "predicate requires one to four explicitly ordered roles"
          | null roles || length roles > 4]
        ++ [bad "TTYPE" key "predicate role references unknown entity type" | any ((`notElem` types) . argumentType) roles]
        ++ [bad "TROLE" key "predicate role names must be nonempty and distinct"
          | any (not . bounded . argumentRole) roles || length (nub (map argumentRole roles)) /= length roles]
        ++ [bad "TGROUNDKEY" key "predicate IDs cannot contain comma/parentheses" | not (groundSafe key)]
        | p <- typedPredicates d, let key = typedId (predicateMeta p), let roles = predicateRoles p]
      ++ [bad "TSCALAR" (typedId (scalarMeta s)) "only integer scalar declarations are admitted by this profile"
        | s <- typedScalars d, scalarDeclaredType s /= "integer"]
    checkTuple owner tuple = case Map.lookup (tuplePredicate tuple) predicates of
      Nothing -> [bad "TPREDICATE" owner "ground tuple references unknown predicate"]
      Just p -> [bad "TARITY" owner "ground tuple arity differs from predicate declaration"
          | length (tupleArguments tuple) /= length (predicateRoles p)]
        ++ [issue "TTYPE" "/typedApplications/arguments" [owner,arg,argumentType role]
          "ground argument must be a declared concrete entity of the role's nominal type"
          | (arg,role) <- zip (tupleArguments tuple) (predicateRoles p), Map.lookup arg entityTypes /= Just (argumentType role)]
    applications = concat [checkTuple (typedId (applicationMeta a)) (applicationTuple a) | a <- typedApplications d]
      ++ [bad "TDUPGROUND" (typedId (applicationMeta a)) "distinct application IDs cannot alias the same backend ground tuple"
        | a <- typedApplications d, length (filter ((== applicationTuple a) . applicationTuple) (typedApplications d)) > 1]
    children key = [e | e <- typedLinks d, typedLinkFrom e == key, typedLinkKind e == "typed_member"]
    expressions = concat [case expressionForm e of
        GroundApplication app -> [bad "TAPPLICATION" key "expression references unknown ground application" | Map.notMember app apps]
          ++ [bad "TSHAPE" key "predicate expression cannot have structural children" | not (null (children key))]
        IntegerComparison op left right -> [bad "TOPERATOR" key "only integer gt and eq are admitted" | op `notElem` ["gt","eq"]]
          ++ [issue "TSCALAR" "/typedExpressions/operands" [key,operand] "operand must reference an integer scalar declaration"
              | operand <- [left,right], (scalarDeclaredType <$> Map.lookup operand scalars) /= Just "integer"]
          ++ [bad "TSHAPE" key "comparison cannot have structural children" | not (null (children key))]
        _ -> [bad "TSHAPE" key "all/any requires at least two typed_member edges" | length (children key) < 2]
      | e <- typedExpressions d, let key = typedId (expressionMeta e)]
    links = concat [let kind = typedLinkKind e
                        from = Map.lookup (typedLinkFrom e) exprs
                        correct = case kind of
                          "typed_body" -> typedLinkFrom e `elem` rules && Map.member (typedLinkTo e) exprs
                          "typed_member" -> maybe False (\x -> expressionForm x `elem` [TypedAll,TypedAny]) from && Map.member (typedLinkTo e) exprs
                          _ -> False
                    in [issue "TLINK" "/typedLinks" [typedLinkId e,typedLinkFrom e,typedLinkTo e]
                      "unsupported typed relationship or incompatible endpoints; proof member/use/defines are not typed edges" | not correct]
      | e <- typedLinks d]
      ++ [bad "TSHAPE" key "ground rule requires exactly one typed_body edge"
        | key <- rules, length [e | e <- typedLinks d, typedLinkFrom e == key, typedLinkKind e == "typed_body"] /= 1]
      ++ [bad "TPROPOSITION" (typedId (typedRuleMeta r)) "rule references unknown proposition" | r <- typedRules d, typedRuleConclusion r `notElem` props]
      ++ [issue "TSHARING" "/typedLinks" (key:map typedLinkId incoming) "shared expression structures are not admitted; author distinct ground expression occurrences"
        | key <- Map.keys exprs, let incoming = filter ((== key) . typedLinkTo) (typedLinks d), length incoming > 1]
    -- DFS uses both active and completed sets: unrelated acyclic material is not expanded.
    cycles = case visitAll [] [] (Map.keys exprs) of
      Left path -> [issue "TCYCLE" "/typedLinks" path "typed expression dependency cycle"]
      Right _ -> []
    visitAll _ done [] = Right done
    visitAll active done (key:rest)
      | key `elem` active = Left [key]
      | key `elem` done = visitAll active done rest
      | otherwise = do
          next <- visitAll (key:active) done (map typedLinkTo (children key))
          visitAll active (key:next) rest
    scope owner s = [bad "TSCOPE" owner "actor/context IDs required" | not (bounded (scopeActor s) && bounded (scopeContext s))]
    supplied = concat [[bad "TAPPLICATION" key "assessment target must be an authored ground application" | Map.notMember (assessedApplication a) apps]
        ++ checkTuple key (assessedTuple a)
        ++ [bad "TTUPLE" key "assessment tuple differs from the target application; revising a tuple does not silently reclassify it"
          | maybe False ((/= assessedTuple a) . applicationTuple) (Map.lookup (assessedApplication a) apps)]
        ++ scope key (typedAssessmentScope a)
        ++ [bad "TMETADATA" key "assessment reason/issuer required, origin and basis must be explicit"
          | blank (typedAssessmentReason a) || blank (typedIssuer a)
            || typedOrigin a `notElem` ["synthetic_fixture","external_assertion"]
            || typedBasis a `notElem` ["assumption","case_material"]
            || (typedBasis a == "case_material" && null (typedAssertionRefs a))]
        ++ [bad "TMETADATA" key "unresolved classification requires a reason" | TechnicalUnresolved reason <- [typedClassification a], blank reason]
        ++ [issue "TREFERENCE" "/typedAssessments" [key,ref] "case assertion not found" | ref <- typedAssertionRefs a, ref `notElem` map assertionId (typedCaseAssertions d)]
      | a <- typedAssessments d, let key = typedId (typedAssessmentMeta a)]
      ++ concat [scope key (valueScope v)
        ++ [bad "TSCALAR" key "value targets an unknown or unsupported scalar" | (scalarDeclaredType <$> Map.lookup (valueScalar v) scalars) /= Just "integer"]
        ++ [bad "TVALUE" key "unresolved scalar expected_type must be integer and reason nonempty"
          | UnknownInteger expected reason <- [valueExact v], expected /= "integer" || blank reason]
        ++ [bad "TMETADATA" key "supplied scalar reason and issuer required" | blank (valueReason v) || blank (valueIssuer v)]
      | v <- typedValues d, let key = typedId (valueMeta v)]
    assessments = map (typedId . typedAssessmentMeta) (typedAssessments d)
    values = map (typedId . valueMeta) (typedValues d)
    analyses = concat [scope key (typedAnalysisScope a)
      ++ [bad "TSCOPE" key "analysis actor must be a declared concrete entity" | Map.notMember (scopeActor (typedAnalysisScope a)) entityTypes]
      ++ [bad "TTARGET" key "selected rule/proposition must exist and match" | typedAnalysisRule a `notElem` rules
        || typedAnalysisProposition a `notElem` props || typedAnalysisProposition a /= maybe "" typedRuleConclusion (find ((== typedAnalysisRule a) . typedId . typedRuleMeta) (typedRules d))]
      ++ [issue "TREFERENCE" "/typedAnalyses" [key,ref] "selected assessment/value not found"
        | ref <- selectedTypedAssessments a, ref `notElem` assessments]
      ++ [issue "TREFERENCE" "/typedAnalyses" [key,ref] "selected scalar value not found" | ref <- selectedTypedValues a, ref `notElem` values]
      | a <- typedAnalyses d, let key = typedAnalysisId a]
    references owner refs = concat [case recoverSourceReference (typedOriginalSources d) ref of
      Left errors -> [e {diagnosticCode="TSOURCE",diagnosticLocation="/typedSources",diagnosticObjects=owner:diagnosticObjects e} | e <- errors]
      Right _ -> [] | ref <- refs]
    originals = concat [references (typedId m) (typedSources m) | (_,m) <- objects]
      ++ concat [references (assertionId a) (assertionSources a) ++ scope (assertionId a) (assertionScope a)
        ++ [bad "TMETADATA" (assertionId a) "case description required" | blank (assertionDescription a)] | a <- typedCaseAssertions d]
      ++ [bad "TSOURCE" (sourceId s) "unsupported original source kind" | s <- typedOriginalSources d, sourceKind s `notElem` ["law","case","other","synthetic"]]
    retained = [issue "TREFERENCE" "/typedAnnotations" [annotationId a,key] "annotation target not found"
        | a <- typedAnnotations d, key <- annotationAbout a, not (exists key)]
      ++ [bad "TMETADATA" (annotationId a) "annotation state must be draft/retained" | a <- typedAnnotations d, annotationState a `notElem` ["draft","retained"]]
      ++ [bad "TREFERENCE" (presentationObject p) "presentation target not found" | p <- typedPresentation d, not (exists (presentationObject p))]

validateTypedBindings :: TypedDocument -> Text -> TypedValidation
validateTypedBindings d key = case typedAnalysisById d key of
  Nothing -> TypedValidation (null errors) False (errors ++ [issue "TTARGET" "/typedAnalyses" [key] "analysis not found"]) []
  Just a ->
    let occurrences = typedOccurrences d a
        applications = nub [app | (e,_) <- occurrences, GroundApplication app <- [expressionForm e]]
        operands = nub (concat [[l,r] | (e,_) <- occurrences, IntegerComparison _ l r <- [expressionForm e]])
        selectedA = mapMaybe (\ref -> find ((== ref) . typedId . typedAssessmentMeta) (typedAssessments d)) (selectedTypedAssessments a)
        selectedV = mapMaybe (\ref -> find ((== ref) . typedId . valueMeta) (typedValues d)) (selectedTypedValues a)
        matchingA app = filter ((== app) . assessedApplication) selectedA
        matchingV scalar = filter ((== scalar) . valueScalar) selectedV
        failBinding code ids message = issue code "/typedAnalyses" (key:ids) message
        missing = [failBinding "TMISSING" [app] "ground application requires an explicitly selected classification" | app <- applications, null (matchingA app)]
          ++ [failBinding "TMISSING" [v] "scalar requires an explicitly selected value" | v <- operands, null (matchingV v)]
        ambiguous = [failBinding "TAMBIGUOUS" (app:map (typedId . typedAssessmentMeta) (matchingA app)) "multiple selected classifications for one ground application" | app <- applications, length (matchingA app) > 1]
          ++ [failBinding "TAMBIGUOUS" (v:map (typedId . valueMeta) (matchingV v)) "multiple selected values for one scalar" | v <- operands, length (matchingV v) > 1]
        binding = [failBinding "TSCOPE" [typedId (typedAssessmentMeta x)] "assessment scope differs from selected analysis" | x <- selectedA, typedAssessmentScope x /= typedAnalysisScope a]
          ++ [failBinding "TSCOPE" [typedId (valueMeta x)] "value scope differs from selected analysis" | x <- selectedV, valueScope x /= typedAnalysisScope a]
          ++ [failBinding "TTARGET" [typedId (typedAssessmentMeta x)] "selected assessment outside requested expression slice" | x <- selectedA, assessedApplication x `notElem` applications]
          ++ [failBinding "TTARGET" [typedId (valueMeta x)] "selected value outside requested expression slice" | x <- selectedV, valueScalar x `notElem` operands]
          ++ [failBinding "TAMBIGUOUS" [] "duplicate selection IDs" | length (nub (selectedTypedAssessments a)) /= length (selectedTypedAssessments a)
            || length (nub (selectedTypedValues a)) /= length (selectedTypedValues a)]
        limits = [failBinding "TDEPTH" path "expanded authored expression depth exceeds four (root depth zero)" | (_,path) <- take 1 (filter ((> 5) . length . snd) occurrences)]
          ++ [failBinding "TLIMIT" [] "selected expression closure exceeds 512 nodes; no truncation" | length occurrences >= 513]
        paths app = [path | (e,path) <- occurrences, expressionForm e == GroundApplication app]
        scalarPaths v = [path | (e,path) <- occurrences, IntegerComparison _ l r <- [expressionForm e], v `elem` [l,r]]
        inventory = concat [case matchingA app of
          [] -> [TypedOpenInput app "application" "missing" (paths app) Nothing]
          [x] | TechnicalUnresolved _ <- typedClassification x -> [TypedOpenInput app "application" "unresolved" (paths app) (Just (typedId (typedAssessmentMeta x)))]
          _ -> [] | app <- applications]
          ++ concat [case matchingV v of
            [] -> [TypedOpenInput v "scalar" "missing" (scalarPaths v) Nothing]
            [x] | UnknownInteger _ _ <- valueExact x -> [TypedOpenInput v "scalar" "unresolved" (scalarPaths v) (Just (typedId (valueMeta x)))]
            _ -> [] | v <- operands]
        diagnostics = errors ++ limits ++ missing ++ ambiguous ++ binding
    in TypedValidation (null errors) (null diagnostics) diagnostics inventory
  where errors = validateTypedDocument d
