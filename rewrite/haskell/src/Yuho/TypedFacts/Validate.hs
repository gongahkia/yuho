{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Validate (ValidatedTyped, validateTyped, typedGraph, typedRequest) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Exception.Types
import Yuho.Exception.Validate (ValidatedGraph, validateGraph)
import Yuho.TypedFacts.Types

data ValidatedTyped = ValidatedTyped TypedRequest ValidatedGraph

typedGraph :: ValidatedTyped -> ValidatedGraph
typedGraph (ValidatedTyped _ graph) = graph

typedRequest :: ValidatedTyped -> TypedRequest
typedRequest (ValidatedTyped request _) = request

validateTyped :: TypedRequest -> Either Diagnostic ValidatedTyped
validateTyped request = do
  let raw = exceptionRawGraph (typedExceptionRequest request)
  graph <- validateGraph raw
  mapM_ (validateRule request raw) (rawRules raw)
  pure (ValidatedTyped request graph)

validateRule :: TypedRequest -> RawGraph -> RawRule -> Either Diagnostic ()
validateRule request raw rule = mapM_ check (leaves (rawRuleProgram rule))
  where
    check leaf = case Map.lookup (requirementId leaf) (typedBindings request) of
      Nothing -> Left (diagnostic "KINV001" "validate"
        ("/facts/" <> requirementId leaf) (Just (requirementSpan leaf)) [])
      Just binding -> case Map.lookup (requirementId leaf) (typedDeclarations request) of
        Nothing -> Right ()
        Just declaration -> do
          compareField "burden" burdenText (metadataBurden declaration)
            (metadataBurden (bindingMetadata binding)) leaf
          compareField "standard_of_proof" standardText (metadataStandard declaration)
            (metadataStandard (bindingMetadata binding)) leaf
    compareField :: Eq a => Text -> (a -> Text) -> Maybe a -> Maybe a
      -> Requirement -> Either Diagnostic ()
    compareField _ _ Nothing _ _ = Right ()
    compareField field showValue (Just expected) supplied leaf
      | supplied == Just expected = Right ()
      | otherwise = Left (diagnostic "KINV007" "validate"
          (requirementPointer leaf <> "/declared_metadata/" <> field)
          (Just (requirementSpan leaf))
          [("rule", rawRuleId rule), ("leaf", requirementId leaf), ("field", field)
          ,("expected", showValue expected)
          ,("supplied", maybe "absent" showValue supplied)
          ,("source_path", maybe "" sourcePath
              (lookup (rawRuleSource rule) (rawSources raw)))])

leaves :: Provision -> [Requirement]
leaves provision = concatMap requirementLeaves (provisionRequirements provision)
  ++ concatMap leaves (provisionChildren provision)
  where
    requirementLeaves requirement = case requirementKind requirement of
      Leaf -> [requirement]
      All -> concatMap requirementLeaves (requirementMembers requirement)
      Any -> concatMap requirementLeaves (requirementMembers requirement)
