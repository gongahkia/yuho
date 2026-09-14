{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Explain (explainChecked) where

import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Protocol.Json (decodeJson)
import Yuho.Exception.Types (Truth(..))
import Yuho.Surface.AST
import Yuho.Surface.ActorExceptions
  ( actContextToken, attachmentRuleId, attachmentTargetToken, sharedExceptionTree )
import Yuho.Surface.Definitions (reachableDefinitions)
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Token (Diagnostic, Token(..), at)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)
import Yuho.SuppliedProofStatus.Types
  ( ProofBranch(..), ProofReason(..), ProofResult(..), ProofRule(..), ProofTrace(..)
  , satisfactionText )
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

explainChecked :: FilePath -> Checked -> Either Diagnostic Text
explainChecked path checked@(Checked model scenario assignments offenceTree exceptionTree) =
  case (scenario, exceptionTree) of
    (Just (ActorScopedScenario _ _ [target] observed bindings _ _ stages _ _ _ acknowledgements),
      Just scopedExceptionTree) -> case modelBody model of
      ActorScopedLegal _ _ _ _ offence (IntentionalAidRoute route _) attempt shared
        attachments citations _ -> do
        attachment <- case [item | item <- attachments,
          tokenText (attachmentTargetToken (attachmentTargetKind item)) == tokenText target] of
          [item] -> Right item
          _ -> at "SFE087" path target "selected actor attachment missing"
        let ActorExceptionDefinition _ sharedRule = shared
            AttemptDefinition authoredAttemptRule _ _ _ _ = attempt
            selectedRule
              | tokenText target == tokenText (ruleIdentifier offence) = offence
              | tokenText target == tokenText (ruleIdentifier route) = route
              | otherwise = authoredAttemptRule
            selectedInstance = attachmentInstanceId attachment
            subjectRole = attachmentSubjectRole attachment
            subjectActor = case [tokenText actor | ActorBinding role actor <- bindings,
              tokenText role == tokenText subjectRole] of
              [actor] -> actor
              _ -> "missing"
        request <- lowerChecked checked
        value <- either (const (at "SFE014" path (modelIdentifier model)
          "compiled request is invalid JSON")) Right (decodeJson request)
        decoded <- kernel (decodeProofRequest value)
        validated <- kernel (validateProofRequest decoded)
        result <- kernel (evaluateProof validated)
        _ <- kernel (selectProofPenalties validated result)
        selectedResult <- case [item | item <- proofResultRules result,
          proofRuleId item == tokenText (ruleId selectedRule)] of
          [item] -> Right item
          _ -> at "SFE014" path (ruleId selectedRule) "selected technical rule result missing"
        exceptionResult <- case [item | item <- proofResultRules result,
          proofRuleId item == tokenText (attachmentRuleId selectedInstance)] of
          [item] -> Right (Just item)
          [] -> Right Nothing
          _ -> at "SFE014" path selectedInstance "ambiguous exception instance result"
        branch <- case proofRuleBranches selectedResult of
          [item] -> Right item
          _ -> at "SFE014" path (ruleId selectedRule) "selected branch result missing"
        authoredTree <- sharedExceptionTree path shared
        let supplied = Map.fromList [(tokenText item, proofText status)
              | (item,status) <- assignments]
            selectedTrace = traceValues selectedResult
            exceptionTrace = maybe Map.empty traceValues exceptionResult
            ActorScopedExceptionResult _ scopedStatus = ActorScopedExceptionResult attachment
              (case fmap proofRuleStatus exceptionResult of
                Just TrueValue -> ExceptionSatisfied
                Just FalseValue -> ExceptionNotSatisfied
                Just UnresolvedValue -> ExceptionUnresolved
                Nothing -> ExceptionNotEvaluated)
            BurdenAnnotation annotation holder burdenKind standard = modelBurden model
            otherLine item =
              let instanceId = attachmentInstanceId item
                  observedHere = tokenText instanceId `elem` map tokenText observed
                  status = case [row | row <- proofResultRules result,
                    proofRuleId row == tokenText (attachmentRuleId instanceId)] of
                    [row] -> satisfactionText (proofRuleStatus row)
                    _ -> "not_evaluated"
              in "  " <> tokenText instanceId <> " — " <>
                (if observedHere then "observed " <> status <> "; did not affect this branch"
                 else "inactive for this analysis")
            sourceLines = ["  " <> tokenText (elementId item) <> " -> "
                <> tokenText (elementQuote item) | item <- ruleElements
                  sharedRule]
            authorityLines = ["  " <> tokenText label <> ": "
              <> instrumentText instrument <> " s " <> tokenText section
              | AuthorityReference label instrument _ section <- citations]
            stageLines = case stages of
              [ConductStageAssignment _ _ (PreparationOnly _)] ->
                ["Conduct stage: preparation_only — externally classified"]
              [ConductStageAssignment _ _ (ActTowardsCommission _)] ->
                ["Conduct stage: act_towards_commission — externally classified"]
              [ConductStageAssignment _ _ (StageUnresolved _ why)] ->
                ["Conduct stage: unresolved(" <> tokenText why <> ") — externally classified"]
              _ -> []
            output =
              ["Model: " <> tokenText (modelIdentifier model)
              ,"Jurisdiction: Singapore — research POC; synthetic classifications only"
              ,"Analysis target: " <> tokenText target
              ,"Subject: " <> subjectActor <> " (" <> tokenText subjectRole <> ")"
              ,"Selected statutory sections: Penal Code ss " <> sectionList (ruleSections selectedRule)]
              ++ stageLines ++
              ["Selected technical requirements:"]
              ++ renderTree 1 supplied selectedTrace offenceTree ++
              ["General exception instance: " <> tokenText selectedInstance
              ,"Definition: " <> tokenText (ruleIdentifier sharedRule)
                <> " — Penal Code s 84; shared legal structure, independent classifications"
              ,"Attachment: " <> tokenText selectedInstance <> " -> " <> tokenText target
              ,"Act context: " <> tokenText (actContextToken (attachmentContext attachment))
              ,"Section 84 routes (authored ID [instantiated ID]):"]
              ++ renderScopedTree 1 supplied exceptionTrace authoredTree scopedExceptionTree ++
              ["Section 84 source references:"] ++ sourceLines ++
              ["Selected section 84 instance status: "
                <> case scopedStatus of
                  ExceptionSatisfied -> "satisfied"
                  ExceptionNotSatisfied -> "not_satisfied"
                  ExceptionUnresolved -> "unresolved"
                  ExceptionNotEvaluated ->
                    "not_evaluated (selected branch did not satisfy its requirements)"
              ,"Other actor instances:"]
              ++ [otherLine item | item <- attachments,
                   tokenText (attachmentInstanceId item) /= tokenText selectedInstance] ++
              ["Typed statutory references:"] ++ authorityLines ++
              ["Evidence Act s 107 context: " <> tokenText annotation <> "; "
                <> tokenText holder <> " " <> tokenText burdenKind <> " burden; "
                <> tokenText standard <> ". It does not classify evidence."
              ,"Scope assumptions: acknowledged by scenario, not inferred or proved"]
              ++ ["  " <> tokenText item | ScopeAcknowledgement item <- acknowledgements] ++
              ["Final technical status: " <> satisfactionText (proofResultStatus result)
                <> " (" <> reasonText (proofBranchReason branch) <> ")"
              ,"No guilt, conviction, acquittal, liability, diagnosis, sentence or court disposition was determined."]
        Right (Text.unlines output)
      AbetmentLegal _ _ _ _ offence abetment attempt shared attachments citations _ ->
        explainAbetment path checked target observed bindings stages acknowledgements
          offence abetment attempt shared attachments citations offenceTree scopedExceptionTree
      _ -> at "SFE013" path (modelIdentifier model)
        "explain requires a checked actor-scoped research model"
    (Just (AttemptScenario _ _ bindings _ stages completions _ acknowledgements _), Nothing) ->
      case modelBody model of
        AttemptLegal _ _ _ target attempt citations _ -> do
          request <- lowerChecked checked
          value <- either (const (at "SFE014" path (modelIdentifier model)
            "compiled request is invalid JSON")) Right (decodeJson request)
          decoded <- kernel (decodeProofRequest value)
          validated <- kernel (validateProofRequest decoded)
          result <- kernel (evaluateProof validated)
          _ <- kernel (selectProofPenalties validated result)
          evaluated <- case [item | item <- proofResultRules result,
            proofRuleId item == tokenText (ruleId (attemptRule attempt))] of
            [item] -> Right item
            _ -> at "SFE014" path (ruleId (attemptRule attempt))
              "attempt rule result missing"
          let AttemptDefinition _ (AttemptActor role) (AttemptTarget targetId)
                intention stageDefinition = attempt
              actor = case [tokenText item | ActorBinding declared item <- bindings,
                tokenText declared == tokenText role] of
                [item] -> item
                _ -> "missing"
              stageText = case stages of
                [ConductStageAssignment _ _ (PreparationOnly _)] -> "preparation_only"
                [ConductStageAssignment _ _ (ActTowardsCommission _)] ->
                  "act_towards_commission"
                [ConductStageAssignment _ _ (StageUnresolved _ reason)] ->
                  "unresolved(" <> tokenText reason <> ")"
                _ -> "missing"
              completionText = case completions of
                [TargetNotCompleted _ _] -> "not_completed"
                [TargetCompleted _ _] -> "completed"
                _ -> "missing"
              supplied = Map.fromList [(tokenText item, proofText status)
                | (item,status) <- assignments]
              technical = traceValues evaluated
              authorities = ["  " <> tokenText label <> ": "
                <> instrumentText instrument <> " s " <> tokenText section
                | AuthorityReference label instrument _ section <- citations]
              linesOfText =
                ["Model: " <> tokenText (modelIdentifier model)
                ,"Jurisdiction: Singapore — research POC; synthetic classifications only"
                ,"Analysis target: bounded Penal Code s 511 attempt"
                ,"Alleged-attempter: " <> actor
                ,"Intended target: " <> tokenText targetId <> " — Penal Code ss "
                  <> sectionList (ruleSections target)
                ,"Target reference only; completed theft requirements are not executable prerequisites."
                ,"Target completion: " <> completionText <> " — supplied scope status, not a kernel fact"
                ,"Target-directed intention: " <> tokenText (attemptIntentionId intention)
                  <> " — supplied " <> Map.findWithDefault "missing"
                    (tokenText (attemptIntentionId intention)) supplied
                ,"Conduct stage: " <> tokenText (attemptStageId stageDefinition)
                  <> " — supplied " <> stageText
                ,"Yuho did not determine the conduct-stage classification or assess evidence."
                ,"Act-toward-commission projection: " <> tokenText (attemptStageOutput stageDefinition)
                  <> " — technical " <> Map.findWithDefault "not_evaluated"
                    (tokenText (attemptStageOutput stageDefinition)) technical
                ,"Bounded s 511 requirements:"]
                ++ renderTree 1 supplied technical offenceTree
                ++ ["Typed statutory references:"] ++ authorities
                ++ ["Scope assumptions: acknowledged by scenario, not inferred or proved"]
                ++ ["  " <> tokenText item | ScopeAcknowledgement item <- acknowledgements]
                ++ ["Final technical attempt status: "
                  <> satisfactionText (proofResultStatus result)
                  ,"No guilt, conviction, acquittal, liability, punishment, sentence or court disposition was determined."]
          Right (Text.unlines linesOfText)
        _ -> at "SFE013" path (modelIdentifier model)
          "explain requires a checked attempt scenario"
    (Just (ParticipationScenario _ _ bindings _ _ _ acknowledgements _), Nothing) ->
      case (modelBody model, offenceTree) of
        (ParticipationLegal _ definitions _ _ _ offence
          (IntentionalAidRoute route relation) citations _,
          ResolvedGroup _ _ [principalTree, aidTree, consequenceTree]) -> do
          request <- lowerChecked checked
          value <- either (const (at "SFE014" path (modelIdentifier model)
            "compiled request is invalid JSON")) Right (decodeJson request)
          decoded <- kernel (decodeProofRequest value)
          validated <- kernel (validateProofRequest decoded)
          result <- kernel (evaluateProof validated)
          _ <- kernel (selectProofPenalties validated result)
          evaluated <- case [item | item <- proofResultRules result,
            proofRuleId item == tokenText (ruleId route)] of
            [item] -> Right item
            _ -> at "SFE014" path (ruleId route) "participation rule result missing"
          let actor role = case [tokenText item | ActorBinding declared item <- bindings,
                tokenText declared == role] of
                [item] -> item
                _ -> "missing"
              supplied = Map.fromList [(tokenText item, proofText status)
                | (item,status) <- assignments]
              technical = traceValues evaluated
              selectedDefinitions = reachableDefinitions
                (Map.fromList [(tokenText (definitionId item),item) | item <- definitions]) offence
              definitionLines = concat
                [["  " <> tokenText (definitionId definition) <> " — Penal Code s "
                   <> sectionList (definitionSections definition)] ++
                 ["    " <> tokenText (elementId element) <> " targets "
                   <> tokenText target <> " (type-checked, not an occurrence finding)"
                  | MentalStateInput element _ target _ <- definitionMentalStates definition]
                | definition <- selectedDefinitions]
              authorityLines = ["  " <> tokenText label <> ": "
                <> instrumentText instrument <> " s " <> tokenText section
                <> " (" <> tokenText source <> ")"
                | AuthorityReference label instrument source section <- citations]
              acknowledged = [tokenText item | ScopeAcknowledgement item <- acknowledgements]
              output =
                ["Model: " <> tokenText (modelIdentifier model)
                ,"Jurisdiction: Singapore — research POC; synthetic classifications only"
                ,"Analysis target: bounded intentional-aid participation"
                ,"Scope assumptions: acknowledged by scenario, not inferred or proved"]
                ++ map ("  " <>) acknowledged
                ++ ["Principal role: " <> actor "role:principal"
                   ,"Candidate target: theft, Penal Code ss " <> sectionList (ruleSections offence)
                   ,"Reachable statutory definitions:"]
                ++ definitionLines
                ++ ["Principal target requirements:"]
                ++ renderTree 1 supplied technical principalTree
                ++ ["Alleged-abettor role: " <> actor "role:alleged-abettor"
                   ,"Intentional assistance and aid form:"]
                ++ renderTree 1 supplied technical aidTree
                ++ ["Relationship: " <> actor "role:alleged-abettor" <> " -> "
                   <> actor "role:principal" <> "; target "
                   <> case relationTarget relation of ParticipationTarget item -> tokenText item
                   ,"Relationship status: supplied " <>
                     Map.findWithDefault "missing" (tokenText (relationStatusId relation)) supplied
                   ,"Commission in consequence:"]
                ++ renderTree 1 supplied technical consequenceTree
                ++ ["Candidate participation provisions:"] ++ authorityLines
                ++ ["Evidence Act s 107 is contextual here; it does not classify evidence or establish the aid route."
                   ,"Final technical participation status: "
                     <> satisfactionText (proofResultStatus result)
                   ,"No guilt, conviction, acquittal, liability, punishment or sentence was determined."]
          Right (Text.unlines output)
        _ -> at "SFE013" path (modelIdentifier model)
          "explain requires a checked intentional-aid scenario"
    (Just (Scenario _ _ _ acknowledgements targets), Just defenceTree) -> do
      (offence, exception, introduction, definitionLines, sourceReferences, offenceHeading) <-
        case modelBody model of
          Legal _ selected shared _ | null targets -> Right
            (selected, shared, [], [], [], "Candidate offence chain (Penal Code ss 319, 321, 323):")
          MultiLegal _ offences exceptions attachments _ -> case targets of
            [target] -> case [(selected, shared) | selected <- offences,
              tokenText (ruleIdentifier selected) == tokenText target,
              Attachment _ exceptionId owner <- attachments,
              tokenText owner == tokenText target,
              GeneralException shared <- exceptions,
              tokenText (ruleIdentifier shared) == tokenText exceptionId] of
              [(selected, shared)] -> Right
                (selected, shared,
                 ["Selected candidate offence: " <> tokenText target
                 ,"Candidate statutory sections: Penal Code ss " <>
                    sectionList (ruleSections selected)
                 ,"General exception: Penal Code s " <> sectionList (ruleSections shared)
                 ,"Attachment: s " <> sectionList (ruleSections shared)
                    <> " -> candidate " <> tokenText target
                 ,"Definition instance: shared " <> tokenText (ruleIdentifier shared)],
                 [],
                 ["  " <> tokenText (elementId item) <> " -> "
                   <> tokenText (elementQuote item)
                   <> maybe "" (\support -> " + " <> tokenText support) (elementSupport item)
                  | item <- ruleElements shared],
                 "Selected candidate offence requirements:")
              _ -> at "SFE040" path target "selected exception attachment is not unique"
            _ -> at "SFE036" path (modelIdentifier model) "one analysis target required"
          DefinitionsLegal definitions _ offences exceptions attachments _ ->
            case targets of
              [target] -> case [(selected, shared) | selected <- offences,
                tokenText (ruleIdentifier selected) == tokenText target,
                Attachment _ exceptionId owner <- attachments,
                tokenText owner == tokenText target,
                GeneralException shared <- exceptions,
                tokenText (ruleIdentifier shared) == tokenText exceptionId] of
                [(selected, shared)] ->
                  let index = Map.fromList [(tokenText (definitionId item), item)
                        | item <- definitions]
                      selectedDefinitions = reachableDefinitions index selected
                      describe definition =
                        ["Statutory definition: " <> tokenText (definitionId definition)
                          <> " — Penal Code s " <> sectionList (definitionSections definition)
                        ,"  Derived output: " <> Text.intercalate ", "
                          [tokenText item | DefinitionOutput item <- definitionOutputs definition]
                        ] ++ ["  Mental-state target: " <> tokenText (elementId element)
                          <> " -> " <> tokenText targetId <> " (type-checked; not an executable dependency)"
                          | MentalStateInput element _ targetId _ <- definitionMentalStates definition]
                  in Right
                    (selected, shared,
                     ["Selected candidate offence: " <> tokenText target
                     ,"Candidate statutory sections: Penal Code ss " <>
                       sectionList (ruleSections selected)
                     ,"General exception: Penal Code s " <> sectionList (ruleSections shared)
                     ,"Attachment: s " <> sectionList (ruleSections shared)
                       <> " -> candidate " <> tokenText target
                     ,"Definition instance: shared " <> tokenText (ruleIdentifier shared)],
                     concatMap describe selectedDefinitions ++
                       ["Referenced by: " <> tokenText (ruleIdentifier selected)],
                     ["  " <> tokenText (elementId item) <> " -> "
                       <> tokenText (elementQuote item)
                       <> maybe "" (\support -> " + " <> tokenText support) (elementSupport item)
                      | item <- ruleElements shared],
                     "Selected candidate offence requirements:")
                _ -> at "SFE040" path target "selected exception attachment is not unique"
              _ -> at "SFE036" path (modelIdentifier model) "one analysis target required"
          _ -> at "SFE013" path (modelIdentifier model)
            "explain requires a checked research offence model and scenario"
      request <- lowerChecked checked
      value <- either (const (at "SFE014" path (modelIdentifier model) "compiled request is invalid JSON"))
        Right (decodeJson request)
      decoded <- kernel (decodeProofRequest value)
      validated <- kernel (validateProofRequest decoded)
      result <- kernel (evaluateProof validated)
      _ <- kernel (selectProofPenalties validated result)
      offenceResult <- case [item | item <- proofResultRules result,
        proofRuleId item == tokenText (ruleId offence)] of
        [item] -> Right item
        _ -> at "SFE014" path (ruleId offence) "candidate rule result missing"
      branch <- case proofRuleBranches offenceResult of
        [item] -> Right item
        _ -> at "SFE014" path (ruleId offence) "candidate branch result missing"
      let defenceResult = case [item | item <- proofResultRules result,
            proofRuleId item == tokenText (ruleId exception)] of
            [item] -> Just item
            _ -> Nothing
          supplied = Map.fromList [(tokenText item, proofText status)
            | (item, status) <- assignments]
          offenceValues = traceValues offenceResult
          defenceValues = maybe Map.empty traceValues defenceResult
          acknowledged = [tokenText item | ScopeAcknowledgement item <- acknowledgements]
          BurdenAnnotation annotation holder burdenKind standard = modelBurden model
          linesOfText =
            ["Model: " <> tokenText (modelIdentifier model)
            ,"Jurisdiction: " <> tokenText (modelJurisdiction model)
              <> " — research POC; synthetic classifications only"
            ] ++ introduction ++
            ["Scope assumptions: acknowledged by scenario, not inferred or proved"]
            ++ map ("  " <>) acknowledged
            ++ definitionLines
            ++ [offenceHeading]
            ++ renderTree 1 supplied offenceValues offenceTree
            ++ ["Section 84 general exception:"]
            ++ renderTree 1 supplied defenceValues defenceTree
            ++ (if null sourceReferences then [] else
                  "Section 84 source references:" : sourceReferences)
            ++ ["Section 84 kernel rule: " <>
                  maybe "not_evaluated" (satisfactionText . proofRuleStatus) defenceResult
                ,"Section 107 context: " <> tokenText annotation <> "; "
                  <> tokenText holder <> " " <> tokenText burdenKind <> " burden; "
                  <> tokenText standard <> ". This annotation does not classify evidence."
                ,"Final technical status: " <> satisfactionText (proofResultStatus result)
                  <> " (" <> reasonText (proofBranchReason branch) <> ")"
                ,"No guilt, conviction, acquittal or sentence was determined."]
      Right (Text.unlines linesOfText)
    _ -> at "SFE013" path (modelIdentifier model)
      "explain requires a checked research offence model and scenario"
  where
    kernel result = either (const (at "SFE014" path (modelIdentifier model)
      "Haskell kernel rejected the compiled research model")) Right result

