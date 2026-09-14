{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.CaseFacts
  ( ResolvedCaseFact(..), validateCaseFacts, checkSharedShapes, expandCaseFacts
  , caseFactsValue, caseFactsExplanation ) where

import Control.Monad (foldM, unless)
import Data.List (sortOn)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Protocol.Json (J(..))
import Yuho.Surface.AST
import Yuho.Surface.Abetment (abetmentAttributions, abetmentRelations)
import Yuho.Surface.ActorExceptions (actContextToken)
import Yuho.Surface.Token

data ResolvedCaseFact = ResolvedCaseFact CaseFact [(Token,CaseInputTarget)]
  deriving (Eq, Show)

data InputDescriptor = InputDescriptor CaseInputTarget CaseFactKind
  CaseFactSubject (Maybe Token) InputShape

data InputShape = ElementInputShape Category Text | RelationInputShape Text
  deriving (Eq, Show)

factToken :: CaseFact -> Token
factToken (CaseFact (CaseFactId item) _ _ _) = item

factIdText :: CaseFact -> Text
factIdText = tokenText . factToken

targetToken :: CaseInputTarget -> Token
targetToken (CasePrimitiveInput item) = item
targetToken (CaseRelationInput item) = item
targetToken (CaseExceptionInput _ item) = item

targetText :: CaseInputTarget -> Text
targetText (CasePrimitiveInput item) = tokenText item
targetText (CaseRelationInput item) = tokenText item
targetText (CaseExceptionInput instanceId item) =
  tokenText instanceId <> "/" <> tokenText item

targetValue :: CaseInputTarget -> J
targetValue (CasePrimitiveInput item) = JObj
  [("kind",JStr "primitive"),("id",JStr (tokenText item))]
targetValue (CaseRelationInput item) = JObj
  [("kind",JStr "relation"),("id",JStr (tokenText item))]
targetValue (CaseExceptionInput instanceId item) = JObj
  [("kind",JStr "exception-input"),("id",JStr (tokenText item)),
   ("instance",JStr (tokenText instanceId))]

factKindText :: CaseFactKind -> Text
factKindText FactConduct = "conduct"
factKindText FactCircumstance = "circumstance"
factKindText FactMentalState = "mental-state"
factKindText FactRelationship = "relationship"

subjectText :: CaseFactSubject -> Text
subjectText (CaseActorSubject actor target) = tokenText actor <>
  maybe "" (" / " <>) (tokenText <$> target)
subjectText (CaseRelationSubject source destination target) =
  tokenText source <> " -> " <> tokenText destination <> " / " <> tokenText target
subjectText (CaseExceptionSubject actor instanceId context) =
  tokenText actor <> " / " <> tokenText instanceId <> " / "
    <> tokenText (actContextToken context)

subjectValue :: CaseFactSubject -> J
subjectValue (CaseActorSubject actor target) = JObj
  ([("kind",JStr "actor"),("actor",JStr (tokenText actor))] ++
    maybe [] (\item -> [("target",JStr (tokenText item))]) target)
subjectValue (CaseRelationSubject source destination target) = JObj
  [("kind",JStr "relationship"),("from",JStr (tokenText source)),
   ("to",JStr (tokenText destination)),("target",JStr (tokenText target))]
subjectValue (CaseExceptionSubject actor instanceId context) = JObj
  [("kind",JStr "exception-instance"),("actor",JStr (tokenText actor)),
   ("instance",JStr (tokenText instanceId)),
   ("act_context",JStr (tokenText (actContextToken context)))]

classification :: CaseFact -> (Token,Maybe Token,Token)
classification (CaseFact _ _ _ (CaseFactClassification status code reason)) =
  (status,code,reason)

validateCaseFacts :: FilePath -> [ActorBinding] -> [CaseFact]
  -> [CaseAllegation] -> Either Diagnostic [ResolvedCaseFact]
validateCaseFacts path actors facts allegations = do
  _ <- foldM uniqueFact Map.empty facts
  let actorIds = Set.fromList [tokenText actor | ActorBinding _ actor <- actors]
  mapM_ (checkFact actorIds) facts
  let actualUses = [(factId,item,target)
        | CaseAllegation item _ _ _ _ bindings <- allegations,
          CaseFactBinding (CaseFactId factId) target <- bindings]
      declared = Set.fromList (map factIdText facts)
      issueOrder = Map.fromList [(tokenText item,index)
        | (index,CaseAllegation item _ _ _ _ _) <- zip [0 :: Int ..] allegations]
  case [factId | (factId,_,_) <- actualUses,
    Set.notMember (tokenText factId) declared] of
    item:_ -> at "SFE110" path item "unknown supplied case fact"
    [] -> pure ()
  case [factToken fact | fact <- facts,
    not (any (\(item,_,_) -> tokenText item == factIdText fact) actualUses)] of
    item:_ -> at "SFE116" path item "supplied case fact is never bound"
    [] -> pure ()
  pure [ResolvedCaseFact fact (sortOn (\(item,target) ->
      (Map.lookup (tokenText item) issueOrder,targetText target))
      [(item,target) | (used,item,target) <- actualUses,
        tokenText used == factIdText fact])
    | fact <- sortOn factIdText facts]
  where
    uniqueFact seen fact = let item = factToken fact in
      if not ("fact:" `Text.isPrefixOf` tokenText item) then
        at "SFE111" path item "typed case fact ID required"
      else case Map.lookup (tokenText item) seen of
        Just earlier -> atRelated "SFE111" path item "duplicate supplied case fact"
          path earlier
        Nothing -> pure (Map.insert (tokenText item) item seen)
    checkFact actorIds fact@(CaseFact _ kind subject _) = do
      let (status,code,reason) = classification fact
      if tokenKind reason == StringToken && not (Text.null (tokenText reason))
        then pure () else at "SFE111" path reason "case fact needs a supplied reason"
      case tokenText status of
        "proved" | code == Nothing -> pure ()
        "not_proved" | code == Nothing -> pure ()
        "unresolved" | maybe False ((`elem`
          ["not_determined","external_decision_pending"]) . tokenText) code -> pure ()
        _ -> at "SFE010" path status "invalid supplied proof classification"
      let participants = case subject of
            CaseActorSubject actor _ -> [actor]
            CaseRelationSubject source destination _ -> [source,destination]
            CaseExceptionSubject actor _ _ -> [actor]
      case [actor | actor <- participants,
        Set.notMember (tokenText actor) actorIds] of
        actor:_ -> at "SFE113" path actor "case fact subject is not a bound actor"
        [] -> pure ()
      case (kind,subject) of
        (_,CaseActorSubject _ (Just target))
          | not ("o:" `Text.isPrefixOf` tokenText target) ->
              at "SFE112" path target "case fact target must be a typed offence"
        (FactRelationship,CaseRelationSubject _ _ target)
          | "o:" `Text.isPrefixOf` tokenText target -> pure ()
        (FactRelationship,_) -> at "SFE112" path (factToken fact)
          "relationship fact needs typed endpoints and target offence"
        (_,CaseRelationSubject _ _ _) -> at "SFE112" path (factToken fact)
          "relation subject requires relationship kind"
        _ -> pure ()

checkSharedShapes :: FilePath -> Model -> [ActorBinding] -> [CaseAllegation]
  -> [ResolvedCaseFact] -> Either Diagnostic ()
checkSharedShapes path model actors allegations facts = mapM_ checkFact facts
  where
    checkFact (ResolvedCaseFact _ []) = pure ()
    checkFact (ResolvedCaseFact _ uses) = do
      descriptions <- mapM lookupInput uses
      case descriptions of
        [] -> pure ()
        (firstToken,firstShape):rest -> mapM_ (\(item,shape) ->
          unless (shape == firstShape) $
            atRelated "SFE117" path item
              "one case fact cannot bind incompatible primitive meanings"
              path firstToken) rest
    lookupInput (allegationId,target) = do
      CaseAllegation _ kind _ _ raw _ <-
        case [item | item@(CaseAllegation declared _ _ _ _ _) <- allegations,
          tokenText declared == tokenText allegationId] of
          [item] -> pure item
          _ -> at "SFE114" path allegationId "unknown allegation for case fact"
      descriptions <- inputDescriptors path model actors kind raw
      case [shape | InputDescriptor candidate _ _ _ shape <- descriptions,
        targetText candidate == targetText target] of
        [shape] -> pure (targetToken target,shape)
        _ -> at "SFE114" path (targetToken target)
          "input is unknown, derived, unselected or outside the proof-status domain"

-- Only leaves of the selected branch and active exception instances are bindable.
expandCaseFacts :: FilePath -> Model -> [ActorBinding] -> [CaseFact]
  -> CaseAllegation -> Either Diagnostic Scenario
expandCaseFacts path model actors facts
  (CaseAllegation allegationId kind _ _ raw bindings) = do
  descriptors <- inputDescriptors path model actors kind raw
  let indexed = Map.fromList [(targetText target,descriptor)
        | descriptor@(InputDescriptor target _ _ _ _) <- descriptors]
      declared = Map.fromList [(factIdText fact,fact) | fact <- facts]
  _ <- foldM uniqueBinding Map.empty bindings
  foldM (insertBinding indexed declared) raw bindings
  where
    uniqueBinding seen (CaseFactBinding _ target) =
      let item = targetToken target in case Map.lookup (targetText target) seen of
        Just first -> atRelated "SFE115" path item
          "duplicate fact binding to one allegation input" path first
        Nothing -> pure (Map.insert (targetText target) item seen)
    insertBinding indexed declared scenario binding@(CaseFactBinding (CaseFactId factId) target) = do
      fact <- case Map.lookup (tokenText factId) declared of
        Just value -> pure value
        Nothing -> at "SFE110" path factId "unknown supplied case fact"
      InputDescriptor _ expectedKind expectedSubject relationProxy _ <-
        case Map.lookup (targetText target) indexed of
          Just value -> pure value
          Nothing -> at "SFE114" path (targetToken target)
            "input is unknown, derived, unselected or outside the proof-status domain"
      let CaseFact _ actualKind actualSubject _ = fact
          (status,code,_) = classification fact
      unless (actualKind == expectedKind) $
        at "SFE112" path factId "case fact kind does not match primitive input"
      unless (sameSubject actualSubject expectedSubject) $
        at "SFE113" path factId
          "case fact actor, relation, target, instance or act context does not match input"
      addAssignment path allegationId binding expectedSubject relationProxy
        status code scenario

sameSubject :: CaseFactSubject -> CaseFactSubject -> Bool
sameSubject (CaseActorSubject a target) (CaseActorSubject b expected) =
  tokenText a == tokenText b && fmap tokenText target == fmap tokenText expected
sameSubject (CaseRelationSubject a b c) (CaseRelationSubject x y z) =
  map tokenText [a,b,c] == map tokenText [x,y,z]
sameSubject (CaseExceptionSubject a b c) (CaseExceptionSubject x y z) =
  tokenText a == tokenText x && tokenText b == tokenText y
    && tokenText (actContextToken c) == tokenText (actContextToken z)
sameSubject _ _ = False

addAssignment :: FilePath -> Token -> CaseFactBinding -> CaseFactSubject
  -> Maybe Token -> Token -> Maybe Token -> Scenario -> Either Diagnostic Scenario
addAssignment path _ (CaseFactBinding _ target) subject relationProxy status code
  (ActorScopedScenario request model targets observations bindings actorRows
    relationRows stages completions scoped plain scopes) = do
  let conflict item = at "SFE115" path item
        "case fact binding conflicts with a direct classification"
  case target of
    CasePrimitiveInput item -> do
      if any (\(ActorAssignment key _ _ _) -> tokenText key == tokenText item) actorRows
        then conflict item else pure ()
      actor <- case subject of
        CaseActorSubject value _ -> pure value
        CaseRelationSubject _ _ _ -> case relationProxy of
          Just relation -> pure relation
          Nothing -> at "SFE114" path item "relation attribution unavailable"
        CaseExceptionSubject _ _ _ -> at "SFE114" path item
          "exception input needs its typed instance"
      pure (ActorScopedScenario request model targets observations bindings
        (ActorAssignment item actor status code : actorRows) relationRows
        stages completions scoped plain scopes)
    CaseRelationInput item -> do
      if any (\(RelationAssignment key _ _ _ _) -> tokenText key == tokenText item)
          relationRows then conflict item else pure ()
      case subject of
        CaseRelationSubject source destination _ ->
          pure (ActorScopedScenario request model targets observations bindings
            actorRows (RelationAssignment item source destination status code : relationRows)
            stages completions scoped plain scopes)
        _ -> at "SFE114" path item "relation endpoints unavailable"
    CaseExceptionInput instanceId item -> do
      if any (\row -> tokenText (scopedAssignmentInstance row) == tokenText instanceId
        && tokenText (scopedAssignmentFact row) == tokenText item) scoped
        then conflict item else pure ()
      case subject of
        CaseExceptionSubject actor _ context ->
          pure (ActorScopedScenario request model targets observations bindings
            actorRows relationRows stages completions
            (ScopedExceptionAssignment instanceId item actor context status code : scoped)
            plain scopes)
        _ -> at "SFE114" path item "exception subject unavailable"
addAssignment path item _ _ _ _ _ _ = at "SFE114" path item
  "case fact binding requires an actor-scoped allegation"

inputDescriptors :: FilePath -> Model -> [ActorBinding] -> CaseTargetKind
  -> Scenario -> Either Diagnostic [InputDescriptor]
inputDescriptors path model bindings kind raw = case modelBody model of
  AbetmentLegal _ _ _ _ offence abetment attempt
    (ActorExceptionDefinition _ exception) attachments _ _ -> do
      let actors = Map.fromList [(tokenText role,actor) | ActorBinding role actor <- bindings]
          selectedKind = case kind of
            CaseOffence -> CandidateOffenceTarget (ruleIdentifier offence)
            CaseParticipation -> ParticipationAttachmentTarget
              (ruleIdentifier (abetmentRule abetment))
            CaseAttempt -> AttemptAttachmentTarget (ruleIdentifier (attemptRule attempt))
          sameTarget (CandidateOffenceTarget x) (CandidateOffenceTarget y) =
            tokenText x == tokenText y
          sameTarget (ParticipationAttachmentTarget x)
            (ParticipationAttachmentTarget y) = tokenText x == tokenText y
          sameTarget (AttemptAttachmentTarget x) (AttemptAttachmentTarget y) =
            tokenText x == tokenText y
          sameTarget _ _ = False
          activeIds = case raw of
            ActorScopedScenario _ _ _ observations _ _ _ _ _ _ _ _ -> observations
            _ -> []
          active = [item | item <- attachments,
            sameTarget (attachmentTargetKind item) selectedKind
              || tokenText (attachmentInstanceId item) `elem` map tokenText activeIds]
      mainRows <- case kind of
        CaseOffence -> mapM (actorElement actors "role:principal")
          (ruleElements offence)
        CaseParticipation -> do
          let relationIds = Set.fromList (map (tokenText . relationStatusId)
                (abetmentRelations abetment))
          elements <- mapM (participationElement actors abetment)
            [item | item <- ruleElements (abetmentRule abetment),
              Set.notMember (tokenText (elementId item)) relationIds]
          relations <- mapM (relationDescriptor actors)
            (abetmentRelations abetment)
          pure (elements ++ relations)
        CaseAttempt -> mapM (attemptElement actors (attemptTarget attempt))
          [item | item <- ruleElements (attemptRule attempt),
            elementCategory item /= SubstantialStep]
      exceptionRows <- fmap concat $ mapM (\attachment -> do
        actor <- actorFor actors (attachmentSubjectRole attachment)
        pure [InputDescriptor (CaseExceptionInput (attachmentInstanceId attachment)
          (elementId element)) (elementFactKind (elementCategory element))
          (CaseExceptionSubject actor (attachmentInstanceId attachment)
            (attachmentContext attachment)) Nothing
          (elementShape element) | element <- ruleElements exception]) active
      pure (mainRows ++ exceptionRows)
  _ -> at "SFE106" path (modelIdentifier model)
    "case facts require the bounded typed multi-allegation model"
  where
    actorFor actors role = case Map.lookup (tokenText role) actors of
      Just actor -> pure actor
      Nothing -> at "SFE113" path role "unbound case fact role"
    actorElement actors roleName item = do
      actor <- case Map.lookup roleName actors of
        Just value -> pure value
        Nothing -> at "SFE113" path (elementId item) "unbound input role"
      pure (InputDescriptor (CasePrimitiveInput (elementId item))
        (elementFactKind (elementCategory item))
        (CaseActorSubject actor Nothing) Nothing (elementShape item))
    attemptElement actors (AttemptTarget target) item = do
      actor <- case Map.lookup "role:alleged-attempter" actors of
        Just value -> pure value
        Nothing -> at "SFE113" path (elementId item) "unbound attempt role"
      pure (InputDescriptor (CasePrimitiveInput (elementId item))
        (elementFactKind (elementCategory item))
        (CaseActorSubject actor (Just target)) Nothing (elementShape item))
    participationElement actors abetment item = do
      let row = [(mental,endpoint) | (key,mental,endpoint) <-
            abetmentAttributions abetment (abetmentActor abetment),
            tokenText key == tokenText (elementId item)]
      case row of
        [(_,RoleEndpoint role)] -> do
          actor <- actorFor actors role
          pure (InputDescriptor (CasePrimitiveInput (elementId item))
            (elementFactKind (elementCategory item))
            (CaseActorSubject actor Nothing) Nothing (elementShape item))
        [(_,RelationEndpoint relationId)] -> do
          relation <- findRelation abetment relationId
          subject <- relationSubject actors relation
          pure (InputDescriptor (CasePrimitiveInput (elementId item))
            FactRelationship subject (Just relationId) (elementShape item))
        _ -> at "SFE114" path (elementId item) "missing typed input attribution"
    findRelation abetment relationId = case [item | item <- abetmentRelations abetment,
      tokenText (relationIdentifier item) == tokenText relationId] of
      [item] -> pure item
      _ -> at "SFE114" path relationId "unknown typed relation"
    relationSubject actors relation = do
      source <- endpointActor actors (relationFrom relation)
      destination <- endpointActor actors (relationTo relation)
      let ParticipationTarget target = relationTarget relation
      pure (CaseRelationSubject source destination target)
    endpointActor actors (RoleEndpoint role) = actorFor actors role
    endpointActor _ (RelationEndpoint item) = at "SFE114" path item
      "relation endpoint requires an actor role"
    relationDescriptor actors relation = do
      subject <- relationSubject actors relation
      pure (InputDescriptor (CaseRelationInput (relationIdentifier relation))
        FactRelationship subject Nothing
        (RelationInputShape (tokenText (relationQuote relation))))

elementShape :: Element -> InputShape
elementShape item = ElementInputShape (elementCategory item)
  (tokenText (elementQuote item))

elementFactKind :: Category -> CaseFactKind
elementFactKind category = case category of
  Conduct -> FactConduct
  Movement -> FactConduct
  MovementForTaking -> FactConduct
  AidAct -> FactConduct
  IllegalOmission -> FactConduct
  PursuantAct -> FactConduct
  PursuantIllegalOmission -> FactConduct
  Fault -> FactMentalState
  Purpose -> FactMentalState
  Intention -> FactMentalState
  Knowledge -> FactMentalState
  DishonestIntention -> FactMentalState
  _ -> FactCircumstance

caseFactsValue :: [ResolvedCaseFact] -> J
caseFactsValue facts = JArr (map row facts)
  where
    row (ResolvedCaseFact fact@(CaseFact _ kind subject _) uses) =
      let (status,code,reason) = classification fact in JObj
        ([ ("id",JStr (factIdText fact)),("kind",JStr (factKindText kind))
         ,("subject",subjectValue subject),("status",JStr (tokenText status))
         ,("reason",JStr (tokenText reason)),("bindings",JArr
           [JObj [("allegation",JStr (tokenText allegation)),
             ("input",targetValue target)] | (allegation,target) <- uses])]
          ++ maybe [] (\item -> [("unresolved_reason",JStr (tokenText item))]) code)

caseFactsExplanation :: [ResolvedCaseFact] -> Text
caseFactsExplanation [] = ""
caseFactsExplanation facts = Text.unlines
  ("Supplied case facts" : concatMap render facts ++
    ["Yuho did not assess evidence or determine these facts."])
  where
    render (ResolvedCaseFact fact@(CaseFact _ kind subject _) uses) =
      let (status,_,reason) = classification fact in
      ["",factIdText fact,"Kind: " <> factKindText kind,
       "Subject: " <> subjectText subject,
       "Supplied status: " <> tokenText status,
       "Reason: " <> tokenText reason,"Bound inputs:"] ++
      ["- " <> tokenText allegation <> " / " <> targetText target
        | (allegation,target) <- uses] ++ [""]
