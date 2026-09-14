{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Resolve (resolveTree) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Token

resolveTree :: FilePath -> [Proposition] -> Token -> Either Diagnostic Resolved
resolveTree path declarations root = do
  indexed <- index Map.empty declarations
  if not ("g:" `Text.isPrefixOf` tokenText root)
    then at "SFE006" path root "root must be an executable group"
    else pure ()
  (tree, visited) <- visit indexed Set.empty Set.empty root
  if visited /= Map.keysSet indexed
    then at "SFE006" path root "every declaration must appear in one source-ordered tree"
    else pure tree
  where
    index seen [] = Right seen
    index seen (item:rest) =
      let key = tokenText (identifier item)
      in if Map.member key seen
         then at "SFE002" path (identifier item) "duplicate proposition ID"
         else index (Map.insert key item seen) rest
    visit indexed active visited token = do
      let key = tokenText token
      if Set.member key active then at "SFE008" path token "cyclic proposition reference"
      else if Set.member key visited then at "SFE006" path token "proposition used more than once"
      else case Map.lookup key indexed of
        Nothing
          | "ann:" `Text.isPrefixOf` key || key == "section107" ->
              at "SFE012" path token "contextual annotation is not executable"
          | not ("f:" `Text.isPrefixOf` key || "g:" `Text.isPrefixOf` key) ->
              at "SFE006" path token "incompatible proposition type"
          | otherwise -> at "SFE003" path token "unknown proposition reference"
        Just (Leaf _ _ quote _) ->
          if "f:" `Text.isPrefixOf` key
          then Right (ResolvedLeaf token quote, Set.insert key visited)
          else at "SFE005" path token "leaf requires fact identifier"
        Just (Group _ combinator members) -> do
          if "g:" `Text.isPrefixOf` key && length members >= 2
          then pure () else at "SFE006" path token "invalid combinator or operands"
          (children, allVisited) <- foldMembers indexed (Set.insert key active)
            (Set.insert key visited) members []
          Right (ResolvedGroup token combinator children, allVisited)
    foldMembers _ _ visited [] reversed = Right (reverse reversed, visited)
    foldMembers indexed active visited (member:rest) reversed = do
      (child, next) <- visit indexed active visited member
      foldMembers indexed active next rest (child:reversed)