explainAbetment :: FilePath -> Checked -> Token -> [Token] -> [ActorBinding]
  -> [ConductStageAssignment] -> [ScopeAcknowledgement] -> Rule -> Abetment
  -> AttemptDefinition -> ActorExceptionDefinition -> [ActorExceptionAttachment]
  -> [AuthorityReference] -> Resolved -> Resolved -> Either Diagnostic Text
explainAbetment path checked@(Checked model _ assignments _ _) target observed bindings
    stages acknowledgements offence abetment attempt shared attachments citations
    selectedTree scopedTree = do
  attachment <- case [item | item <- attachments,
    tokenText (attachmentTargetToken (attachmentTargetKind item)) == tokenText target] of
    [item] -> Right item
    _ -> at "SFE087" path target "selected actor attachment missing"
  let route = abetmentRule abetment
      AttemptDefinition attemptRuleId _ _ _ _ = attempt
      selectedRule
        | tokenText target == tokenText (ruleIdentifier offence) = offence
        | tokenText target == tokenText (ruleIdentifier route) = route
        | otherwise = attemptRuleId
      instanceId = attachmentInstanceId attachment
      actor role = case [tokenText item | ActorBinding declared item <- bindings,
        tokenText declared == role] of
        [item] -> item
        _ -> "missing"
  request <- lowerChecked checked
  value <- either (const (at "SFE014" path (modelIdentifier model)
    "compiled request is invalid JSON")) Right (decodeJson request)
  decoded <- kernel (decodeProofRequest value)
  validated <- kernel (validateProofRequest decoded)
  result <- kernel (evaluateProof validated)
  _ <- kernel (selectProofPenalties validated result)
  evaluated <- case [item | item <- proofResultRules result,
    proofRuleId item == tokenText (ruleId selectedRule)] of
    [item] -> Right item
    _ -> at "SFE014" path (ruleId selectedRule) "selected technical result missing"
  authoredException <- sharedExceptionTree path shared
  let supplied = Map.fromList [(tokenText item,proofText proof)
        | (item,proof) <- assignments]
      technical = traceValues evaluated
      exceptionResult = case [item | item <- proofResultRules result,
        proofRuleId item == tokenText (attachmentRuleId instanceId)] of
        [item] -> Just item
        _ -> Nothing
      exceptionTechnical = maybe Map.empty traceValues exceptionResult
      scopedStatus = maybe "not_evaluated" (satisfactionText . proofRuleStatus) exceptionResult
      currentIsAbetment = tokenText target == tokenText (ruleIdentifier route)
      treeId node = case node of
        ResolvedLeaf item _ -> tokenText item
        ResolvedGroup item _ _ -> tokenText item
      routeLines = case selectedTree of
        ResolvedGroup _ All [ResolvedGroup overall Any routeTrees, consequence]
          | currentIsAbetment ->
            ["Penal Code s 107 route classifications:"]
            ++ concat [ ["  " <> treeId node <> ": " <>
                Map.findWithDefault "not_evaluated" (treeId node) technical]
               ++ renderTree 2 supplied technical node | node <- routeTrees]
            ++ ["Overall technical s 107 status: " <>
                Map.findWithDefault "not_evaluated" (tokenText overall) technical
               ,"Separate s 109 candidate consequence:"]
            ++ renderTree 1 supplied technical consequence
            ++ ["Technical s 109 candidate status: " <>
                Map.findWithDefault "not_evaluated" (treeId selectedTree) technical]
        _ -> "Selected technical requirements:" : renderTree 1 supplied technical selectedTree
      otherLine item = let other = attachmentInstanceId item
        in "  " <> tokenText other <> " — " <>
          (if tokenText other `elem` map tokenText observed
           then "observed, but not_evaluated for this branch"
           else "not_evaluated")
      BurdenAnnotation annotation holder burdenKind standard = modelBurden model
      ActorExceptionDefinition _ sharedRule = shared
      stageLines = case stages of
        [ConductStageAssignment _ _ (PreparationOnly _)] ->
          ["Conduct stage: preparation_only — externally classified"]
        [ConductStageAssignment _ _ (ActTowardsCommission _)] ->
          ["Conduct stage: act_towards_commission — externally classified"]
        [ConductStageAssignment _ _ (StageUnresolved _ why)] ->
          ["Conduct stage: unresolved(" <> tokenText why <> ") — externally classified"]
        _ -> []
      output =
        ["Model: " <> tokenText (modelIdentifier model)
        ,"Jurisdiction: Singapore — research POC; synthetic classifications only"
        ,"Analysis target: " <> tokenText target
        ,"Principal actor: " <> actor "role:principal"
        ,"Alleged-abettor actor: " <> actor "role:alleged-abettor"
        ,"Co-conspirator actor: " <> actor "role:co-conspirator"
        ,"Alleged-attempter actor: " <> actor "role:alleged-attempter"
        ,"Target thing: " <> tokenText (ruleIdentifier offence)
          <> " — Penal Code ss " <> sectionList (ruleSections offence)]
        ++ stageLines ++ routeLines
        ++ ["General exception instance: " <> tokenText instanceId
           ,"Definition: " <> tokenText (ruleIdentifier sharedRule)
             <> " — Penal Code s 84; shared structure, independent classifications"
           ,"Subject actor: " <> actor (tokenText (attachmentSubjectRole attachment))
           ,"Act context: " <> tokenText (actContextToken (attachmentContext attachment))
           ,"Section 84 routes:"]
        ++ renderScopedTree 1 supplied exceptionTechnical authoredException scopedTree
        ++ ["Selected section 84 status: " <> scopedStatus
           ,"Other actor instances:"]
        ++ [otherLine item | item <- attachments,
          tokenText (attachmentInstanceId item) /= tokenText instanceId]
        ++ ["Typed statutory references:"]
        ++ ["  " <> tokenText label <> ": " <> instrumentText instrument
            <> " s " <> tokenText section
           | AuthorityReference label instrument _ section <- citations]
        ++ ["Evidence Act s 107 context: " <> tokenText annotation <> "; "
            <> tokenText holder <> " " <> tokenText burdenKind <> " burden; "
            <> tokenText standard <> ". It does not classify evidence."
           ,"Scope assumptions: acknowledged by scenario, not inferred or proved"]
        ++ ["  " <> tokenText item | ScopeAcknowledgement item <- acknowledgements]
        ++ ["Final technical participation status: " <>
          satisfactionText (proofResultStatus result)
           ,"No guilt, conviction, acquittal, liability, punishment or sentence was determined."]
  Right (Text.unlines output)
  where
    kernel result = either (const (at "SFE014" path (modelIdentifier model)
      "Haskell kernel rejected the compiled research model")) Right result

