{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Check (checkModel) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Resolve (resolveTree)
import Yuho.Surface.Token

checkModel :: FilePath -> Model -> Maybe (FilePath, Scenario) -> Either Diagnostic Checked
checkModel path model supplied = do
  expect path "SFE004" (modelVariant model) "SuppliedProofStatus-v1"
  expect path "SFE004" (modelLimit model) "1024"
  if null (modelLimitations model) || any (Text.null . tokenText) (modelLimitations model)
    then at "SFE004" path (modelIdentifier model) "limitations required"
    else pure ()
  quoteIndex <- unique path "SFE002" (modelQuotes model)
  sourceIndex <- sourceDeclarations path (modelSources model)
  case modelBody model of
    Section rootId programId sourcePath root mapping declarations inline -> do
      expect path "SFE004" (modelIdentifier model) "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      expect path "SFE007" rootId "r:section84"
      expect path "SFE007" programId "p:section84"
      expect path "SFE007" sourcePath "section84"
      expect path "SFE014" mapping "src:pc84-extracted"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      expect path "SFE011" annotation "section107"
      expect path "SFE011" holder "defence"
      expect path "SFE011" burdenKind "legal"
      expect path "SFE011" standard "balance_of_probabilities"
      requireSources path sourceIndex
        [("src:pc84-excerpt", "excerpt", "research/section84/excerpt.txt")
        ,("src:synthetic-status", "synthetic_status", "research/section84/synthetic-status.txt")]
      if null (modelQuotes model) then at "SFE014" path rootId "source quotes required" else pure ()
      mapM_ (sectionProp path quoteIndex) declarations
      tree <- resolveTree path declarations root
      case supplied of
        Just _ -> at "SFE004" path rootId "section 84 uses inline supplied classifications"
        Nothing -> pure ()
      assignments <- checkAssignments path tree inline
      pure (Checked model Nothing assignments tree Nothing)
    Synthetic offence exception outputs -> do
      expect path "SFE004" (modelIdentifier model) "FictionalRestrictedAreaEntry-v0.1"
      expect path "SFE021" (modelJurisdiction model) "Fictional"
      expect path "SFE021" (modelPurpose model) "compiler_fixture"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      if tokenText annotation `elem` ["none", "synthetic_context"]
         && map tokenText [holder, burdenKind, standard] == ["none", "none", "not_applicable"]
      then pure () else at "SFE011" path annotation "invalid contextual burden"
      requireSources path sourceIndex
        [("src:fictional-rule", "source_text", "fictional/restricted-entry.txt")
        ,("src:fictional-status", "synthetic_status", "fictional/classifications.txt")]
      if length (modelQuotes model) < 5 then at "SFE014" path (modelIdentifier model) "five source quotes required" else pure ()
      expect path "SFE017" (ruleIdentifier offence) "o:entry"
      if ruleKind offence == OffenceKind && ruleKind exception == ExceptionKind then pure ()
        else at "SFE017" path (ruleIdentifier offence) "invalid rule kinds"
      expect path "SFE017" (ruleIdentifier exception) "x:emergency-rescue"
      expect path "SFE018" (maybe (ruleIdentifier exception) id (ruleTarget exception)) "o:entry"
      if tokenText (ruleIdentifier offence) == tokenText (ruleIdentifier exception)
        then at "SFE002" path (ruleIdentifier exception) "duplicate rule identity"
        else pure ()
      offenceTree <- checkedRule path quoteIndex offence
        (Set.fromList [Conduct, Circumstance, Fault])
      exceptionTree <- checkedRule path quoteIndex exception
        (Set.fromList [Circumstance, Purpose])
      let topIds = map tokenText [ruleIdentifier offence, ruleIdentifier exception,
            ruleId offence, ruleId exception, ruleProgram offence, ruleProgram exception]
          propIds = map (tokenText . identifier) (ruleGroups offence ++ ruleGroups exception)
          leafIds = map (tokenText . elementId) (ruleElements offence ++ ruleElements exception)
      if Set.size (Set.fromList (topIds ++ propIds ++ leafIds)) /= length (topIds ++ propIds ++ leafIds)
        then at "SFE002" path (ruleIdentifier exception) "duplicate semantic identifier"
        else pure ()
      let expected = [("offence_requirements", treeId offenceTree)
            ,("exception_applicable", treeId exceptionTree)
            ,("defeated_branch", tokenText (ruleProgram offence))
            ,("final_rule", tokenText (ruleId offence))]
      if map (\(TechnicalOutput a b) -> (tokenText a, tokenText b)) outputs /= expected
        then at "SFE020" path (modelIdentifier model) "typed technical outputs differ"
        else pure ()
      assignments <- case supplied of
        Nothing -> pure []
        Just (scenarioPath, Scenario scenarioId modelId entries acknowledgements) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          case acknowledgements of
            ScopeAcknowledgement item:_ -> at "SFE023" scenarioPath item "undeclared scope acknowledgement"
            [] -> pure ()
          checkAssignments scenarioPath
            (ResolvedGroup (ruleIdentifier offence) All [offenceTree, exceptionTree]) entries
      pure (Checked model (snd <$> supplied) assignments offenceTree (Just exceptionTree))
    Legal assumptions offence exception outputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      expect path "SFE011" annotation "section107"
      expect path "SFE011" holder "defence"
      expect path "SFE011" burdenKind "legal"
      expect path "SFE011" standard "balance_of_probabilities"
      requireRoles path sourceIndex
      if ruleKind offence == OffenceKind && ruleKind exception == ExceptionKind
        then pure () else at "SFE017" path (ruleIdentifier offence) "offence and exception declarations required"
      case ruleTarget exception of
        Just target | tokenText target == tokenText (ruleIdentifier offence) -> pure ()
        Just target -> at "SFE018" path target "exception must target the declared offence"
        Nothing -> at "SFE018" path (ruleIdentifier exception) "exception target required"
      declared <- checkScopeDeclarations path assumptions
      offenceTree <- checkedLegalRule path quoteIndex offence
      exceptionTree <- checkedLegalRule path quoteIndex exception
      shape <- checkLegalShape path offence exception offenceTree exceptionTree
      checkLegalOutputs path offence exception shape outputs
      let allIds = map tokenText
            ([ruleIdentifier offence, ruleIdentifier exception, ruleId offence, ruleId exception,
              ruleProgram offence, ruleProgram exception]
            ++ map elementId (ruleElements offence ++ ruleElements exception)
            ++ map identifier (ruleGroups offence ++ ruleGroups exception))
      if Set.size (Set.fromList allIds) == length allIds then pure ()
        else at "SFE002" path (ruleIdentifier exception) "duplicate semantic identifier"
      assignments <- case supplied of
        Nothing -> pure []
        Just (scenarioPath, Scenario scenarioId modelId entries acknowledgements) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          checkScopeAcknowledgements scenarioPath scenarioId declared acknowledgements
          checkAssignments scenarioPath
            (ResolvedGroup (ruleIdentifier offence) All [offenceTree, exceptionTree]) entries
      pure (Checked model (snd <$> supplied) assignments offenceTree (Just exceptionTree))

expect :: FilePath -> Text -> Token -> Text -> Either Diagnostic ()
expect path code token wanted
  | tokenText token == wanted = Right ()
  | otherwise = at code path token ("expected " <> wanted)

unique :: FilePath -> Text -> [(Token, a)] -> Either Diagnostic (Map.Map Text a)
unique path code = go Map.empty
  where
    go seen [] = Right seen
    go seen ((key,value):rest)
      | Map.member (tokenText key) seen = at code path key "duplicate identifier"
      | otherwise = go (Map.insert (tokenText key) value seen) rest

sourceDeclarations :: FilePath -> [SourceDecl] -> Either Diagnostic (Map.Map Text (Text, Text))
sourceDeclarations path rows = go Map.empty rows
  where
    go seen [] = Right seen
    go seen (SourceDecl key role location:rest)
      | Map.member (tokenText key) seen = at "SFE002" path key "duplicate source ID"
      | Text.null (tokenText location)
        || Text.isPrefixOf "/" (tokenText location)
        || ".." `elem` Text.splitOn "/" (tokenText location) =
          at "SFE015" path location "unsafe source reference"
      | otherwise = go (Map.insert (tokenText key) (tokenText role, tokenText location) seen) rest

requireSources :: FilePath -> Map.Map Text (Text, Text) -> [(Text, Text, Text)] -> Either Diagnostic ()
requireSources path actual expected =
  if actual == Map.fromList [(key,(role,location)) | (key,role,location) <- expected]
  then Right () else at "SFE014" path (Token WordToken "source" 1 1) "source declarations differ from supported slice"

sectionProp :: FilePath -> Map.Map Text Token -> Proposition -> Either Diagnostic ()
sectionProp path quotes (Leaf key proposition quote support) = do
  if "f:" `Text.isPrefixOf` tokenText key && maybe False ("P84-" `Text.isPrefixOf`) (tokenText <$> proposition)
    then pure () else at "SFE005" path key "invalid section proposition ID"
  mapM_ (knownQuote path quotes) (quote : maybe [] (:[]) support)
sectionProp _ _ (Group _ _ _) = Right ()

knownQuote :: FilePath -> Map.Map Text Token -> Token -> Either Diagnostic ()
knownQuote path quotes token =
  if Map.member (tokenText token) quotes then Right ()
  else at "SFE003" path token "unknown source quote"

treeId :: Resolved -> Text
treeId (ResolvedLeaf token _) = tokenText token
treeId (ResolvedGroup token _ _) = tokenText token

checkedRule :: FilePath -> Map.Map Text Token -> Rule -> Set.Set Category -> Either Diagnostic Resolved
checkedRule path quotes rule expected = do
  let categories = map elementCategory (ruleElements rule)
  if Set.fromList categories /= expected || length categories /= Set.size expected
    then at "SFE017" path (ruleIdentifier rule) "typed offence or exception elements differ"
    else pure ()
  mapM_ (\item -> do
    if "f:" `Text.isPrefixOf` tokenText (elementId item) then pure ()
      else at "SFE017" path (elementId item) "element requires fact ID"
    knownQuote path quotes (elementQuote item)
    mapM_ (knownQuote path quotes) (maybe [] (:[]) (elementSupport item))) (ruleElements rule)
  let declarations = [Leaf (elementId item) Nothing (elementQuote item) (elementSupport item)
        | item <- ruleElements rule] ++ ruleGroups rule
  case reverse (ruleGroups rule) of
    Group root _ _: _ -> resolveTree path declarations root
    _ -> at "SFE007" path (ruleIdentifier rule) "root proposition missing"

checkAssignments :: FilePath -> Resolved -> [Assignment] -> Either Diagnostic [(Token, Proof)]
checkAssignments path tree rows = do
  assigned <- go Map.empty rows
  let leaves = Set.fromList (map tokenText (leafTokens tree))
  if Map.keysSet assigned /= leaves
    then at "SFE009" path (treeToken tree) "missing or unexpected supplied assignment"
    else pure (Map.elems assigned)
  where
    go seen [] = Right seen
    go seen (Assignment key status reason:rest)
      | Map.member (tokenText key) seen = at "SFE002" path key "duplicate supplied assignment"
      | otherwise = do
          value <- proofStatus path status reason
          go (Map.insert (tokenText key) (key, value) seen) rest
    treeToken (ResolvedLeaf token _) = token
    treeToken (ResolvedGroup token _ _) = token

proofStatus :: FilePath -> Token -> Maybe Token -> Either Diagnostic Proof
proofStatus path status reason = case tokenText status of
  "proved" | reason == Nothing -> Right Proved
  "not_proved" | reason == Nothing -> Right NotProved
  "unresolved" -> case reason of
    Just token | tokenText token `elem` ["not_determined", "external_decision_pending"] ->
      Right (Unresolved (tokenText token))
    _ -> at "SFE010" path status "unresolved requires supported reason"
  _ -> at "SFE010" path status "invalid supplied proof classification"

requireRoles :: FilePath -> Map.Map Text (Text, Text) -> Either Diagnostic ()
requireRoles path sources =
  if Set.fromList (map fst (Map.elems sources)) == Set.fromList ["source_text", "synthetic_status"]
     && Map.size sources == 2
  then Right () else at "SFE014" path (Token WordToken "provenance" 1 1)
    "research model needs one text and one synthetic-status source"

checkScopeDeclarations :: FilePath -> [ScopeAssumption] -> Either Diagnostic (Set.Set Text)
checkScopeDeclarations path rows = do
  if null rows then at "SFE022" path (Token WordToken "scope-assumptions" 1 1)
    "research-scope assumptions required" else pure ()
  go Set.empty rows
  where
    go seen [] = Right seen
    go seen (ScopeAssumption item:rest)
      | not ("a:" `Text.isPrefixOf` tokenText item) =
          at "SFE022" path item "scope assumption requires a: identifier"
      | Set.member (tokenText item) seen = at "SFE002" path item "duplicate scope assumption"
      | otherwise = go (Set.insert (tokenText item) seen) rest

checkScopeAcknowledgements :: FilePath -> Token -> Set.Set Text
  -> [ScopeAcknowledgement] -> Either Diagnostic ()
checkScopeAcknowledgements path scenarioId declared = go Set.empty
  where
    go seen []
      | seen == declared = Right ()
      | otherwise = at "SFE022" path scenarioId "missing required research-scope acknowledgement"
    go seen (ScopeAcknowledgement item:rest)
      | Set.member (tokenText item) seen = at "SFE024" path item "duplicate scope acknowledgement"
      | not (Set.member (tokenText item) declared) = at "SFE023" path item "unknown scope assumption"
      | otherwise = go (Set.insert (tokenText item) seen) rest

checkedLegalRule :: FilePath -> Map.Map Text Token -> Rule -> Either Diagnostic Resolved
checkedLegalRule path quotes rule = do
  mapM_ (\item -> do
    if "f:" `Text.isPrefixOf` tokenText (elementId item) then pure ()
      else at "SFE017" path (elementId item) "typed element requires fact ID"
    knownQuote path quotes (elementQuote item)
    mapM_ (knownQuote path quotes) (maybe [] (:[]) (elementSupport item))) (ruleElements rule)
  let declarations = [Leaf (elementId item) Nothing (elementQuote item) (elementSupport item)
        | item <- ruleElements rule] ++ ruleGroups rule
  case reverse (ruleGroups rule) of
    Group root _ _: _ -> resolveTree path declarations root
    _ -> at "SFE007" path (ruleIdentifier rule) "rule root proposition missing"

data LegalShape = LegalShape
  { legalHurt :: Token, legalFault :: Token, legalOffenceRoot :: Token
  , legalNature :: Token, legalWrongfulness :: Token, legalControl :: Token
  , legalExceptionRoot :: Token }

checkLegalShape :: FilePath -> Rule -> Rule -> Resolved -> Resolved
  -> Either Diagnostic LegalShape
checkLegalShape path offence exception offenceTree exceptionTree = do
  let offenceKinds = Map.fromList [(tokenText (elementId item), elementCategory item)
        | item <- ruleElements offence]
      exceptionKinds = Map.fromList [(tokenText (elementId item), elementCategory item)
        | item <- ruleElements exception]
      category index token = Map.lookup (tokenText token) index
  (hurt, fault, offenceRoot) <- case offenceTree of
    ResolvedGroup root All
      [ResolvedLeaf act _, ResolvedLeaf result _, ResolvedLeaf causal _,
       ResolvedGroup faultId Any [ResolvedLeaf intention _, ResolvedLeaf knowledge _]] -> do
        if category offenceKinds causal == Just Causation then pure ()
          else at "SFE026" path causal "voluntary hurt requires a causation element"
        if map (category offenceKinds) [intention, knowledge] == [Just Intention, Just Knowledge]
          then pure () else at "SFE027" path faultId "fault alternative requires intention or knowledge"
        if map (category offenceKinds) [act, result] == [Just Conduct, Just Result]
           && Map.size offenceKinds == 5 && length (ruleElements offence) == 5
          then pure (result, faultId, root)
          else at "SFE017" path (ruleIdentifier offence) "offence requires conduct and hurt result"
    _ -> at "SFE027" path (ruleIdentifier offence)
      "offence requires conduct, result, causation and one typed fault alternative"
  (nature, wrongfulness, control, exceptionRoot) <- case exceptionTree of
    ResolvedGroup root All [ResolvedLeaf condition _,
      ResolvedGroup _ Any [natureRoute, wrongRoute, controlRoute]] -> do
        if category exceptionKinds condition == Just Unsoundness
          then pure () else at "SFE028" path condition "unsoundness at the act time required"
        if routeKinds exceptionKinds natureRoute == Just [Causation, NatureIncapacity]
           && routeKinds exceptionKinds wrongRoute ==
                Just [Causation, OrdinaryWrongfulness, ContraryLawWrongfulness]
           && routeKinds exceptionKinds controlRoute == Just [Causation, ControlIncapacity]
           && Map.size exceptionKinds == 8 && length (ruleElements exception) == 8
          then pure (resolvedToken natureRoute, resolvedToken wrongRoute,
            resolvedToken controlRoute, root)
          else at "SFE028" path (ruleIdentifier exception)
            "section 84 routes require causal links and both wrongfulness components"
    _ -> at "SFE028" path (ruleIdentifier exception)
      "section 84 requires unsoundness and three alternative incapacity routes"
  pure (LegalShape hurt fault offenceRoot nature wrongfulness control exceptionRoot)
  where
    routeKinds index (ResolvedGroup _ All members) =
      traverse (\item -> case item of
        ResolvedLeaf token _ -> Map.lookup (tokenText token) index
        _ -> Nothing) members
    routeKinds _ _ = Nothing
    resolvedToken (ResolvedLeaf token _) = token
    resolvedToken (ResolvedGroup token _ _) = token

checkLegalOutputs :: FilePath -> Rule -> Rule -> LegalShape
  -> [TechnicalOutput] -> Either Diagnostic ()
checkLegalOutputs path offence exception shape rows = do
  _ <- unique path "SFE002" [(label, target) | TechnicalOutput label target <- rows]
  let expected =
        [("hurt_status", legalHurt shape)
        ,("fault_alternative", legalFault shape)
        ,("voluntary_hurt_requirements", legalOffenceRoot shape)
        ,("section323_candidate_requirements", ruleId offence)
        ,("nature_route", legalNature shape)
        ,("wrongfulness_route", legalWrongfulness shape)
        ,("control_route", legalControl shape)
        ,("section84_requirements", legalExceptionRoot shape)
        ,("section84_defeat", ruleIdentifier exception)
        ,("final_rule", ruleId offence)]
  if map (\(TechnicalOutput label target) -> (tokenText label, tokenText target)) rows
       == [(label, tokenText target) | (label, target) <- expected]
    then Right () else at "SFE020" path (ruleIdentifier offence)
      "technical outputs must name the checked offence and exception nodes"
