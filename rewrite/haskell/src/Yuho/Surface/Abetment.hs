{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Abetment
  ( checkAbetment, abetmentRelations, abetmentRouteRoots
  , abetmentAttributions ) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Resolve (resolveTree)
import Yuho.Surface.Token

abetmentRelations :: Abetment -> [ParticipationRelation]
abetmentRelations abetment = map relation (abetmentRoutes abetment)
  ++ [abetmentConsequenceRelation abetment]
  where
    relation (InstigationRoute _ item) = item
    relation (ConspiracyRoute _ _ item _ _ _ _) = item
    relation (AidRoute _ item _ _ _) = item

abetmentAttributions :: Abetment -> Token
  -> [(Token, Bool, RelationEndpoint)]
abetmentAttributions abetment abettor =
  concatMap routeRows (abetmentRoutes abetment)
    ++ [relationRow (abetmentConsequenceRelation abetment)]
  where
    relationRow relation = (relationStatusId relation,False,
      RelationEndpoint (relationIdentifier relation))
    factRow role item = (elementId item,elementCategory item == Intention,
      RoleEndpoint role)
    routeRows (InstigationRoute _ relation) = [relationRow relation]
    routeRows (ConspiracyRoute _ _ relation
      (PursuantConduct _ actor act omission) link _ _) =
        [relationRow relation,factRow actor act,factRow actor omission,
         (elementId link,False,RelationEndpoint (relationIdentifier relation))]
    routeRows (AidRoute _ relation elements _ _) =
      relationRow relation : map (factRow abettor) elements

abetmentRouteRoots :: Abetment -> [Token]
abetmentRouteRoots = map root . abetmentRoutes
  where
    root (InstigationRoute _ relation) = relationStatusId relation
    root (ConspiracyRoute _ _ _ _ _ _ (Group item _ _)) = item
    root (AidRoute _ _ _ _ (Group item _ _)) = item
    root _ = Token EndToken "" 1 1

checkAbetment :: FilePath -> Map.Map Text Token -> Token -> Token -> Token
  -> Rule -> Abetment -> Either Diagnostic Resolved
checkAbetment path quotes principal abettor co offence abetment = do
  let rule = abetmentRule abetment
      routes = abetmentRoutes abetment
      ids = map routeId routes
      sections = [tokenText item | StatutorySection item <- ruleSections rule]
      target = tokenText (ruleIdentifier offence)
  if ruleKind rule == ParticipationKind
      && fmap tokenText (ruleTarget rule) == Just target
      && tokenText (abetmentPrincipal abetment) == tokenText principal
      && tokenText (abetmentActor abetment) == tokenText abettor
      && sections == ["107","108","109"]
      then pure () else at "SFE100" path (ruleIdentifier rule)
        "bounded abetment requires typed actors, theft target and Penal Code ss 107–109"
  if length routes == 3 && Set.fromList (map routeKind routes) ==
      Set.fromList ["instigation","conspiracy","intentional-aid"]
      && Set.size (Set.fromList (map tokenText ids)) == 3
      && all (Text.isPrefixOf "route:" . tokenText) ids
      then pure () else at "SFE101" path (ruleIdentifier rule)
        "one distinct declaration of each closed s 107 route is required"
  mapM_ checkRoute routes
  mapM_ (\route -> case route of
    InstigationRoute _ relation -> checkRelation principal relation
    ConspiracyRoute _ _ relation _ _ _ _ -> checkRelation co relation
    AidRoute _ relation _ _ _ -> checkRelation principal relation) routes
  checkRelation principal (abetmentConsequenceRelation abetment)
  let relations = abetmentRelations abetment
  if Set.size (Set.fromList (map (tokenText . relationIdentifier) relations)) ==
      length relations then pure () else at "SFE002" path (ruleIdentifier rule)
        "duplicate typed relation identifier"
  let consequence = abetmentConsequence abetment
      consequenceRelation = abetmentConsequenceRelation abetment
      roots = map tokenText (abetmentRouteRoots abetment)
  if elementCategory consequence == Consequence
      && tokenText (elementId consequence) == tokenText (relationStatusId consequenceRelation)
      then pure () else at "SFE104" path (elementId consequence)
        "s 109 consequence requires its own typed supplied classification"
  case (abetmentOverall abetment, abetmentCandidate abetment) of
    (Group overall Any members,Group _ All [overallRef,consequenceRef])
      | map tokenText members == roots
        && tokenText overallRef == tokenText overall
        && tokenText consequenceRef == tokenText (elementId consequence) -> pure ()
    _ -> at "SFE104" path (ruleIdentifier rule)
      "s 107 any-route status and s 109 candidate consequence must remain separate"
  let leaves = [Leaf (elementId item) Nothing (elementQuote item) (elementSupport item)
        | item <- ruleElements rule]
  mapM_ (\item -> if Map.member (tokenText (elementQuote item)) quotes
    then pure () else at "SFE003" path (elementQuote item) "unknown source quote")
    (ruleElements rule)
  if Set.size (Set.fromList (map (tokenText . elementId) (ruleElements rule))) ==
      length (ruleElements rule) then pure () else
    at "SFE002" path (ruleIdentifier rule) "duplicate route fact or relation ID"
  case abetmentCandidate abetment of
    Group root _ _ -> resolveTree path (leaves ++ ruleGroups rule) root
    _ -> at "SFE007" path (ruleIdentifier rule) "s 109 candidate root required"
  where
    routeId (InstigationRoute item _) = item
    routeId (ConspiracyRoute item _ _ _ _ _ _) = item
    routeId (AidRoute item _ _ _ _) = item
    routeKind (InstigationRoute _ _) = "instigation" :: Text
    routeKind (ConspiracyRoute _ _ _ _ _ _ _) = "conspiracy"
    routeKind (AidRoute _ _ _ _ _) = "intentional-aid"
    checkRelation destination relation = do
      let endpoint value = case value of
            RoleEndpoint item -> tokenText item
            RelationEndpoint item -> tokenText item
          fromRole = endpoint (relationFrom relation)
          toRole = endpoint (relationTo relation)
      if fromRole == tokenText abettor && toRole == tokenText destination
          && (case relationTarget relation of
                ParticipationTarget item ->
                  tokenText item == tokenText (ruleIdentifier offence))
          && Text.isPrefixOf "rel:" (tokenText (relationIdentifier relation))
          && Text.isPrefixOf "f:" (tokenText (relationStatusId relation))
        then pure () else at "SFE102" path (relationIdentifier relation)
          "relation direction, target or status type is invalid"
    checkRoute route = case route of
      InstigationRoute _ _ -> pure ()
      ConspiracyRoute _ other _ (PursuantConduct conductId actor act omission)
        link form groupId -> do
          if tokenText other == tokenText co && tokenText actor == tokenText co
              && Text.isPrefixOf "conduct:" (tokenText conductId)
              && map elementCategory [act,omission,link] ==
                [PursuantAct,PursuantIllegalOmission,Causation]
              then pure () else at "SFE103" path conductId
                "conspiracy needs another participant and distinct pursuant conduct"
          case (form,groupId) of
            (Group formId Any [actRef,omissionRef],
             Group _ All [agreementRef,formRef,linkRef])
              | map tokenText [actRef,omissionRef] ==
                  map (tokenText . elementId) [act,omission]
                && tokenText formRef == tokenText formId
                && tokenText linkRef == tokenText (elementId link)
                && tokenText agreementRef == tokenText (relationStatusId
                  (conspiracyRelation route)) -> pure ()
            _ -> at "SFE103" path conductId
              "conspiracy requires agreement, pursuant act or omission, and in-order link"
      AidRoute _ relation elements form groupId -> do
        case (elements,form,groupId) of
          ([intention,act,omission],
           Group formId Any [actRef,omissionRef],
           Group _ All [intentionRef,relationRef,formRef])
            | map elementCategory elements == [Intention,AidAct,IllegalOmission]
              && map tokenText [actRef,omissionRef] ==
                map (tokenText . elementId) [act,omission]
              && tokenText intentionRef == tokenText (elementId intention)
              && tokenText relationRef == tokenText (relationStatusId relation)
              && tokenText formRef == tokenText formId -> pure ()
          _ -> at "SFE105" path (relationIdentifier relation)
            "intentional aid requires intention, directed link and act or illegal omission"
    conspiracyRelation (ConspiracyRoute _ _ relation _ _ _ _) = relation
    conspiracyRelation _ = abetmentConsequenceRelation abetment
