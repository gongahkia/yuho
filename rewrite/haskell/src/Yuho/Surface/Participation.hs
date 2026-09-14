{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Participation (resolveParticipationTree) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Token

resolveParticipationTree :: FilePath -> Resolved -> ParticipationRoute
  -> Either Diagnostic Resolved
resolveParticipationTree path offenceTree (IntentionalAidRoute route relation) = do
  root <- case reverse (ruleGroups route) of
    Group item _ _:_ -> Right item
    _ -> at "SFE007" path (ruleIdentifier route) "participation root required"
  let offenceId = resolvedId offenceTree
      relationLeaf = Leaf (relationStatusId relation) Nothing (relationQuote relation) Nothing
      local = [Leaf (elementId item) Nothing (elementQuote item) (elementSupport item)
        | item <- ruleElements route] ++ [relationLeaf] ++ ruleGroups route
  indexed <- index Map.empty local
  if Map.member (tokenText offenceId) indexed then
    at "SFE069" path offenceId "participation ID conflicts with target requirements"
    else pure ()
  (tree, visited) <- visit indexed offenceId Set.empty Set.empty root
  if visited == Set.insert (tokenText offenceId) (Map.keysSet indexed)
    then Right tree
    else at "SFE069" path root "participation declaration or target is unused"
  where
    resolvedId (ResolvedLeaf item _) = item
    resolvedId (ResolvedGroup item _ _) = item
    index seen [] = Right seen
    index seen (item:rest)
      | Map.member (tokenText (identifier item)) seen =
          at "SFE002" path (identifier item) "duplicate participation proposition"
      | otherwise = index (Map.insert (tokenText (identifier item)) item seen) rest
    visit indexed offenceId active seen item
      | Set.member key active = at "SFE008" path item "cyclic participation proposition"
      | Set.member key seen = at "SFE006" path item "participation proposition reused"
      | key == tokenText offenceId = Right (offenceTree, Set.insert key seen)
      | Just (Leaf declared _ quote _) <- Map.lookup key indexed =
          if "f:" `Text.isPrefixOf` key then
            Right (ResolvedLeaf declared quote, Set.insert key seen)
          else at "SFE069" path item "participation leaf requires f: identifier"
      | Just (Group declared combinator members) <- Map.lookup key indexed = do
          if "g:" `Text.isPrefixOf` key && not (null members) then pure () else
            at "SFE069" path item "invalid participation group"
          (children, allSeen) <- foldMembers indexed offenceId
            (Set.insert key active) (Set.insert key seen) members []
          Right (ResolvedGroup declared combinator children, allSeen)
      | "a:" `Text.isPrefixOf` key =
          at "SFE025" path item "scope assumption is not executable"
      | otherwise = at "SFE003" path item "unknown participation proposition"
      where key = tokenText item
    foldMembers _ _ _ seen [] reversed = Right (reverse reversed, seen)
    foldMembers indexed offenceId active seen (item:rest) reversed = do
      (child,next) <- visit indexed offenceId active seen item
      foldMembers indexed offenceId active next rest (child:reversed)