traceValues :: ProofRule -> Map Text Text
traceValues item = Map.fromList
  [(proofTraceId trace, satisfactionText (proofTraceStatus trace))
  | trace <- proofRuleTrace item]

renderScopedTree :: Int -> Map Text Text -> Map Text Text
  -> Resolved -> Resolved -> [Text]
renderScopedTree depth supplied evaluated authored scoped = case (authored,scoped) of
  (ResolvedLeaf original _,ResolvedLeaf instantiated _) ->
    [indent <> tokenText original <> " [" <> tokenText instantiated <> "] — supplied "
      <> Map.findWithDefault "missing" (tokenText instantiated) supplied
      <> "; technical " <> Map.findWithDefault "not_evaluated"
        (tokenText instantiated) evaluated]
  (ResolvedGroup original combinator children,
    ResolvedGroup instantiated _ scopedChildren) ->
    (indent <> tokenText original <> " [" <> tokenText instantiated <> "] — "
      <> combinatorText combinator <> "; technical "
      <> Map.findWithDefault "not_evaluated" (tokenText instantiated) evaluated)
      : concat (zipWith (renderScopedTree (depth + 1) supplied evaluated)
        children scopedChildren)
  _ -> [indent <> "invalid scoped exception tree"]
  where indent = Text.replicate depth "  "

