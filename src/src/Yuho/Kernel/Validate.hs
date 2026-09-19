{-# LANGUAGE OverloadedStrings #-}
module Yuho.Kernel.Validate (validateInput) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Kernel.Evaluate (branches)

validateInput :: KernelInput -> Either Diagnostic ()
validateInput (Validate _ _ _ _) = Right ()
validateInput (Evaluate _ root facts _ maxNodes) = do
  let nodes = allNodes root
  if length nodes > maxNodes
    then Left (diagnostic "KINV004" "validate" "/program" (Just (provisionSpan root)) [])
    else pure ()
  _ <- foldM checkNode Set.empty nodes
  let leaves = [(requirementId item, requirementSpan item) | Right item <- nodes,
                requirementKind item == Leaf]
      referenced = Set.fromList (map fst leaves)
  mapM_ (\(identifier, sourceSpan) ->
    if Map.member identifier facts then Right ()
    else Left (diagnostic "KINV001" "validate" ("/facts/" <> identifier)
               (Just sourceSpan) [("id", identifier)])) leaves
  case Set.toList (Map.keysSet facts `Set.difference` referenced) of
    extra : _ -> Left (diagnostic "KINV004" "validate" ("/facts/" <> extra) Nothing [])
    [] -> pure ()
  if null (branches root []) && not (hasDefinition root)
    then Left (diagnostic "KINV004" "validate" "/program/definitions"
               (Just (provisionSpan root)) [])
    else pure ()
  where
    checkNode :: Set Text -> Either Provision Requirement -> Either Diagnostic (Set Text)
    checkNode seen node = case node of
      Left provision -> checkId seen (provisionId provision)
        (provisionPointer provision <> "/id") (provisionSpan provision)
      Right requirement -> checkId seen (requirementId requirement)
        (requirementPointer requirement <> "/id") (requirementSpan requirement)
    checkId seen identifier pointer sourceSpan
      | Set.member identifier seen = Left (diagnostic "KINV002" "validate" pointer
          (Just sourceSpan) [("id", identifier)])
      | otherwise = Right (Set.insert identifier seen)

allNodes :: Provision -> [Either Provision Requirement]
allNodes provision = Left provision :
  concatMap reqNodes (provisionRequirements provision)
  ++ concatMap allNodes (provisionChildren provision)
  where
    reqNodes requirement = Right requirement : concatMap reqNodes (requirementMembers requirement)

hasDefinition :: Provision -> Bool
hasDefinition provision = provisionDefinitions provision || any hasDefinition (provisionChildren provision)
