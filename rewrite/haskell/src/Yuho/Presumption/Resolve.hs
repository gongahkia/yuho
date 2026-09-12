{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Resolve
  ( resolveGraph, referencedLeaves ) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Presumption.Types

referencedLeaves :: Condition -> [Text]
referencedLeaves condition = case conditionKind condition of
  EffectiveLeaf identifier -> [identifier]
  ConditionAll children -> concatMap referencedLeaves children
  ConditionAny children -> concatMap referencedLeaves children

resolveGraph :: [Registration] -> Either Diagnostic (Map Text [Registration])
resolveGraph registrations = do
  let targets = unique (map registrationTarget registrations)
      byTarget = Map.fromList [(target, [item | item <- registrations
        , registrationTarget item == target]) | target <- targets]
      edges target = concatMap (\item -> referencedLeaves (registrationTrigger item)
        ++ referencedLeaves (registrationRebuttal item))
        (Map.findWithDefault [] target byTarget)
      visit active done leaf
        | Set.member leaf done = Right done
        | Set.member leaf active = Left (diagnostic "KINV006" "validate"
            "/presumptions" Nothing
            [("graph_kind", "effective_leaf"), ("cycle_leaf", leaf)])
        | otherwise = do
            visited <- foldM (visit (Set.insert leaf active)) done (edges leaf)
            pure (Set.insert leaf visited)
  _ <- foldM (visit Set.empty) Set.empty targets
  pure byTarget

unique :: Ord a => [a] -> [a]
unique = go Set.empty
  where
    go :: Ord a => Set a -> [a] -> [a]
    go _ [] = []
    go seen (item:rest)
      | Set.member item seen = go seen rest
      | otherwise = item : go (Set.insert item seen) rest