renderTree :: Int -> Map Text Text -> Map Text Text -> Resolved -> [Text]
renderTree depth supplied evaluated node = case node of
  ResolvedLeaf item _ ->
    [indent <> tokenText item <> " — supplied "
      <> Map.findWithDefault "missing" (tokenText item) supplied
      <> "; technical " <> Map.findWithDefault "not_evaluated" (tokenText item) evaluated]
  ResolvedGroup item combinator members ->
    (indent <> tokenText item <> " — " <> combinatorText combinator <> "; technical "
      <> Map.findWithDefault "not_evaluated" (tokenText item) evaluated)
      : concatMap (renderTree (depth + 1) supplied evaluated) members
  where indent = Text.replicate depth "  "

combinatorText :: Combinator -> Text
combinatorText All = "all"
combinatorText Any = "any"

proofText :: Proof -> Text
proofText Proved = "proved"
proofText NotProved = "not_proved"
proofText (Unresolved reason) = "unresolved(" <> reason <> ")"

reasonText :: ProofReason -> Text
reasonText ProofSatisfied = "candidate requirements technically satisfied; no section 84 defeat"
reasonText ProofRequirementsNotSatisfied = "candidate requirements not technically satisfied"
reasonText ProofRequirementsUnresolved = "candidate requirements unresolved"
reasonText ProofDefeated = "candidate branch technically defeated by section 84"
reasonText ProofExceptionUnresolved = "section 84 guard unresolved"

sectionList :: [StatutorySection] -> Text
sectionList sections = Text.intercalate ", "
  [tokenText item | StatutorySection item <- sections]

instrumentText :: StatutoryInstrument -> Text
instrumentText PenalCode1871 = "Penal Code 1871"
instrumentText EvidenceAct1893 = "Evidence Act 1893"
