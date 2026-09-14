{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Check (checkModel) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.ActorExceptions
  ( scopedToken, scopeTree, actContextToken, attachmentTargetToken, sharedExceptionTree )
import Yuho.Surface.Abetment (checkAbetment, abetmentRelations, abetmentAttributions)
import Yuho.Surface.Definitions
  ( definitionIndex, definitionLeaves, reachableDefinitions, resolveDefinition
  , resolveDefinitionRule )
import Yuho.Surface.Participation (resolveParticipationTree)
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
        Just (scenarioPath, _) -> at "SFE063" scenarioPath (modelIdentifier model)
          "actor bindings require a participation model"
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
        Just (scenarioPath, _) -> at "SFE063" scenarioPath (modelIdentifier model)
          "actor bindings require a participation model"
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
        Just (scenarioPath, _) -> at "SFE063" scenarioPath (modelIdentifier model)
          "actor bindings require a participation model"
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
        Just (scenarioPath, _) -> at "SFE063" scenarioPath (modelIdentifier model)
          "actor bindings require a participation model"
    ParticipationLegal roles definitions attributedFacts attributedMental assumptions offence
      participation citations declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"none"),(holder,"none"),(burdenKind,"none"),
         (standard,"not_applicable")]
      let IntentionalAidRoute route relation = participation
      checkParticipationSources path sourceIndex definitions offence route citations
      (principalRole, abettorRole) <- checkPartyRoles path roles
      index <- definitionIndex path definitions
      mapM_ (checkDefinition path quoteIndex index) definitions
      mapM_ (checkElementQuote path quoteIndex) (ruleElements offence)
      checkSections path (ruleIdentifier offence) (ruleSections offence)
      offenceTree <- resolveDefinitionRule path index offence
      checkDefinitionOffence path index offence offenceTree
      declared <- checkScopeDeclarations path assumptions
      checkParticipationShape path quoteIndex offence offenceTree route relation
      participationTree <- resolveParticipationTree path offenceTree participation
      checkParticipationAttributions path principalRole abettorRole definitions offence
        route relation attributedFacts attributedMental
      checkParticipationOutputs path offence route relation declaredOutputs
      case supplied of
        Nothing -> pure (Checked model Nothing [] participationTree Nothing)
        Just (scenarioPath, scenario@(ParticipationScenario scenarioId modelId bindings
          actorRows relationRows plain acknowledgements targets)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          target <- case targets of
            [item] -> pure item
            [] -> at "SFE036" scenarioPath scenarioId "participation analysis target required"
            _:second:_ -> at "SFE037" scenarioPath second "multiple analysis targets"
          expect scenarioPath "SFE069" target (tokenText (ruleIdentifier route))
          checkScopeAcknowledgements scenarioPath path scenarioId declared acknowledgements
          actorMap <- checkActorBindings scenarioPath principalRole abettorRole bindings
          case plain of
            Assignment item _ _:_ -> at "SFE065" scenarioPath item
              "actor-specific classification requires by actor or relation"
            [] -> pure ()
          relationAssignment <- case relationRows of
            [row] -> checkRelationAssignment scenarioPath actorMap relation row
            [] -> at "SFE068" scenarioPath (relationIdentifier relation)
              "relation status and endpoints required"
            _:second:_ -> at "SFE002" scenarioPath (relationAssignmentId second)
              "duplicate relation status"
          checkedActorRows <- mapM (checkActorAssignment scenarioPath actorMap
            attributedFacts attributedMental) actorRows
          let RelationAssignment _ _ _ relationStatus relationReason = relationAssignment
              relationFact = Assignment (relationStatusId relation)
                relationStatus relationReason
              entries = checkedActorRows ++ [relationFact]
          assignments <- checkAssignments scenarioPath participationTree entries
          pure (Checked model (Just scenario) assignments participationTree Nothing)
        Just (scenarioPath, Scenario scenarioId _ _ _ _) ->
          at "SFE064" scenarioPath scenarioId "participant role bindings required"
        Just (scenarioPath, AttemptScenario scenarioId _ _ _ _ _ _ _ _) ->
          at "SFE064" scenarioPath scenarioId "participation scenario required"
        Just (scenarioPath, ActorScopedScenario scenarioId _ _ _ _ _ _ _ _ _ _ _) ->
          at "SFE064" scenarioPath scenarioId "participation scenario required"
    AttemptLegal roles definitions assumptions offence attempt citations declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"none"),(holder,"none"),(burdenKind,"none"),
         (standard,"not_applicable")]
      requireRoles path sourceIndex
      role <- case roles of
        [PartyRole item AllegedAttempterParty] -> pure item
        PartyRole item _: _ -> at "SFE083" path item
          "exactly one alleged-attempter role required"
        [] -> at "SFE083" path (modelIdentifier model) "alleged-attempter role required"
      index <- definitionIndex path definitions
      mapM_ (checkDefinition path quoteIndex index) definitions
      mapM_ (checkElementQuote path quoteIndex) (ruleElements offence)
      targetTree <- resolveDefinitionRule path index offence
      checkDefinitionOffence path index offence targetTree
      let AttemptDefinition attemptRuleId (AttemptActor declaredActor)
            (AttemptTarget declaredTarget) intention stage = attempt
          TargetDirectedMentalState mentalId (AttemptActor mentalActor)
            (AttemptTarget mentalTarget) mentalQuote = intention
          ConductStageDefinition stageId (AttemptActor stageActor) stageOutput stageQuote = stage
          sections rule = [tokenText item | StatutorySection item <- ruleSections rule]
          definitionSectionsText definition =
            [tokenText item | StatutorySection item <- definitionSections definition]
      checkDefinitionIds path definitions [offence,attemptRuleId] []
      checkSections path (ruleIdentifier attemptRuleId) (ruleSections attemptRuleId)
      if tokenText (ruleIdentifier offence) == "o:theft"
          && sections offence == ["378","379"]
          && map definitionSectionsText definitions == [["23"],["23"],["24"]]
        then pure () else at "SFE075" path (ruleIdentifier offence)
          "bounded target must be the authored theft candidate and definitions"
      checkAttemptAuthorities path sourceIndex citations
      if tokenText declaredActor == tokenText role
          && tokenText mentalActor == tokenText role
          && tokenText stageActor == tokenText role
        then pure () else at "SFE081" path declaredActor
          "attempt intention and stage must belong to alleged-attempter role"
      if tokenText declaredTarget == tokenText (ruleIdentifier offence)
          && tokenText mentalTarget == tokenText declaredTarget
          && fmap tokenText (ruleTarget attemptRuleId) == Just (tokenText declaredTarget)
        then pure () else atRelated "SFE075" path declaredTarget
          "attempt and intention must target the candidate offence" path (ruleIdentifier offence)
      if ruleKind attemptRuleId == AttemptKind
          && "attempt:" `Text.isPrefixOf` tokenText (ruleIdentifier attemptRuleId)
          && "r:" `Text.isPrefixOf` tokenText (ruleId attemptRuleId)
          && sections attemptRuleId == ["511"]
          && null (ruleDefinitionReferences attemptRuleId)
          && map elementCategory (ruleElements attemptRuleId) == [Intention,SubstantialStep]
          && map (tokenText . elementId) (ruleElements attemptRuleId) ==
            map tokenText [mentalId,stageOutput]
          && "stage:" `Text.isPrefixOf` tokenText stageId
          && "f:" `Text.isPrefixOf` tokenText mentalId
          && "f:" `Text.isPrefixOf` tokenText stageOutput
        then pure () else at "SFE072" path (ruleIdentifier attemptRuleId)
          "invalid typed direct-attempt declaration"
      knownQuote path quoteIndex mentalQuote
      knownQuote path quoteIndex stageQuote
      root <- case ruleGroups attemptRuleId of
        [Group item All [mentalRef,stageRef]]
          | "g:" `Text.isPrefixOf` tokenText item
            && map tokenText [mentalRef,stageRef] == map tokenText [mentalId,stageOutput] ->
              pure item
        _ -> at "SFE085" path (ruleIdentifier attemptRuleId)
          "attempt requirements must use intention and substantial-step status only"
      let declarations = [Leaf (elementId item) Nothing (elementQuote item) Nothing
            | item <- ruleElements attemptRuleId] ++ ruleGroups attemptRuleId
      attemptTree <- resolveTree path declarations root
      let scoped = [item | AttemptScopeAssumption item <- assumptions]
      declared <- checkScopeDeclarations path scoped
      let requiredScopes = Set.fromList
            ["a:direct-self-attempt-only", "a:target-not-completed",
             "a:no-express-attempt-punishment-provision-modelled",
             "a:punishment-outside-scope", "a:statutory-expression-supplied",
             "a:stage-externally-classified", "a:impossible-attempts-excluded"]
      if Map.keysSet declared == requiredScopes then pure () else
        at "SFE084" path (ruleIdentifier attemptRuleId)
          "bounded attempt research-scope declarations required"
      let outputs = [item | AttemptTechnicalOutput item <- declaredOutputs]
      if [(tokenText label,tokenText target) | TechnicalOutput label target <- outputs] ==
          [("intended_target",tokenText mentalId),
           ("conduct_stage",tokenText stageId),
           ("act_towards_commission",tokenText stageOutput),
           ("section511_requirements",tokenText root),
           ("final_rule",tokenText (ruleId attemptRuleId))]
        then pure () else at "SFE020" path (ruleIdentifier attemptRuleId)
          "invalid typed attempt output reference"
      case supplied of
        Nothing -> pure (Checked model Nothing [] attemptTree Nothing)
        Just (scenarioPath, scenario@(AttemptScenario scenarioId modelId bindings
          actorRows stageRows completions plain acknowledgements targets)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          case targets of
            [item] -> expect scenarioPath "SFE075" item (tokenText (ruleIdentifier attemptRuleId))
            [] -> at "SFE036" scenarioPath scenarioId "attempt analysis target required"
            _:item:_ -> at "SFE037" scenarioPath item "multiple analysis targets"
          checkScopeAcknowledgements scenarioPath path scenarioId declared acknowledgements
          actor <- checkAttemptBinding scenarioPath scenarioId role bindings
          case plain of
            Assignment item _ _:_ -> at "SFE082" scenarioPath item
              "attempt inputs require actor attribution or typed stage"
            [] -> pure ()
          mental <- case actorRows of
            [row@(ActorAssignment item owner _ _)]
              | tokenText item == tokenText mentalId && tokenText owner == tokenText actor ->
                  pure row
              | otherwise -> at "SFE081" scenarioPath item
                  "target-directed intention must belong to alleged attempter"
            [] -> at "SFE081" scenarioPath scenarioId "target-directed intention required"
            _:item:_ -> at "SFE081" scenarioPath (actorAssignmentId item)
              "one target-directed intention classification required"
          suppliedStage <- case stageRows of
            [row@(ConductStageAssignment item owner _)]
              | tokenText item == tokenText stageId && tokenText owner == tokenText actor ->
                  pure row
              | otherwise -> at "SFE082" scenarioPath item
                  "conduct stage must belong to alleged attempter and declared stage"
            [] -> at "SFE076" scenarioPath scenarioId "conduct stage required"
            first:second:_ -> atRelated "SFE077" scenarioPath (stageAssignmentId second)
              "duplicate or contradictory conduct stages" scenarioPath (stageAssignmentId first)
          case completions of
            [TargetNotCompleted target _]
              | tokenText target == tokenText declaredTarget -> pure ()
              | otherwise -> at "SFE075" scenarioPath target
                  "target completion reference cannot replace declared offence"
            [TargetCompleted _ status] -> at "SFE080" scenarioPath status
              "completed target offence is outside bounded attempt analysis"
            [] -> at "SFE080" scenarioPath scenarioId "target completion status required"
            _:second:_ -> at "SFE080" scenarioPath (completionToken second)
              "multiple target completion statuses"
          let ActorAssignment _ _ mentalStatus mentalReason = mental
              ConductStageAssignment _ _ stageStatus = suppliedStage
              (stageProof,stageReason) = case stageStatus of
                PreparationOnly item -> (item { tokenText = "not_proved" },Nothing)
                ActTowardsCommission item -> (item { tokenText = "proved" },Nothing)
                StageUnresolved item reason -> (item { tokenText = "unresolved" },Just reason)
          assignments <- checkAssignments scenarioPath attemptTree
            [Assignment mentalId mentalStatus mentalReason,
             Assignment stageOutput stageProof stageReason]
          pure (Checked model (Just scenario) assignments attemptTree Nothing)
        Just (scenarioPath, ParticipationScenario scenarioId _ _ _ _ _ _ _) ->
          at "SFE076" scenarioPath scenarioId "typed attempt stage required"
        Just (scenarioPath, Scenario scenarioId _ _ _ _) ->
          at "SFE083" scenarioPath scenarioId "alleged-attempter binding required"
        Just (scenarioPath, ActorScopedScenario scenarioId _ _ _ _ _ _ _ _ _ _ _) ->
          at "SFE083" scenarioPath scenarioId "typed attempt scenario required"
    ActorScopedLegal _ _ _ _ _ _ _ _ _ _ _ ->
      checkActorScoped path model supplied quoteIndex sourceIndex
    AbetmentLegal _ _ _ _ _ _ _ _ _ _ _ ->
      checkAbetmentScoped path model supplied quoteIndex sourceIndex

checkActorScoped :: FilePath -> Model -> Maybe (FilePath, Scenario)
  -> Map.Map Text Token -> Map.Map Text (Text, Text) -> Either Diagnostic Checked
checkActorScoped path model supplied quotes sources = case modelBody model of
  ActorScopedLegal roles attributedFacts attributedMental assumptions offence
    participation@(IntentionalAidRoute route relation) attempt
    shared@(ActorExceptionDefinition (ActorSubject subject) exception)
    attachments citations declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"section107"),(holder,"defence"),(burdenKind,"legal"),
         (standard,"balance_of_probabilities")]
      if Set.fromList (map fst (Map.elems sources)) ==
          Set.fromList ["source_text", "synthetic_status", "contextual"]
          && Map.size sources == 3 then pure () else
        at "SFE014" path (modelIdentifier model)
          "actor-scoped model requires source, synthetic status and contextual authority"
      _ <- unique path "SFE063" [(item,()) | PartyRole item _ <- roles]
      let roleKind wanted = [item | PartyRole item kind <- roles, kind == wanted]
      (principal,abettor,attempter) <- case
        (roleKind PrincipalParty,roleKind AllegedAbettorParty,
         roleKind AllegedAttempterParty) of
        ([a],[b],[c]) | length roles == 3 -> pure (a,b,c)
        _ -> at "SFE088" path (modelIdentifier model)
          "principal, alleged-abettor and alleged-attempter roles required"
      declared <- checkScopeDeclarations path assumptions
      let requiredScopes = Set.fromList
            ["a:post-2022-section-84-expression-applicable",
             "a:dishonesty-externally-classified",
             "a:only-intentional-aid-route",
             "a:principal-theft-requirements-separately-supplied",
             "a:broader-section108-cases-excluded",
             "a:no-express-punishment-provision-modelled",
             "a:direct-self-attempt-only",
             "a:target-not-completed",
             "a:no-express-attempt-punishment-provision-modelled",
             "a:punishment-outside-scope",
             "a:statutory-expression-supplied",
             "a:stage-externally-classified",
             "a:impossible-attempts-excluded"]
      if Map.keysSet declared == requiredScopes then pure () else
        at "SFE088" path (modelIdentifier model) "bounded actor-specific scope required"
      offenceTree <- checkedLegalRule path quotes offence
      checkOffenceShape path offence offenceTree
      checkParticipationShape path quotes offence offenceTree route relation
      participationTree <- resolveParticipationTree path offenceTree participation
      checkParticipationAttributions path principal abettor [] offence route relation
        attributedFacts attributedMental
      let AttemptDefinition attemptRuleId (AttemptActor declaredAttemptActor)
            (AttemptTarget declaredAttemptTarget) intention stage = attempt
          TargetDirectedMentalState mentalId (AttemptActor mentalActor)
            (AttemptTarget mentalTarget) mentalQuote = intention
          ConductStageDefinition stageId (AttemptActor stageActor) stageOutput stageQuote = stage
          sectionNumbers rule = [tokenText item | StatutorySection item <- ruleSections rule]
      checkSections path (ruleIdentifier attemptRuleId) (ruleSections attemptRuleId)
      if ruleKind offence == OffenceKind && tokenText (ruleIdentifier offence) == "o:theft"
          && sectionNumbers offence == ["378","379"]
          && ruleKind attemptRuleId == AttemptKind
          && sectionNumbers attemptRuleId == ["511"]
          && map elementCategory (ruleElements attemptRuleId) == [Intention,SubstantialStep]
          && map (tokenText . elementId) (ruleElements attemptRuleId) ==
            map tokenText [mentalId,stageOutput]
          && all ((== tokenText attempter) . tokenText)
            [declaredAttemptActor,mentalActor,stageActor]
          && all ((== tokenText (ruleIdentifier offence)) . tokenText)
            [declaredAttemptTarget,mentalTarget]
          && fmap tokenText (ruleTarget attemptRuleId) ==
            Just (tokenText (ruleIdentifier offence))
          && "stage:" `Text.isPrefixOf` tokenText stageId
        then pure () else at "SFE087" path (ruleIdentifier attemptRuleId)
          "attempt must target the declared theft candidate for the alleged attempter"
      knownQuote path quotes mentalQuote
      knownQuote path quotes stageQuote
      attemptRoot <- case ruleGroups attemptRuleId of
        [Group item All [mentalRef,stageRef]]
          | map tokenText [mentalRef,stageRef] == map tokenText [mentalId,stageOutput] ->
              pure item
        _ -> at "SFE087" path (ruleIdentifier attemptRuleId)
          "bounded attempt needs distinct intention and supplied stage"
      let attemptDeclarations = [Leaf (elementId item) Nothing (elementQuote item) Nothing
            | item <- ruleElements attemptRuleId] ++ ruleGroups attemptRuleId
      attemptTree <- resolveTree path attemptDeclarations attemptRoot
      if tokenText subject == "subject:actor" then pure () else
        at "SFE088" path subject "general exception requires actor subject parameter"
      case [member | Group _ _ members <- ruleGroups exception, member <- members,
          "xi:" `Text.isPrefixOf` tokenText member ||
          "f:xi-" `Text.isPrefixOf` tokenText member ||
          "g:xi-" `Text.isPrefixOf` tokenText member] of
        item:_ -> at "SFE095" path item "cross-instance exception reference is forbidden"
        [] -> pure ()
      exceptionTree <- sharedExceptionTree path shared
      mapM_ (checkElementQuote path quotes) (ruleElements exception)
      checkSharedExceptionShape path exception exceptionTree
      checkDefinitionIds path [] [offence,route,attemptRuleId,exception] []
      validateScopedAttachments path (principal,abettor,attempter)
        offence route attemptRuleId exception attachments
      checkActorScopedAuthorities path sources citations
      checkActorScopedOutputs path offence route attemptRuleId attachments declaredOutputs
      case supplied of
        Nothing -> case attachments of
          first:_ -> pure (Checked model Nothing [] offenceTree
            (Just (scopeTree (attachmentInstanceId first) exceptionTree)))
          [] -> at "SFE089" path (ruleIdentifier exception) "attachment required"
        Just (scenarioPath, scenario@(ActorScopedScenario scenarioId modelId targets
          observations bindings actorRows relationRows stageRows completions scopedRows
          plain acknowledgements)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          target <- case targets of
            [item] -> pure item
            [] -> at "SFE036" scenarioPath scenarioId "one analysis target required"
            _:second:_ -> at "SFE037" scenarioPath second "multiple analysis targets"
          selected <- case [item | item <- attachments,
            tokenText (attachmentTargetToken (attachmentTargetKind item)) == tokenText target] of
            [item] -> pure item
            _ -> at "SFE087" scenarioPath target "unknown actor-scoped analysis target"
          checkScopeAcknowledgements scenarioPath path scenarioId declared acknowledgements
          actors <- checkScopedActorBindings scenarioPath scenarioId roles bindings
          let chosen = tokenText target
              selectedBranch
                | chosen == tokenText (ruleIdentifier offence) = offenceTree
                | chosen == tokenText (ruleIdentifier route) = participationTree
                | otherwise = attemptTree
              exceptionFacts = Set.fromList (map (tokenText . elementId)
                (ruleElements exception))
          case [item | Assignment item _ _ <- plain, Set.member (tokenText item) exceptionFacts]
            ++ [item | ActorAssignment item _ _ _ <- actorRows,
              Set.member (tokenText item) exceptionFacts] of
            item:_ -> at "SFE090" scenarioPath item
              "section 84 input requires an explicit exception instance"
            [] -> pure ()
          case plain of
            Assignment item _ _:_ -> at "SFE090" scenarioPath item
              "actor-specific classifications require typed attribution"
            [] -> pure ()
          active <- checkedObservations scenarioPath selected observations attachments
          targetEntries <- if chosen == tokenText (ruleIdentifier attemptRuleId)
            then checkScopedAttemptInputs scenarioPath scenarioId actors attempt
              actorRows relationRows stageRows completions
            else do
              if null stageRows && null completions then pure () else
                at "SFE087" scenarioPath scenarioId
                  "attempt-stage inputs are inactive for this analysis"
              converted <- mapM (checkActorAssignment scenarioPath actors
                attributedFacts attributedMental) actorRows
              if chosen == tokenText (ruleIdentifier route) then case relationRows of
                [row@(RelationAssignment _ _ _ status reason)] -> do
                  _ <- checkRelationAssignment scenarioPath actors relation row
                  pure (converted ++ [Assignment (relationStatusId relation) status reason])
                [] -> at "SFE068" scenarioPath scenarioId "aid relation required"
                _:second:_ -> at "SFE068" scenarioPath (relationAssignmentId second)
                  "duplicate aid relation"
              else if null relationRows then pure converted else
                at "SFE087" scenarioPath scenarioId "aid relation inactive for offence analysis"
          scopedEntries <- mapM (checkScopedExceptionInput scenarioPath actors
            exceptionFacts attachments active) scopedRows
          let activeTrees = [scopeTree (attachmentInstanceId item) exceptionTree
                | item <- active]
              combined = ResolvedGroup scenarioId All (selectedBranch : activeTrees)
          checked <- checkAssignments scenarioPath combined (targetEntries ++ scopedEntries)
          pure (Checked model (Just scenario) checked selectedBranch
            (Just (scopeTree (attachmentInstanceId selected) exceptionTree)))
        Just (scenarioPath, _) -> at "SFE089" scenarioPath (modelIdentifier model)
          "actor-scoped exception scenario and instance classifications required"
  _ -> at "SFE087" path (modelIdentifier model) "actor-scoped model required"

checkAbetmentScoped :: FilePath -> Model -> Maybe (FilePath, Scenario)
  -> Map.Map Text Token -> Map.Map Text (Text,Text) -> Either Diagnostic Checked
checkAbetmentScoped path model supplied quotes sources = case modelBody model of
  AbetmentLegal roles attributedFacts attributedMental assumptions offence
    abetment attempt shared@(ActorExceptionDefinition (ActorSubject subject) exception)
    attachments citations declaredOutputs -> do
      if "ResearchPrototype-v1" `Text.isSuffixOf` tokenText (modelIdentifier model)
        then pure () else at "SFE004" path (modelIdentifier model) "research model ID required"
      expect path "SFE004" (modelJurisdiction model) "Singapore"
      expect path "SFE004" (modelPurpose model) "research_prototype"
      expect path "SFE004" (modelDate model) "2026-09-13"
      let BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      mapM_ (\(item,wanted) -> expect path "SFE011" item wanted)
        [(annotation,"section107"),(holder,"defence"),(burdenKind,"legal"),
         (standard,"balance_of_probabilities")]
      if Set.fromList (map fst (Map.elems sources)) ==
          Set.fromList ["source_text","synthetic_status","contextual"]
          && Map.size sources == 3 then pure () else
        at "SFE014" path (modelIdentifier model) "three typed source roles required"
      _ <- unique path "SFE063" [(item,()) | PartyRole item _ <- roles]
      let role kind = [item | PartyRole item declared <- roles, declared == kind]
      (principal,abettor,co,attempter) <- case
        (role PrincipalParty,role AllegedAbettorParty,
         role CoConspiratorParty,role AllegedAttempterParty) of
        ([a],[b],[c],[d]) | length roles == 4 -> pure (a,b,c,d)
        _ -> at "SFE101" path (modelIdentifier model) "four typed actor roles required"
      declared <- checkScopeDeclarations path assumptions
      let requiredScopes = Set.fromList
            ["a:post-2022-section-84-expression-applicable",
             "a:dishonesty-externally-classified",
             "a:direct-s107-routes-only",
             "a:broader-section108-cases-excluded",
             "a:no-express-punishment-provision-modelled",
             "a:direct-self-attempt-only",
             "a:target-not-completed",
             "a:no-express-attempt-punishment-provision-modelled",
             "a:punishment-outside-scope",
             "a:statutory-expression-supplied",
             "a:stage-externally-classified",
             "a:impossible-attempts-excluded"]
      if Map.keysSet declared == requiredScopes then pure () else
        at "SFE100" path (modelIdentifier model) "bounded s 107 research scope required"
      offenceTree <- checkedLegalRule path quotes offence
      checkOffenceShape path offence offenceTree
      abetmentTree <- checkAbetment path quotes principal abettor co offence abetment
      let route = abetmentRule abetment
          relations = abetmentRelations abetment
          AttemptDefinition attemptRuleId (AttemptActor attemptActorId)
            (AttemptTarget attemptTargetId) intention stage = attempt
          TargetDirectedMentalState mentalId (AttemptActor mentalActor)
            (AttemptTarget mentalTarget) mentalQuote = intention
          ConductStageDefinition stageId (AttemptActor stageActor) stageOutput stageQuote = stage
      if tokenText attemptActorId == tokenText attempter
          && tokenText mentalActor == tokenText attempter
          && tokenText stageActor == tokenText attempter
          && tokenText attemptTargetId == tokenText (ruleIdentifier offence)
          && tokenText mentalTarget == tokenText attemptTargetId
          && map elementCategory (ruleElements attemptRuleId) == [Intention,SubstantialStep]
          && "stage:" `Text.isPrefixOf` tokenText stageId
        then pure () else at "SFE087" path (ruleIdentifier attemptRuleId)
          "bounded theft attempt actor or target mismatch"
      mapM_ (knownQuote path quotes) [mentalQuote,stageQuote]
      attemptRoot <- case ruleGroups attemptRuleId of
        [Group item All [mentalRef,stageRef]]
          | map tokenText [mentalRef,stageRef] == map tokenText [mentalId,stageOutput] ->
              pure item
        _ -> at "SFE087" path (ruleIdentifier attemptRuleId)
          "bounded attempt requires intention and stage"
      attemptTree <- resolveTree path
        ([Leaf (elementId item) Nothing (elementQuote item) Nothing
          | item <- ruleElements attemptRuleId] ++ ruleGroups attemptRuleId) attemptRoot
      expect path "SFE088" subject "subject:actor"
      exceptionTree <- sharedExceptionTree path shared
      mapM_ (checkElementQuote path quotes) (ruleElements exception)
      checkSharedExceptionShape path exception exceptionTree
      checkDefinitionIds path [] [offence,route,attemptRuleId,exception] []
      validateScopedAttachments path (principal,abettor,attempter)
        offence route attemptRuleId exception attachments
      checkActorScopedAuthorities path sources citations
      let expectedRows = [(elementId item,
            elementCategory item `elem` [Intention,Knowledge,Fault,DishonestIntention],
            RoleEndpoint principal) | item <- ruleElements offence]
            ++ abetmentAttributions abetment abettor
          actualRows = [(item,False,endpoint) | ActorAttributedFact item endpoint <- attributedFacts]
            ++ [(item,True,endpoint) | ActorAttributedMentalState item endpoint <- attributedMental]
          endpointKey endpoint = case endpoint of
            RoleEndpoint item -> ("role" :: Text,tokenText item)
            RelationEndpoint item -> ("relation" :: Text,tokenText item)
          rowMap rows = Map.fromList [(tokenText item,(mental,endpointKey endpoint))
            | (item,mental,endpoint) <- rows]
      _ <- unique path "SFE002" [(item,()) | (item,_,_) <- expectedRows]
      _ <- unique path "SFE002" [(item,()) | (item,_,_) <- actualRows]
      if rowMap expectedRows == rowMap actualRows then pure () else
        at "SFE067" path (ruleIdentifier route)
          "actor-specific facts or mental states have missing or wrong typed attribution"
      let expectedOutputIds = Set.fromList
            (map (tokenText . attachmentInstanceId) attachments
             ++ map (tokenText . ruleId) [offence,route,attemptRuleId]
             ++ [tokenText item | Group item _ _ <- ruleGroups offence ++
                   ruleGroups route ++ ruleGroups attemptRuleId]
             ++ [tokenText (relationStatusId relation) | relation <- relations])
      if not (null declaredOutputs) && all (\(TechnicalOutput _ item) ->
          Set.member (tokenText item) expectedOutputIds) declaredOutputs
          && all (\item -> any (\(TechnicalOutput _ target) ->
            tokenText target == tokenText item) declaredOutputs)
            [ruleId offence,ruleId route,ruleId attemptRuleId]
        then pure () else at "SFE020" path (ruleIdentifier route)
          "unknown or missing typed technical output"
      case supplied of
        Nothing -> case attachments of
          first:_ -> pure (Checked model Nothing [] offenceTree
            (Just (scopeTree (attachmentInstanceId first) exceptionTree)))
          [] -> at "SFE089" path (ruleIdentifier exception) "attachment required"
        Just (scenarioPath, scenario@(ActorScopedScenario scenarioId modelId targets
          observations bindings actorRows relationRows stageRows completions scopedRows
          plain acknowledgements)) -> do
          expect scenarioPath "SFE004" scenarioId (tokenText (modelRequest model))
          expect scenarioPath "SFE004" modelId (tokenText (modelIdentifier model))
          target <- case targets of
            [item] -> pure item
            [] -> at "SFE036" scenarioPath scenarioId "one analysis target required"
            _:second:_ -> at "SFE037" scenarioPath second "multiple analysis targets"
          selected <- case [item | item <- attachments,
            tokenText (attachmentTargetToken (attachmentTargetKind item)) == tokenText target] of
            [item] -> pure item
            _ -> at "SFE087" scenarioPath target "unknown analysis target"
          checkScopeAcknowledgements scenarioPath path scenarioId declared acknowledgements
          actors <- checkScopedActorBindings scenarioPath scenarioId roles bindings
          let chosen = tokenText target
              selectedBranch
                | chosen == tokenText (ruleIdentifier offence) = offenceTree
                | chosen == tokenText (ruleIdentifier route) = abetmentTree
                | otherwise = attemptTree
              exceptionFacts = Set.fromList (map (tokenText . elementId)
                (ruleElements exception))
          case [item | Assignment item _ _ <- plain, Set.member (tokenText item) exceptionFacts]
            ++ [item | ActorAssignment item _ _ _ <- actorRows,
              Set.member (tokenText item) exceptionFacts] of
            item:_ -> at "SFE090" scenarioPath item
              "section 84 input requires an explicit exception instance"
            [] -> pure ()
          case plain of
            Assignment item _ _:_ -> at "SFE090" scenarioPath item
              "actor-specific classifications require typed attribution"
            [] -> pure ()
          active <- checkedObservations scenarioPath selected observations attachments
          targetEntries <- if chosen == tokenText (ruleIdentifier attemptRuleId)
            then checkScopedAttemptInputs scenarioPath scenarioId actors attempt
              actorRows relationRows stageRows completions
            else do
              if null stageRows && null completions then pure () else
                at "SFE087" scenarioPath scenarioId "attempt inputs inactive"
              converted <- mapM (checkActorAssignment scenarioPath actors
                attributedFacts attributedMental) actorRows
              if chosen == tokenText (ruleIdentifier route) then do
                relationEntries <- mapM (checkAbetmentRelationInput scenarioPath actors
                  relationRows) relations
                if length relationRows == length relations then pure () else
                  at "SFE102" scenarioPath scenarioId "unexpected or duplicate relation assignment"
                pure (converted ++ relationEntries)
              else if null relationRows then pure converted else
                at "SFE102" scenarioPath scenarioId "relation inactive for offence analysis"
          scopedEntries <- mapM (checkScopedExceptionInput scenarioPath actors
            exceptionFacts attachments active) scopedRows
          let activeTrees = [scopeTree (attachmentInstanceId item) exceptionTree
                | item <- active]
              combined = ResolvedGroup scenarioId All (selectedBranch : activeTrees)
          checked <- checkAssignments scenarioPath combined (targetEntries ++ scopedEntries)
          pure (Checked model (Just scenario) checked selectedBranch
            (Just (scopeTree (attachmentInstanceId selected) exceptionTree)))
        Just (scenarioPath, _) -> at "SFE089" scenarioPath (modelIdentifier model)
          "actor-scoped route scenario required"
  _ -> at "SFE100" path (modelIdentifier model) "typed abetment model required"

checkAbetmentRelationInput :: FilePath -> Map.Map Text Token
  -> [RelationAssignment] -> ParticipationRelation -> Either Diagnostic Assignment
checkAbetmentRelationInput path actors rows relation = do
  let wanted = tokenText (relationIdentifier relation)
      selected = [row | row@(RelationAssignment item _ _ _ _) <- rows,
        tokenText item == wanted]
  row <- case selected of
    [item] -> pure item
    [] -> at "SFE102" path (relationIdentifier relation) "missing directed relation assignment"
    _:second:_ -> at "SFE002" path (relationAssignmentId second)
      "duplicate directed relation assignment"
  let RelationAssignment _ source destination status reason = row
      actor endpoint = case endpoint of
        RoleEndpoint role -> Map.lookup (tokenText role) actors
        RelationEndpoint _ -> Nothing
  if fmap tokenText (actor (relationFrom relation)) == Just (tokenText source)
      && fmap tokenText (actor (relationTo relation)) == Just (tokenText destination)
    then pure (Assignment (relationStatusId relation) status reason)
    else at "SFE102" path (relationAssignmentId row)
      "directed relation has incompatible actors"

validateScopedAttachments :: FilePath -> (Token,Token,Token)
  -> Rule -> Rule -> Rule -> Rule -> [ActorExceptionAttachment]
  -> Either Diagnostic ()
validateScopedAttachments path (principal,abettor,attempter)
    offence route attemptRuleId exception attachments = do
  _ <- unique path "SFE089" [(attachmentInstanceId item,()) | item <- attachments]
  _ <- unique path "SFE087" [(attachmentTargetToken (attachmentTargetKind item),())
    | item <- attachments]
  if length attachments == 3 then pure () else
    at "SFE089" path (ruleIdentifier exception) "three explicit actor attachments required"
  mapM_ validate attachments
  where
    validate item = do
      let instanceId = attachmentInstanceId item
          definition = attachmentDefinition item
          role = attachmentSubjectRole item
          context = attachmentContext item
      if "xi:" `Text.isPrefixOf` tokenText instanceId
          && tokenText definition == tokenText (ruleIdentifier exception)
        then pure () else at "SFE089" path instanceId
          "attachment requires the authored section 84 definition and unique instance ID"
      let target = attachmentTargetToken (attachmentTargetKind item)
          valid = case (attachmentTargetKind item,context) of
            (CandidateOffenceTarget _,PrincipalConductContext _) ->
              tokenText target == tokenText (ruleIdentifier offence)
                && tokenText role == tokenText principal
            (ParticipationAttachmentTarget _,AidConductContext _) ->
              tokenText target == tokenText (ruleIdentifier route)
                && tokenText role == tokenText abettor
            (AttemptAttachmentTarget _,AttemptConductContext _) ->
              tokenText target == tokenText (ruleIdentifier attemptRuleId)
                && tokenText role == tokenText attempter
            _ -> False
      if valid then pure () else
        if tokenText target `elem` [tokenText (ruleIdentifier offence),
          tokenText (ruleIdentifier route),tokenText (ruleIdentifier attemptRuleId)]
        then at "SFE088" path role "attachment subject or act context does not belong to target"
        else at "SFE087" path target "invalid exception attachment target"

checkActorScopedAuthorities :: FilePath -> Map.Map Text (Text,Text)
  -> [AuthorityReference] -> Either Diagnostic ()
checkActorScopedAuthorities path sources citations = do
  let expected = Map.fromList
        [("theft-conduct",(PenalCode1871,"378","source_text")),
         ("theft-anchor",(PenalCode1871,"379","source_text")),
         ("aid",(PenalCode1871,"107","source_text")),
         ("abettor",(PenalCode1871,"108","source_text")),
         ("consequence",(PenalCode1871,"109","source_text")),
         ("attempt",(PenalCode1871,"511","source_text")),
         ("general-exception",(PenalCode1871,"84","source_text")),
         ("burden-context",(EvidenceAct1893,"107","contextual"))]
      rows = [(label,(instrument,source,section))
        | AuthorityReference label instrument source section <- citations]
  actual <- unique path "SFE074" rows
  if Map.keysSet actual == Map.keysSet expected then pure () else
    at "SFE074" path (Token WordToken "authorities" 1 1)
      "typed offence, participation, attempt and burden authorities required"
  mapM_ (\(label,(instrument,source,section)) ->
    case Map.lookup (tokenText label) expected of
      Just (wantedInstrument,wantedSection,wantedRole)
        | instrument == wantedInstrument
          && tokenText section == wantedSection
          && maybe False ((== wantedRole) . fst) (Map.lookup (tokenText source) sources) ->
            pure ()
      _ -> at "SFE074" path label "authority instrument, section or source role mismatch") rows

checkActorScopedOutputs :: FilePath -> Rule -> Rule -> Rule
  -> [ActorExceptionAttachment] -> [TechnicalOutput] -> Either Diagnostic ()
checkActorScopedOutputs path offence route attemptRuleId attachments rows = do
  let instanceFor target = [attachmentInstanceId item | item <- attachments,
        tokenText (attachmentTargetToken (attachmentTargetKind item)) == tokenText target]
      outputRoot rule = case reverse (ruleGroups rule) of
        Group item _ _:_ -> item
        _ -> ruleIdentifier rule
      expected = case (instanceFor (ruleIdentifier offence),
        instanceFor (ruleIdentifier route),instanceFor (ruleIdentifier attemptRuleId)) of
        ([principal],[abettor],[attempter]) ->
          [("principal_requirements",outputRoot offence),
           ("principal_section84",principal),
           ("principal_final",ruleId offence),
           ("abettor_requirements",outputRoot route),
           ("abettor_section84",abettor),
           ("abettor_final",ruleId route),
           ("attempter_requirements",outputRoot attemptRuleId),
           ("attempter_section84",attempter),
           ("attempter_final",ruleId attemptRuleId)]
        _ -> []
  if [(tokenText label,tokenText target) | TechnicalOutput label target <- rows] ==
      [(label,tokenText target) | (label,target) <- expected]
    then pure () else at "SFE020" path (ruleIdentifier offence)
      "actor-qualified technical outputs required"

checkScopedActorBindings :: FilePath -> Token -> [PartyRole] -> [ActorBinding]
  -> Either Diagnostic (Map.Map Text Token)
checkScopedActorBindings path scenarioId roles rows = do
  bound <- unique path "SFE088" [(role,actor) | ActorBinding role actor <- rows]
  if Map.keysSet bound == Set.fromList [tokenText item | PartyRole item _ <- roles]
    then pure () else at "SFE088" path scenarioId
      "all declared actor roles require one binding"
  let actors = Map.elems bound
  if length actors == length roles && all ("actor:" `Text.isPrefixOf`) (map tokenText actors)
      && Set.size (Set.fromList (map tokenText actors)) == length roles
    then pure bound else at "SFE088" path scenarioId
      "distinct opaque actor identifiers required"

checkedObservations :: FilePath -> ActorExceptionAttachment -> [Token]
  -> [ActorExceptionAttachment] -> Either Diagnostic [ActorExceptionAttachment]
checkedObservations path selected observations attachments = do
  _ <- unique path "SFE089" [(item,()) | item <- observations]
  others <- mapM findObservation observations
  pure (selected:others)
  where
    findObservation item
      | tokenText item == tokenText (attachmentInstanceId selected) =
          at "SFE089" path item "selected instance is already active"
      | otherwise = case [attachment | attachment <- attachments,
          tokenText (attachmentInstanceId attachment) == tokenText item] of
          [attachment] -> pure attachment
          _ -> at "SFE089" path item "unknown exception instance observation"

checkScopedAttemptInputs :: FilePath -> Token -> Map.Map Text Token
  -> AttemptDefinition -> [ActorAssignment] -> [RelationAssignment]
  -> [ConductStageAssignment] -> [TargetCompletion]
  -> Either Diagnostic [Assignment]
checkScopedAttemptInputs path scenarioId actors attempt actorRows relationRows stages completions = do
  let AttemptDefinition _ (AttemptActor role) (AttemptTarget target) intention stage = attempt
      intended = attemptIntentionId intention
      stageId = attemptStageId stage
      expectedActor = Map.lookup (tokenText role) actors
  if null relationRows then pure () else at "SFE087" path scenarioId
    "aid relation is inactive for attempt analysis"
  intentionAssignment <- case actorRows of
    [ActorAssignment item actor status reason]
      | tokenText item == tokenText intended
        && fmap tokenText expectedActor == Just (tokenText actor) ->
          pure (Assignment intended status reason)
      | otherwise -> at "SFE091" path actor
          "target intention belongs to the alleged-attempter actor"
    [] -> at "SFE081" path scenarioId "attempt intention classification required"
    _:second:_ -> at "SFE091" path (actorAssignmentId second)
      "only the selected attempt intention may be supplied"
  stageAssignment <- case stages of
    [ConductStageAssignment item actor status]
      | tokenText item == tokenText stageId
        && fmap tokenText expectedActor == Just (tokenText actor) ->
          let (proof,reason) = case status of
                PreparationOnly source -> (source { tokenText = "not_proved" },Nothing)
                ActTowardsCommission source -> (source { tokenText = "proved" },Nothing)
                StageUnresolved source why -> (source { tokenText = "unresolved" },Just why)
          in pure (Assignment (attemptStageOutput stage) proof reason)
      | otherwise -> at "SFE091" path actor "attempt stage belongs to alleged attempter"
    [] -> at "SFE076" path scenarioId "attempt conduct stage required"
    _:second:_ -> at "SFE077" path (stageAssignmentId second) "duplicate conduct stage"
  case completions of
    [TargetNotCompleted item _] | tokenText item == tokenText target -> pure ()
    [TargetNotCompleted item _] -> at "SFE075" path item "attempt target cannot be replaced"
    [TargetCompleted _ item] -> at "SFE080" path item
      "completed target is outside bounded attempt analysis"
    [] -> at "SFE080" path scenarioId "target completion status required"
    _:second:_ -> at "SFE080" path (completionToken second)
      "duplicate target completion status"
  pure [intentionAssignment,stageAssignment]

checkScopedExceptionInput :: FilePath -> Map.Map Text Token -> Set.Set Text
  -> [ActorExceptionAttachment] -> [ActorExceptionAttachment]
  -> ScopedExceptionAssignment -> Either Diagnostic Assignment
checkScopedExceptionInput path actors facts attachments active row = do
  let instanceId = scopedAssignmentInstance row
      fact = scopedAssignmentFact row
  attachment <- case [item | item <- attachments,
    tokenText (attachmentInstanceId item) == tokenText instanceId] of
    [item] -> pure item
    _ -> at "SFE089" path instanceId "unknown exception instance"
  if any ((== tokenText instanceId) . tokenText . attachmentInstanceId) active
    then pure () else at "SFE093" path instanceId
      "classification for inactive exception instance"
  if Set.member (tokenText fact) facts then pure () else
    at "SFE095" path fact "unknown or cross-instance section 84 proposition"
  let expectedActor = Map.lookup (tokenText (attachmentSubjectRole attachment)) actors
  if fmap tokenText expectedActor == Just (tokenText (scopedAssignmentActor row))
    then pure () else at "SFE091" path (scopedAssignmentActor row)
      "exception classification belongs to the attachment subject actor"
  if tokenText (actContextToken (scopedAssignmentContext row)) ==
      tokenText (actContextToken (attachmentContext attachment))
    then pure () else at "SFE092" path (actContextToken (scopedAssignmentContext row))
      "exception classification uses another act context"
  pure (Assignment (scopedToken instanceId fact)
    (scopedAssignmentStatus row) (scopedAssignmentReason row))

checkAttemptAuthorities :: FilePath -> Map.Map Text (Text, Text)
  -> [AuthorityReference] -> Either Diagnostic ()
checkAttemptAuthorities path sources citations = do
  let rows = [(label,(instrument,source,section))
        | AuthorityReference label instrument source section <- citations]
      expected = Map.fromList
        [("wrongful-concepts","23"),("dishonesty","24"),
         ("theft-conduct","378"),("theft-anchor","379"),("attempt","511")]
  indexed <- unique path "SFE002" rows
  if Map.keysSet indexed == Map.keysSet expected then pure () else
    at "SFE074" path (Token WordToken "authorities" 1 1)
      "typed Penal Code authority references required"
  mapM_ (\(label,(instrument,source,section)) ->
    if instrument == PenalCode1871
      && Map.lookup (tokenText label) expected == Just (tokenText section)
      && maybe False ((== "source_text") . fst) (Map.lookup (tokenText source) sources)
    then pure () else at "SFE074" path label "attempt authority has incompatible instrument or section") rows

checkAttemptBinding :: FilePath -> Token -> Token -> [ActorBinding] -> Either Diagnostic Token
checkAttemptBinding path scenarioId role rows = case rows of
  [ActorBinding declared actor]
    | tokenText declared == tokenText role
      && "actor:" `Text.isPrefixOf` tokenText actor -> Right actor
    | otherwise -> at "SFE083" path declared "invalid alleged-attempter binding"
  [] -> at "SFE083" path scenarioId "alleged-attempter binding required"
  _:second:_ -> at "SFE083" path secondRole "duplicate or unknown actor binding"
    where ActorBinding secondRole _ = second

actorAssignmentId :: ActorAssignment -> Token
actorAssignmentId (ActorAssignment item _ _ _) = item

stageAssignmentId :: ConductStageAssignment -> Token
stageAssignmentId (ConductStageAssignment item _ _) = item

completionToken :: TargetCompletion -> Token
completionToken (TargetNotCompleted item _) = item
completionToken (TargetCompleted item _) = item

checkElementQuote :: FilePath -> Map.Map Text Token -> Element -> Either Diagnostic ()
checkElementQuote path quotes item = do
  if "f:" `Text.isPrefixOf` tokenText (elementId item) then pure ()
    else at "SFE017" path (elementId item) "primitive input requires f: identifier"
  knownQuote path quotes (elementQuote item)
  mapM_ (knownQuote path quotes) (maybe [] (:[]) (elementSupport item))

checkParticipationSources :: FilePath -> Map.Map Text (Text, Text)
  -> [StatutoryDefinition] -> Rule -> Rule
  -> [AuthorityReference] -> Either Diagnostic ()
checkParticipationSources path sources definitions offence route citations = do
  if Set.fromList (map fst (Map.elems sources)) ==
      Set.fromList ["source_text", "synthetic_status", "contextual"]
      && Map.size sources == 3 then pure () else
    at "SFE014" path (Token WordToken "provenance" 1 1)
      "participation model needs source, status and contextual authority references"
  let labels = [(label, (instrument, source, section))
        | AuthorityReference label instrument source section <- citations]
  index <- unique path "SFE002" labels
  let expected = Map.fromList
        [("wrongful-concepts", (PenalCode1871,"23","source_text"))
        ,("dishonesty", (PenalCode1871,"24","source_text"))
        ,("theft-conduct", (PenalCode1871,"378","source_text"))
        ,("theft-anchor", (PenalCode1871,"379","source_text"))
        ,("abetment", (PenalCode1871,"107","source_text"))
        ,("abettor", (PenalCode1871,"108","source_text"))
        ,("consequence", (PenalCode1871,"109","source_text"))
        ,("burden-context", (EvidenceAct1893,"107","contextual"))]
  if Map.keysSet index == Map.keysSet expected then pure () else
    at "SFE073" path (Token WordToken "authorities" 1 1)
      "typed statutory-authority references required for each modelled provision"
  mapM_ (checkOne expected) labels
  let sections = map (map (tokenText . sectionToken) . definitionSections) definitions
      sectionToken (StatutorySection item) = item
      offenceSections = map (tokenText . sectionToken) (ruleSections offence)
      routeSections = map (tokenText . sectionToken) (ruleSections route)
  if sections == [["23"],["23"],["24"]]
      && offenceSections == ["378","379"]
      && routeSections == ["107","108","109"] then pure () else
    at "SFE074" path (ruleIdentifier offence)
      "modelled sections must match their typed Penal Code authority references"
  where
    checkOne expected (label,(instrument,source,section)) =
      case Map.lookup (tokenText label) expected of
        Just (wantedInstrument,wantedSection,wantedRole) ->
          if instrument == wantedInstrument && tokenText section == wantedSection
            && maybe False ((== wantedRole) . fst) (Map.lookup (tokenText source) sources)
          then Right () else at "SFE074" path label
            "authority instrument, source ID or section has the wrong legal role"
        Nothing -> at "SFE073" path label "unknown statutory authority use"

checkPartyRoles :: FilePath -> [PartyRole] -> Either Diagnostic (Token, Token)
checkPartyRoles path rows = do
  _ <- unique path "SFE063" [(role,()) | PartyRole role _ <- rows]
  case rows of
    [PartyRole principal PrincipalParty, PartyRole abettor AllegedAbettorParty]
      | tokenText principal /= tokenText abettor -> Right (principal,abettor)
    [PartyRole abettor AllegedAbettorParty, PartyRole principal PrincipalParty]
      | tokenText principal /= tokenText abettor -> Right (principal,abettor)
    PartyRole token _: _ -> at "SFE063" path token
      "exactly one principal and one alleged-abettor role required"
    [] -> at "SFE063" path (Token WordToken "party-roles" 1 1)
      "principal and alleged-abettor roles required"

checkParticipationShape :: FilePath -> Map.Map Text Token -> Rule -> Resolved
  -> Rule -> ParticipationRelation -> Either Diagnostic ()
checkParticipationShape path quotes offence offenceTree route relation = do
  if ruleKind route == ParticipationKind &&
      fmap tokenText (ruleTarget route) == Just (tokenText (ruleIdentifier offence))
    then pure () else at "SFE069" path (ruleIdentifier route)
      "participation must target the declared candidate offence"
  if map (\(StatutorySection item) -> tokenText item) (ruleSections route) ==
      ["107","108","109"] then pure () else
    at "SFE074" path (ruleIdentifier route)
      "bounded intentional-aid route requires Penal Code ss 107–109"
  if ruleDefinitionReferences route == [] then pure () else
    at "SFE069" path (ruleIdentifier route)
      "participation cannot access a definition directly"
  let endpoint (RoleEndpoint item) = tokenText item
      endpoint (RelationEndpoint item) = tokenText item
      offenceRoot = case offenceTree of
        ResolvedGroup item _ _ -> item
        ResolvedLeaf item _ -> item
  if "rel:" `Text.isPrefixOf` tokenText (relationIdentifier relation)
      && endpoint (relationFrom relation) == "role:alleged-abettor"
      && endpoint (relationTo relation) == "role:principal"
      && case relationTarget relation of
        ParticipationTarget target -> tokenText target == tokenText (ruleIdentifier offence)
      && "f:" `Text.isPrefixOf` tokenText (relationStatusId relation)
    then pure () else at "SFE068" path (relationIdentifier relation)
      "relation requires alleged-abettor to principal and the declared offence target"
  knownQuote path quotes (relationQuote relation)
  mapM_ (checkElementQuote path quotes) (ruleElements route)
  let categories = Map.fromList [(tokenText (elementId item),elementCategory item)
        | item <- ruleElements route]
      category item = Map.lookup (tokenText item) categories
  case ruleGroups route of
    [Group aidForm Any [aidAct, omission],
     Group aid All [intention, relationStatus, aidFormRef],
     Group _ All [targetRef, aidRef, consequence]]
      | tokenText aidForm == tokenText aidFormRef
        && tokenText aid == tokenText aidRef
        && tokenText targetRef == tokenText offenceRoot
        && tokenText relationStatus == tokenText (relationStatusId relation)
        && map category [aidAct,omission,intention,consequence] ==
          map Just [AidAct,IllegalOmission,Intention,Consequence]
        && length (ruleElements route) == 4 -> pure ()
    _ -> at "SFE070" path (ruleIdentifier route)
      "intentional aid needs act-or-illegal-omission, distinct intention and consequence"
  let offenceIds = Set.fromList (treeIds offenceTree)
      ownIds = map tokenText
        (relationStatusId relation : map elementId (ruleElements route)
          ++ map identifier (ruleGroups route))
  if Set.null (Set.intersection offenceIds (Set.fromList ownIds))
      && Set.size (Set.fromList ownIds) == length ownIds then pure () else
    at "SFE002" path (ruleIdentifier route)
      "participation and target proposition IDs must be distinct"
  where
    treeIds (ResolvedLeaf item _) = [tokenText item]
    treeIds (ResolvedGroup item _ children) =
      tokenText item : concatMap treeIds children

checkParticipationAttributions :: FilePath -> Token -> Token
  -> [StatutoryDefinition] -> Rule -> Rule -> ParticipationRelation
  -> [ActorAttributedFact] -> [ActorAttributedMentalState] -> Either Diagnostic ()
checkParticipationAttributions path principal abettor definitions offence route relation facts mental = do
  let isMental kind = kind `elem` [Intention,Knowledge,Fault,DishonestIntention]
      definitionMap = Map.fromList [(tokenText (definitionId item),item) | item <- definitions]
      selectedDefinitions = reachableDefinitions definitionMap offence
      principalRows = [(elementId item,(isMental (elementCategory item),RoleEndpoint principal))
        | item <- concatMap definitionLeaves selectedDefinitions ++ ruleElements offence]
      routeRows = [(elementId item,(isMental (elementCategory item),
        if elementCategory item == Consequence then RelationEndpoint (relationIdentifier relation)
        else RoleEndpoint abettor)) | item <- ruleElements route]
      relationRows = [(relationStatusId relation,
        (False,RelationEndpoint (relationIdentifier relation)))]
      expectedRows = principalRows ++ routeRows ++ relationRows
      actualRows = [(item,(False,endpoint)) | ActorAttributedFact item endpoint <- facts]
        ++ [(item,(True,endpoint)) | ActorAttributedMentalState item endpoint <- mental]
  expected <- unique path "SFE002" expectedRows
  actual <- unique path "SFE002" actualRows
  if Map.keysSet expected == Map.keysSet actual then pure () else
    at "SFE065" path (ruleIdentifier route)
      "every actor-specific primitive needs exactly one typed attribution"
  let endpointKey :: RelationEndpoint -> (Text,Text)
      endpointKey (RoleEndpoint item) = ("role",tokenText item)
      endpointKey (RelationEndpoint item) = ("relation",tokenText item)
      equalAttribution (kind,endpoint) (otherKind,otherEndpoint) =
        kind == otherKind && endpointKey endpoint == endpointKey otherEndpoint
  case [item | (item,wanted) <- expectedRows,
        maybe True (not . equalAttribution wanted) (Map.lookup (tokenText item) actual)] of
    item:_ -> at "SFE067" path item
      "fact or mental state attributed to wrong role or relation"
    [] -> pure ()

checkParticipationOutputs :: FilePath -> Rule -> Rule -> ParticipationRelation
  -> [TechnicalOutput] -> Either Diagnostic ()
checkParticipationOutputs path offence route relation rows = do
  let offenceRoot = case reverse (ruleGroups offence) of
        Group item _ _:_ -> item
        _ -> ruleIdentifier offence
      ids kind = [elementId item | item <- ruleElements route,
        elementCategory item == kind]
      groups = [item | Group item _ _ <- ruleGroups route]
      expected = case (ids Intention,ids AidAct,ids IllegalOmission,ids Consequence,groups) of
        ([intention],[act],[omission],[consequence],[aidForm,aid,root]) ->
          Just [("principal_target",offenceRoot),("aid_intention",intention),
            ("aid_by_act",act),("aid_illegal_omission",omission),
            ("aid_relationship",relationStatusId relation),
            ("aid_form",aidForm),("intentional_aid",aid),
            ("commission_in_consequence",consequence),
            ("section109_candidate",root),("final_rule",ruleId route)]
        _ -> Nothing
  case expected of
    Just pairs | map (\(TechnicalOutput label target) ->
      (tokenText label,tokenText target)) rows ==
      [(label,tokenText target) | (label,target) <- pairs] -> pure ()
    _ -> at "SFE020" path (ruleIdentifier route)
      "participation technical outputs differ from typed declarations"

checkActorBindings :: FilePath -> Token -> Token -> [ActorBinding]
  -> Either Diagnostic (Map.Map Text Token)
checkActorBindings path principal abettor rows = do
  bindings <- unique path "SFE064" [(role,actor) | ActorBinding role actor <- rows]
  if Map.keysSet bindings == Set.fromList [tokenText principal,tokenText abettor]
    then pure () else case rows of
      ActorBinding item _:_ -> at "SFE063" path item
        "missing or unknown participant role binding"
      [] -> at "SFE064" path principal "principal and alleged-abettor bindings required"
  let actors = Map.elems bindings
  case actors of
    [first,second] | all ("actor:" `Text.isPrefixOf`) (map tokenText actors)
      && tokenText first /= tokenText second -> pure ()
    first:_ -> at "SFE064" path first
      "distinct opaque actor identifiers required for this bounded POC"
    [] -> at "SFE064" path principal "participant actor bindings required"
  pure bindings

relationAssignmentId :: RelationAssignment -> Token
relationAssignmentId (RelationAssignment item _ _ _ _) = item

checkRelationAssignment :: FilePath -> Map.Map Text Token -> ParticipationRelation
  -> RelationAssignment -> Either Diagnostic RelationAssignment
checkRelationAssignment path actors relation row@(RelationAssignment item source destination _ _) = do
  let expectedSource = Map.lookup "role:alleged-abettor" actors
      expectedDestination = Map.lookup "role:principal" actors
  if tokenText item == tokenText (relationIdentifier relation)
      && fmap tokenText expectedSource == Just (tokenText source)
      && fmap tokenText expectedDestination == Just (tokenText destination)
    then Right row else at "SFE068" path item
      "relation endpoints or identifier do not match declared direction"

checkActorAssignment :: FilePath -> Map.Map Text Token
  -> [ActorAttributedFact] -> [ActorAttributedMentalState]
  -> ActorAssignment -> Either Diagnostic Assignment
checkActorAssignment path actors facts mental (ActorAssignment item suppliedActor status reason) = do
  let declarations = [(key,endpoint) | ActorAttributedFact key endpoint <- facts]
        ++ [(key,endpoint) | ActorAttributedMentalState key endpoint <- mental]
      expected = lookup (tokenText item)
        [(tokenText key,endpoint) | (key,endpoint) <- declarations]
      actual = case expected of
        Just (RoleEndpoint role) -> Map.lookup (tokenText role) actors
        Just (RelationEndpoint relation) -> Just relation
        Nothing -> Nothing
  case expected of
    Nothing -> at "SFE065" path item "unknown or unselected actor-specific fact"
    Just _ | fmap tokenText actual == Just (tokenText suppliedActor) ->
      Right (Assignment item status reason)
    Just _ -> at "SFE067" path suppliedActor
      "classification attributed to wrong actor or relation"

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
