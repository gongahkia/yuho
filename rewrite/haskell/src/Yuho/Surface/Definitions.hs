{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Definitions
  ( definitionIndex, resolveDefinition, resolveDefinitionRule, reachableDefinitions
  , definitionLeaves, definitionQuoteKeys ) where

import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Token

definitionIndex :: FilePath -> [StatutoryDefinition]
  -> Either Diagnostic (Map Text StatutoryDefinition)
definitionIndex path = go Map.empty
  where
    go seen [] = Right seen
    go seen (item:rest)
      | not ("d:" `Text.isPrefixOf` key) = at "SFE051" path (definitionId item)
          "statutory definition requires d: identifier"
      | Just prior <- Map.lookup key seen = atRelated "SFE050" path (definitionId item)
          "duplicate statutory definition" path (definitionId prior)
      | otherwise = go (Map.insert key item seen) rest
      where key = tokenText (definitionId item)

resolveDefinition :: FilePath -> Map Text StatutoryDefinition -> Token
  -> Either Diagnostic Resolved
resolveDefinition path definitions = resolveById path definitions Set.empty

resolveDefinitionRule :: FilePath -> Map Text StatutoryDefinition -> Rule
  -> Either Diagnostic Resolved
resolveDefinitionRule path definitions rule = do
  root <- case reverse (ruleGroups rule) of
    Group item _ _:_ -> Right item
    _ -> at "SFE007" path (ruleIdentifier rule) "candidate offence root missing"
  resolveLocal path definitions Set.empty (ruleIdentifier rule)
    (ruleElements rule) [] (ruleDefinitionReferences rule) (ruleGroups rule) root

resolveById :: FilePath -> Map Text StatutoryDefinition -> Set Text -> Token
  -> Either Diagnostic Resolved
resolveById path definitions active item = do
  definition <- case Map.lookup (tokenText item) definitions of
    Nothing -> at "SFE053" path item "unknown statutory definition"
    Just value -> Right value
  if Set.member (tokenText item) active then at "SFE054" path item
    "statutory-definition dependency cycle" else pure ()
  output <- case definitionOutputs definition of
    [DefinitionOutput value] -> Right value
    [] -> at "SFE055" path (definitionId definition) "definition output required"
    _:DefinitionOutput second:_ -> at "SFE055" path second "multiple definition outputs"
  let inputs = [value | DefinitionInput value <- definitionInputs definition]
      mental = [value | MentalStateInput value _ _ _ <- definitionMentalStates definition]
  tree <- resolveLocal path definitions (Set.insert (tokenText item) active)
    (definitionId definition) (inputs ++ mental) (definitionMentalStates definition)
    (definitionReferences definition) (definitionGroups definition) output
  pure (ResolvedGroup (definitionId definition) All [tree])

resolveLocal :: FilePath -> Map Text StatutoryDefinition -> Set Text -> Token
  -> [Element] -> [MentalStateInput] -> [DefinitionReference] -> [Proposition] -> Token
  -> Either Diagnostic Resolved
resolveLocal path definitions active owner elements mental references groups root = do
  let leafEntries = [(tokenText (elementId element), ResolvedLeaf (elementId element)
        (elementQuote element)) | element <- elements]
      groupEntries = [(tokenText item, (comb, members)) | Group item comb members <- groups]
      localIds = map fst leafEntries ++ map fst groupEntries
      refEntries = [(tokenText item, (item, declaredKind))
        | DefinitionReference item _ declaredKind <- references]
      refIds = map fst refEntries
      allIds = localIds ++ refIds
  if Set.size (Set.fromList allIds) /= length allIds then
    at "SFE002" path owner "duplicate local definition or proposition identifier"
    else pure ()
  let leaves = Map.fromList leafEntries
      groupMap = Map.fromList groupEntries
      refs = Map.fromList refEntries
  mapM_ (checkReference path definitions) references
  mapM_ (checkMental path definitions) mental
  if Map.member (tokenText root) groupMap then pure () else
    at "SFE055" path root "definition output must name its declared group"
  let private = Set.fromList [tokenText item | definition <- Map.elems definitions,
        tokenText (definitionId definition) /= tokenText owner,
        item <- map elementId [value | DefinitionInput value <- definitionInputs definition]
          ++ [elementId value | MentalStateInput value _ _ _ <- definitionMentalStates definition]
          ++ map identifier (definitionGroups definition)]
      walk visiting item
        | Set.member (tokenText item) visiting = at "SFE006" path item
            "proposition dependency cycle"
        | Just value <- Map.lookup (tokenText item) leaves = Right value
        | Just (comb,members) <- Map.lookup (tokenText item) groupMap = do
            if null members then at "SFE005" path item "empty proposition group" else pure ()
            children <- mapM (walk (Set.insert (tokenText item) visiting)) members
            pure (ResolvedGroup item comb children)
        | Just (_, declaredKind) <- Map.lookup (tokenText item) refs = do
            definition <- case Map.lookup (tokenText item) definitions of
              Nothing -> at "SFE053" path item "unknown statutory definition"
              Just value -> Right value
            if definitionKind definition /= declaredKind then at "SFE056" path item
              "definition reference type mismatch" else pure ()
            resolveById path definitions active item
        | Set.member (tokenText item) private = at "SFE058" path item
            "direct access to a definition's private proposition"
        | otherwise = at "SFE003" path item "unknown proposition or undeclared definition reference"
  tree <- walk Set.empty root
  let used = treeIds tree
      unused = Set.fromList allIds `Set.difference` used
  case Set.toAscList unused of
    item:_ -> at "SFE058" path (Token WordToken item (tokenLine owner) (tokenColumn owner))
      "declared input, proposition or definition reference is not reachable from output"
    [] -> Right tree

treeIds :: Resolved -> Set Text
treeIds (ResolvedLeaf item _) = Set.singleton (tokenText item)
treeIds (ResolvedGroup item _ members) =
  Set.insert (tokenText item) (Set.unions (map treeIds members))

checkReference :: FilePath -> Map Text StatutoryDefinition -> DefinitionReference
  -> Either Diagnostic ()
checkReference path definitions (DefinitionReference item _ declaredKind) =
  case Map.lookup (tokenText item) definitions of
    Nothing -> at "SFE053" path item "unknown statutory definition"
    Just definition | definitionKind definition /= declaredKind ->
      at "SFE056" path item "definition reference type mismatch"
    _ -> Right ()

checkMental :: FilePath -> Map Text StatutoryDefinition -> MentalStateInput
  -> Either Diagnostic ()
checkMental path definitions (MentalStateInput element mentalKind target declaredKind) = do
  definition <- case Map.lookup (tokenText target) definitions of
    Nothing -> at "SFE057" path target "unknown mental-state target definition"
    Just value -> Right value
  if definitionKind definition /= declaredKind then at "SFE057" path target
    "mental-state target type mismatch" else pure ()
  let allowed = case (mentalKind, declaredKind) of
        (MentalIntention, HurtResult) -> True
        (MentalKnowledge, HurtResult) -> True
        (MentalIntention, WrongfulGain) -> True
        (MentalIntention, WrongfulLoss) -> True
        _ -> False
  if allowed && elementCategory element == case mentalKind of
       MentalIntention -> Intention
       MentalKnowledge -> Knowledge
    then Right () else at "SFE057" path (elementId element)
      "invalid mental-state kind or target"

reachableDefinitions :: Map Text StatutoryDefinition -> Rule -> [StatutoryDefinition]
reachableDefinitions definitions rule = go Set.empty (map refId (ruleDefinitionReferences rule)) []
  where
    refId (DefinitionReference item _ _) = tokenText item
    go _ [] reversed = reverse reversed
    go seen (key:rest) reversed
      | Set.member key seen = go seen rest reversed
      | Just definition <- Map.lookup key definitions =
          go (Set.insert key seen)
            (map refId (definitionReferences definition) ++ rest) (definition:reversed)
      | otherwise = go seen rest reversed

definitionLeaves :: StatutoryDefinition -> [Element]
definitionLeaves definition =
  [item | DefinitionInput item <- definitionInputs definition]
  ++ [item | MentalStateInput item _ _ _ <- definitionMentalStates definition]

definitionQuoteKeys :: StatutoryDefinition -> [Token]
definitionQuoteKeys definition = concatMap
  (\element -> elementQuote element : maybe [] (:[]) (elementSupport element))
  (definitionLeaves definition)
