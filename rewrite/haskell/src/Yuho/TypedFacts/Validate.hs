{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Validate (ValidatedTyped, validateTyped, typedGraph, typedRequest
  , validateBindingMetadata) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Exception.Types
import Yuho.Exception.Validate (ValidatedGraph, validateGraph)
import Yuho.TypedFacts.Types

data ValidatedTyped = ValidatedTyped TypedRequest (ValidatedGraph Bool)

typedGraph :: ValidatedTyped -> ValidatedGraph Bool
typedGraph (ValidatedTyped _ graph) = graph

typedRequest :: ValidatedTyped -> TypedRequest
typedRequest (ValidatedTyped request _) = request

validateTyped :: TypedRequest -> Either Diagnostic ValidatedTyped
validateTyped request = do
  let raw = exceptionRawGraph (typedExceptionRequest request)
  graph <- validateGraph raw
  validateBindingMetadata raw (typedDeclarations request)
    (typedBindings request) bindingMetadata
  pure (ValidatedTyped request graph)

validateBindingMetadata :: RawGraph a -> Map.Map Text Metadata -> Map.Map Text b
  -> (b -> Metadata) -> Either Diagnostic ()
validateBindingMetadata raw declarations bindings metadataOf =
  mapM_ validateRule (rawRules raw)
  where
    validateRule rule = mapM_ (check rule) (leaves (rawRuleProgram rule))
    check rule leaf = case Map.lookup (requirementId leaf) bindings of
      Nothing -> Left (diagnostic "KINV001" "validate"
        ("/facts/" <> requirementId leaf) (Just (requirementSpan leaf)) [])
      Just binding -> case Map.lookup (requirementId leaf) declarations of
        Nothing -> Right ()
        Just declaration -> do
          compareField "burden" burdenText (metadataBurden declaration)
            (metadataBurden (metadataOf binding)) leaf rule
          compareField "standard_of_proof" standardText (metadataStandard declaration)
            (metadataStandard (metadataOf binding)) leaf rule
    compareField :: Eq a => Text -> (a -> Text) -> Maybe a -> Maybe a
      -> Requirement -> RawRule -> Either Diagnostic ()
    compareField _ _ Nothing _ _ _ = Right ()
    compareField field showValue (Just expected) supplied leaf rule
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
