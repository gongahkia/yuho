{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Check (checkModel) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Definitions
  ( definitionIndex, definitionLeaves, reachableDefinitions, resolveDefinition
  , resolveDefinitionRule )
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
        Just (scenarioPath, Scenario scenarioId modelId entries acknowledgements targets) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          noAnalysisTarget scenarioPath targets
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
        Just target -> atRelated "SFE018" path target
          "exception must target the declared offence" path (ruleIdentifier offence)
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
        Just (scenarioPath, Scenario scenarioId modelId entries acknowledgements targets) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          noAnalysisTarget scenarioPath targets
          checkScopeAcknowledgements scenarioPath path scenarioId declared acknowledgements
          checkAssignments scenarioPath
            (ResolvedGroup (ruleIdentifier offence) All [offenceTree, exceptionTree]) entries
      pure (Checked model (snd <$> supplied) assignments offenceTree (Just exceptionTree))
    MultiLegal assumptions offences exceptions attachments declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"section107"),(holder,"defence"),(burdenKind,"legal"),
         (standard,"balance_of_probabilities")]
      requireRoles path sourceIndex
      declared <- checkMultiScope path offences assumptions
      checkPrivateReferences path (offences ++ [item | GeneralException item <- exceptions])
      checkedOffences <- mapM (\offence -> do
        tree <- checkedLegalRule path quoteIndex offence
        checkOffenceShape path offence tree
        pure (offence, tree)) offences
      checkedExceptions <- mapM (\(GeneralException exception) -> do
        tree <- checkedLegalRule path quoteIndex exception
        checkSharedExceptionShape path exception tree
        pure (exception, tree)) exceptions
      checkMultiIdentities path checkedOffences checkedExceptions
      checkAttachments path checkedOffences checkedExceptions attachments
      checkMultiOutputs path checkedOffences checkedExceptions declaredOutputs
      case supplied of
        Nothing -> case (checkedOffences, checkedExceptions) of
          ((_,tree):_, (_,exceptionTree):_) ->
            pure (Checked model Nothing [] tree (Just exceptionTree))
          _ -> at "SFE030" path (modelIdentifier model) "offence and general exception required"
        Just (scenarioPath, scenario@(Scenario scenarioId modelId entries acknowledgements targets)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          target <- case targets of
            [] -> at "SFE036" scenarioPath scenarioId "one analysis target required"
            [item] -> pure item
            item:second:_ -> atRelated "SFE037" scenarioPath second
              "multiple analysis targets" scenarioPath item
          (selected, offenceTree) <- case [row | row@(offence,_) <- checkedOffences,
              tokenText (ruleIdentifier offence) == tokenText target] of
            [row] -> pure row
            _ -> at "SFE038" scenarioPath target "unknown candidate offence analysis target"
          (_, exceptionTree) <- attachedException scenarioPath target
            checkedExceptions attachments
          let expectedAssumptions = Map.filter
                (\(_,owner) -> maybe True (== tokenText target) owner) declared
          checkScopeAcknowledgements scenarioPath path scenarioId
            (Map.map fst expectedAssumptions) acknowledgements
          let unselected = Set.fromList [tokenText (elementId item)
                | (offence,_) <- checkedOffences,
                  tokenText (ruleIdentifier offence) /= tokenText target,
                  item <- ruleElements offence]
          case [item | Assignment item _ _ <- entries,
               Set.member (tokenText item) unselected] of
            item:_ -> at "SFE039" scenarioPath item "assignment belongs to an unselected offence"
            [] -> pure ()
          let required = Set.fromList (map tokenText
                (leafTokens offenceTree ++ leafTokens exceptionTree))
              provided = Set.fromList [tokenText item | Assignment item _ _ <- entries]
          if Set.null (required `Set.difference` provided) then pure ()
            else at "SFE042" scenarioPath target
              "missing selected-offence or attached-exception classification"
          assignments <- checkAssignments scenarioPath
            (ResolvedGroup (ruleIdentifier selected) All [offenceTree, exceptionTree]) entries
          pure (Checked model (Just scenario) assignments offenceTree (Just exceptionTree))
    DefinitionsLegal definitions assumptions offences exceptions attachments declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"section107"),(holder,"defence"),(burdenKind,"legal"),
         (standard,"balance_of_probabilities")]
      requireRoles path sourceIndex
      index <- definitionIndex path definitions
      mapM_ (checkDefinition path quoteIndex index) definitions
      declared <- checkMultiScope path offences assumptions
      checkPrivateReferences path (offences ++ [item | GeneralException item <- exceptions])
      checkedOffences <- mapM (\offence -> do
        mapM_ (checkElementQuote path quoteIndex) (ruleElements offence)
        checkSections path (ruleIdentifier offence) (ruleSections offence)
        tree <- resolveDefinitionRule path index offence
        checkDefinitionOffence path index offence tree
        pure (offence, tree)) offences
      checkedExceptions <- mapM (\(GeneralException exception) -> do
        tree <- checkedLegalRule path quoteIndex exception
        checkSharedExceptionShape path exception tree
        pure (exception, tree)) exceptions
      checkMultiIdentities path checkedOffences checkedExceptions
      checkAttachments path checkedOffences checkedExceptions attachments
      checkDefinitionIds path definitions offences exceptions
      checkDefinitionOutputs path index checkedOffences checkedExceptions declaredOutputs
      case supplied of
        Nothing -> case (checkedOffences, checkedExceptions) of
          ((_,tree):_, (_,exceptionTree):_) ->
            pure (Checked model Nothing [] tree (Just exceptionTree))
          _ -> at "SFE030" path (modelIdentifier model) "offence and exception required"
        Just (scenarioPath, scenario@(Scenario scenarioId modelId entries acknowledgements targets)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          target <- case targets of
            [] -> at "SFE036" scenarioPath scenarioId "one analysis target required"
            [item] -> pure item
            item:second:_ -> atRelated "SFE037" scenarioPath second
              "multiple analysis targets" scenarioPath item
          (selected, offenceTree) <- case [row | row@(offence,_) <- checkedOffences,
              tokenText (ruleIdentifier offence) == tokenText target] of
            [row] -> pure row
            _ -> at "SFE038" scenarioPath target "unknown candidate offence analysis target"
          (_, exceptionTree) <- attachedException scenarioPath target
            checkedExceptions attachments
          let expectedAssumptions = Map.filter
                (\(_,owner) -> maybe True (== tokenText target) owner) declared
          checkScopeAcknowledgements scenarioPath path scenarioId
            (Map.map fst expectedAssumptions) acknowledgements
          let derived = Set.fromList
                (map (tokenText . definitionId) definitions
                ++ [tokenText item | definition <- definitions,
                    DefinitionOutput item <- definitionOutputs definition])
              selectedDefinitions = reachableDefinitions index selected
              selectedLeaves = Set.fromList (map (tokenText . elementId)
                (concatMap definitionLeaves selectedDefinitions))
              allDefinitionLeaves = Set.fromList (map (tokenText . elementId)
                (concatMap definitionLeaves definitions))
              unreachable = allDefinitionLeaves `Set.difference` selectedLeaves
              otherOffence = Set.fromList [tokenText (elementId item)
                | offence <- offences, tokenText (ruleIdentifier offence) /= tokenText target,
                  item <- ruleElements offence]
          case [item | Assignment item _ _ <- entries,
               Set.member (tokenText item) derived] of
            item:_ -> at "SFE059" scenarioPath item "derived definition output cannot be assigned"
            [] -> pure ()
          case [item | Assignment item _ _ <- entries,
               Set.member (tokenText item) (unreachable `Set.union` otherOffence)] of
            item:_ -> at "SFE060" scenarioPath item
              "assignment belongs only to an unselected or unreachable definition"
            [] -> pure ()
          let required = Set.fromList (map tokenText
                (leafTokens offenceTree ++ leafTokens exceptionTree))
              provided = Set.fromList [tokenText item | Assignment item _ _ <- entries]
          if Set.null (required `Set.difference` provided) then pure ()
            else at "SFE061" scenarioPath target
              "missing reachable primitive classification"
          assignments <- checkAssignments scenarioPath
            (ResolvedGroup (ruleIdentifier selected) All [offenceTree,exceptionTree]) entries
          pure (Checked model (Just scenario) assignments offenceTree (Just exceptionTree))

checkElementQuote :: FilePath -> Map.Map Text Token -> Element -> Either Diagnostic ()
checkElementQuote path quotes item = do
  if "f:" `Text.isPrefixOf` tokenText (elementId item) then pure ()
    else at "SFE017" path (elementId item) "primitive input requires f: identifier"
  knownQuote path quotes (elementQuote item)
  mapM_ (knownQuote path quotes) (maybe [] (:[]) (elementSupport item))

checkDefinition :: FilePath -> Map.Map Text Token
  -> Map.Map Text StatutoryDefinition -> StatutoryDefinition -> Either Diagnostic ()
checkDefinition path quotes index definition = do
  checkSections path (definitionId definition) (definitionSections definition)
  mapM_ (checkElementQuote path quotes) (definitionLeaves definition)
  _ <- resolveDefinition path index (definitionId definition)
  pure ()

checkDefinitionOffence :: FilePath -> Map.Map Text StatutoryDefinition
  -> Rule -> Resolved -> Either Diagnostic ()
checkDefinitionOffence path index offence tree = do
  if ruleKind offence == OffenceKind then pure () else
    at "SFE017" path (ruleIdentifier offence) "candidate offence required"
  case (ruleDefinitionReferences offence, tree) of
    ([DefinitionReference item _ VoluntaryHurt],
      ResolvedGroup _ All [ResolvedGroup used All [_]])
      | tokenText item == tokenText used && null (ruleElements offence) -> pure ()
    ([DefinitionReference item _ Dishonesty],
      ResolvedGroup _ All members)
      | any (\node -> case node of
          ResolvedGroup used All [_] -> tokenText used == tokenText item
          _ -> False) members
        && Set.fromList (map elementCategory (ruleElements offence)) ==
          Set.fromList [MovableProperty,Possession,ConsentAbsence,Movement,MovementForTaking]
        && length (ruleElements offence) == 5 -> pure ()
    _ -> at "SFE062" path (ruleIdentifier offence)
      "candidate offence must explicitly use its typed statutory definition"
  let referenced = [item | DefinitionReference item _ _ <- ruleDefinitionReferences offence]
  if all (\item -> Map.member (tokenText item) index) referenced then pure ()
    else at "SFE053" path (ruleIdentifier offence) "unknown offence definition"

checkDefinitionIds :: FilePath -> [StatutoryDefinition] -> [Rule]
  -> [GeneralException] -> Either Diagnostic ()
checkDefinitionIds path definitions offences exceptions = do
  let definitionIds definition = definitionId definition
        : map (elementId) (definitionLeaves definition)
        ++ map identifier (definitionGroups definition)
      ruleIds rule = [ruleIdentifier rule,ruleId rule,ruleProgram rule]
        ++ map elementId (ruleElements rule) ++ map identifier (ruleGroups rule)
      allIds = concatMap definitionIds definitions
        ++ concatMap ruleIds offences
        ++ concatMap (ruleIds . (\(GeneralException rule) -> rule)) exceptions
  _ <- unique path "SFE002" [(item, ()) | item <- allIds]
  pure ()

checkDefinitionOutputs :: FilePath -> Map.Map Text StatutoryDefinition
  -> [(Rule, Resolved)] -> [(Rule, Resolved)] -> [TechnicalOutput]
  -> Either Diagnostic ()
checkDefinitionOutputs path index offences exceptions rows = do
  if null rows then at "SFE020" path (Token WordToken "outputs" 1 1)
    "technical outputs required" else pure ()
  _ <- unique path "SFE002" [(label, ()) | TechnicalOutput label _ <- rows]
  let valid = Set.fromList
        ([tokenText item | definition <- Map.elems index,
           DefinitionOutput item <- definitionOutputs definition]
        ++ [tokenText (ruleId rule) | (rule,_) <- offences]
        ++ [tokenText (ruleIdentifier rule) | (rule,_) <- exceptions]
        ++ [tokenText item | (rule,_) <- offences ++ exceptions,
            Group item _ _ <- ruleGroups rule])
  case [item | TechnicalOutput _ item <- rows,
        not (Set.member (tokenText item) valid)] of
    item:_ -> at "SFE020" path item "invalid technical-output reference"
    [] -> pure ()

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

checkScopeDeclarations :: FilePath -> [ScopeAssumption]
  -> Either Diagnostic (Map.Map Text Token)
checkScopeDeclarations path rows = do
  if null rows then at "SFE022" path (Token WordToken "scope-assumptions" 1 1)
    "research-scope assumptions required" else pure ()
  go Map.empty rows
  where
    go seen [] = Right seen
    go seen (ScopeAssumption item:rest)
      | not ("a:" `Text.isPrefixOf` tokenText item) =
          at "SFE022" path item "scope assumption requires a: identifier"
      | Map.member (tokenText item) seen = at "SFE002" path item "duplicate scope assumption"
      | otherwise = go (Map.insert (tokenText item) item seen) rest
    go _ (TargetScopeAssumption item _:_) =
      at "SFE030" path item "targeted scope requires a multi-offence model"

noAnalysisTarget :: FilePath -> [Token] -> Either Diagnostic ()
noAnalysisTarget _ [] = Right ()
noAnalysisTarget path (item:_) = at "SFE030" path item
  "analysis targets require a multi-offence model"

checkMultiScope :: FilePath -> [Rule] -> [ScopeAssumption]
  -> Either Diagnostic (Map.Map Text (Token, Maybe Text))
checkMultiScope path offences rows = do
  if null rows then at "SFE022" path (Token WordToken "scope-assumptions" 1 1)
    "research scope assumptions required" else pure ()
  go Map.empty rows
  where
    owners = Set.fromList (map (tokenText . ruleIdentifier) offences)
    go seen [] = Right seen
    go seen (row:rest) = do
      let (item, owner) = case row of
            ScopeAssumption token -> (token, Nothing)
            TargetScopeAssumption token target -> (token, Just target)
      if not ("a:" `Text.isPrefixOf` tokenText item) then
        at "SFE022" path item "scope assumption requires a: identifier" else pure ()
      case owner of
        Just target | not (Set.member (tokenText target) owners) ->
          at "SFE033" path target "scope assumption targets an unknown offence"
        _ -> pure ()
      if Map.member (tokenText item) seen then
        at "SFE002" path item "duplicate scope assumption" else
        go (Map.insert (tokenText item) (item, tokenText <$> owner) seen) rest

checkPrivateReferences :: FilePath -> [Rule] -> Either Diagnostic ()
checkPrivateReferences path rules = go rules
  where
    declared rule = map elementId (ruleElements rule) ++ map identifier (ruleGroups rule)
    go [] = Right ()
    go (rule:rest) = do
      let local = Set.fromList (map tokenText (declared rule))
          other = Map.fromList [(tokenText item, item) | candidate <- rules,
            tokenText (ruleIdentifier candidate) /= tokenText (ruleIdentifier rule),
            item <- declared candidate]
      case [(member, original) | Group _ _ members <- ruleGroups rule,
            member <- members, not (Set.member (tokenText member) local),
            Just original <- [Map.lookup (tokenText member) other]] of
        (member, original):_ -> atRelated "SFE045" path member
          "reference crosses a private offence or exception graph" path original
        [] -> go rest

checkOffenceShape :: FilePath -> Rule -> Resolved -> Either Diagnostic ()
checkOffenceShape path offence tree = do
  if ruleKind offence == OffenceKind then pure () else
    at "SFE017" path (ruleIdentifier offence) "candidate offence required"
  checkSections path (ruleIdentifier offence) (ruleSections offence)
  let categories = Map.fromList [(tokenText (elementId item), elementCategory item)
        | item <- ruleElements offence]
      kind item = Map.lookup (tokenText item) categories
  case tree of
    ResolvedGroup _ All [ResolvedLeaf act _, ResolvedLeaf result _,
      ResolvedLeaf causal _, ResolvedGroup _ Any [ResolvedLeaf intention _, ResolvedLeaf knowledge _]]
      | map kind [act,result,causal,intention,knowledge] ==
          map Just [Conduct,Result,Causation,Intention,Knowledge]
        && length (ruleElements offence) == 5 -> pure ()
    ResolvedGroup _ All [ResolvedLeaf movable _, ResolvedLeaf possession _,
      ResolvedLeaf consent _, ResolvedLeaf dishonest _, ResolvedLeaf moved _,
      ResolvedLeaf forTaking _]
      | map kind [movable,possession,consent,dishonest,moved,forTaking] ==
          map Just [MovableProperty,Possession,ConsentAbsence,DishonestIntention,
                    Movement,MovementForTaking]
        && length (ruleElements offence) == 6 -> pure ()
    _ -> at "SFE031" path (ruleIdentifier offence)
      "candidate offence must use the supported hurt or theft typed structure"

checkSharedExceptionShape :: FilePath -> Rule -> Resolved -> Either Diagnostic ()
checkSharedExceptionShape path exception tree = do
  if ruleKind exception == ExceptionKind && ruleTarget exception == Nothing
    then pure () else at "SFE032" path (ruleIdentifier exception)
      "general exception must be a reusable exception declaration"
  checkSections path (ruleIdentifier exception) (ruleSections exception)
  let categories = Map.fromList [(tokenText (elementId item), elementCategory item)
        | item <- ruleElements exception]
      route wanted (ResolvedGroup _ All members) =
        traverse (\item -> case item of
          ResolvedLeaf token _ -> Map.lookup (tokenText token) categories
          _ -> Nothing) members == Just wanted
      route _ _ = False
  case tree of
    ResolvedGroup _ All [ResolvedLeaf condition _,
      ResolvedGroup _ Any [nature,wrong,control]]
      | Map.lookup (tokenText condition) categories == Just Unsoundness
        && route [Causation,NatureIncapacity] nature
        && route [Causation,OrdinaryWrongfulness,ContraryLawWrongfulness] wrong
        && route [Causation,ControlIncapacity] control
        && length (ruleElements exception) == 8 -> pure ()
    _ -> at "SFE032" path (ruleIdentifier exception)
      "shared section 84 needs unsoundness and the three reviewed causal routes"

checkSections :: FilePath -> Token -> [StatutorySection] -> Either Diagnostic ()
checkSections path declaration sections = do
  if null sections then at "SFE031" path declaration
    "authored statutory section references required" else pure ()
  let tokens = [item | StatutorySection item <- sections]
  case [item | item <- tokens,
        Text.null (tokenText item) || not (Text.all (`elem` ['0'..'9']) (tokenText item))] of
    item:_ -> at "SFE031" path item "statutory section reference must be numeric"
    [] -> pure ()
  _ <- unique path "SFE002" [(item, ()) | item <- tokens]
  pure ()

checkMultiIdentities :: FilePath -> [(Rule, Resolved)] -> [(Rule, Resolved)]
  -> Either Diagnostic ()
checkMultiIdentities path offences exceptions = do
  let exceptionNames = map (ruleIdentifier . fst) exceptions
  if Set.size (Set.fromList (map tokenText exceptionNames)) == length exceptionNames
    then pure () else case exceptionNames of
      first:second:_ -> atRelated "SFE043" path second
        "duplicate general exception" path first
      _ -> at "SFE043" path (Token WordToken "general-exception" 1 1)
        "duplicate general exception"
  if length offences >= 2 && length exceptions == 1 then pure () else
    at "SFE030" path (Token WordToken "general-exception" 1 1)
      "bounded composition requires two candidate offences and one general exception"
  let rules = map fst (offences ++ exceptions)
      ids rule = [ruleIdentifier rule, ruleId rule, ruleProgram rule]
        ++ map elementId (ruleElements rule)
        ++ map identifier (ruleGroups rule)
  _ <- unique path "SFE002" [(item, ()) | rule <- rules, item <- ids rule]
  pure ()

checkAttachments :: FilePath -> [(Rule, Resolved)] -> [(Rule, Resolved)]
  -> [Attachment] -> Either Diagnostic ()
checkAttachments path offences exceptions = go Set.empty
  where
    offenceIds = Set.fromList (map (tokenText . ruleIdentifier . fst) offences)
    exceptionIds = Set.fromList (map (tokenText . ruleIdentifier . fst) exceptions)
    privateIds = Set.fromList [tokenText item | (rule,_) <- offences,
      item <- map elementId (ruleElements rule) ++ map identifier (ruleGroups rule)]
    go _ [] = Right ()
    go seen (Attachment _ exception target:rest)
      | not (Set.member (tokenText exception) exceptionIds) =
          at "SFE044" path exception "unknown general exception in attachment"
      | Set.member (tokenText target) privateIds =
          at "SFE034" path target "attachment target is a private offence proposition"
      | not (Set.member (tokenText target) offenceIds) =
          at "SFE033" path target "unknown candidate offence in attachment"
      | Set.member (tokenText exception, tokenText target) seen =
          at "SFE035" path target "duplicate general-exception attachment"
      | otherwise = go (Set.insert (tokenText exception, tokenText target) seen) rest

attachedException :: FilePath -> Token -> [(Rule, Resolved)] -> [Attachment]
  -> Either Diagnostic (Rule, Resolved)
attachedException path target exceptions attachments =
  case [(rule,tree) | Attachment _ exception owner <- attachments,
       tokenText owner == tokenText target, (rule,tree) <- exceptions,
       tokenText (ruleIdentifier rule) == tokenText exception] of
    [row] -> Right row
    [] -> at "SFE040" path target "selected offence has no attached general exception"
    _ -> at "SFE041" path target "bounded slice supports one attached exception per offence"

checkMultiOutputs :: FilePath -> [(Rule, Resolved)] -> [(Rule, Resolved)]
  -> [TechnicalOutput] -> Either Diagnostic ()
checkMultiOutputs path offences exceptions rows = do
  if null rows then at "SFE020" path (Token WordToken "outputs" 1 1)
    "technical outputs required" else pure ()
  _ <- unique path "SFE002" [(label, ()) | TechnicalOutput label _ <- rows]
  let rules = map fst (offences ++ exceptions)
      groups = Set.fromList [tokenText (identifier item) | rule <- rules,
        item <- ruleGroups rule]
      ruleIds = Set.fromList (map (tokenText . ruleId) (map fst offences))
      exceptionIds = Set.fromList (map (tokenText . ruleIdentifier . fst) exceptions)
      valid label target
        | "_requirements" `Text.isSuffixOf` label = Set.member target groups
        | "_final" `Text.isSuffixOf` label = Set.member target ruleIds
        | label == "section84_defeat" = Set.member target exceptionIds
        | otherwise = False
  case [item | TechnicalOutput label item <- rows,
       not (valid (tokenText label) (tokenText item))] of
    item:_ -> at "SFE020" path item "technical output has unknown or incompatible reference"
    [] -> pure ()

checkScopeAcknowledgements :: FilePath -> FilePath -> Token -> Map.Map Text Token
  -> [ScopeAcknowledgement] -> Either Diagnostic ()
checkScopeAcknowledgements path modelPath scenarioId declared = go Set.empty
  where
    go seen []
      | seen == Map.keysSet declared = Right ()
      | otherwise = case Map.toAscList (Map.withoutKeys declared seen) of
          (_, declaration):_ -> atRelated "SFE022" path scenarioId
            "missing required research-scope acknowledgement" modelPath declaration
          [] -> at "SFE022" path scenarioId "missing required research-scope acknowledgement"
    go seen (ScopeAcknowledgement item:rest)
      | Set.member (tokenText item) seen = at "SFE024" path item "duplicate scope acknowledgement"
      | not (Map.member (tokenText item) declared) = at "SFE023" path item "unknown scope assumption"
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
        ,("section323_candidate_requirements", legalOffenceRoot shape)
        ,("nature_route", legalNature shape)
        ,("wrongfulness_route", legalWrongfulness shape)
        ,("control_route", legalControl shape)
        ,("section84_requirements", legalExceptionRoot shape)
        ,("section84_defeat", ruleIdentifier exception)
        ,("final_rule", ruleId offence)]
  case [(target, correct) | (TechnicalOutput label target, (expectedLabel, correct)) <- zip rows expected,
      tokenText label /= expectedLabel || tokenText target /= tokenText correct] of
    (wrong, correct):_ -> atRelated "SFE020" path wrong
      "technical output must name the checked offence or exception node" path correct
    [] | length rows == length expected -> Right ()
       | otherwise -> at "SFE020" path (ruleIdentifier offence)
           "technical output list is incomplete"
