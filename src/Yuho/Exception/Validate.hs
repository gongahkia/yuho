{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Validate
  ( ValidatedGraph, RuleKey, ResolvedRule, ResolvedException
  , validateGraph, rootKey, ruleKeyText, orderedKeys, ruleFor, ruleProgram, ruleSource
  , ruleExceptionsFor, exceptionDetails, exceptionTarget, sharedFacts, sharedDate
  , sharedMaxNodes
  ) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import Yuho.Core.Types
import Yuho.Exception.Types
import Yuho.Kernel.Evaluate (branches)

newtype RuleKey = RuleKey Text deriving (Eq, Ord, Show)

data ResolvedException = ResolvedException RawException RuleKey deriving (Eq, Show)
data ResolvedRule = ResolvedRule
  { resolvedRaw :: RawRule, resolvedBranches :: Map Text [ResolvedException]
  } deriving (Eq, Show)
data ValidatedGraph a = ValidatedGraph
  { graphRoot :: RuleKey, graphOrder :: [RuleKey]
  , graphRegistry :: Map RuleKey ResolvedRule, graphSharedFacts :: Map Text a
  , graphDate :: Day, graphMaxNodes :: Int
  } deriving (Eq, Show)

rootKey :: ValidatedGraph a -> RuleKey
rootKey = graphRoot

ruleKeyText :: RuleKey -> Text
ruleKeyText (RuleKey value) = value

orderedKeys :: ValidatedGraph a -> [RuleKey]
orderedKeys = graphOrder

ruleFor :: ValidatedGraph a -> RuleKey -> Maybe ResolvedRule
ruleFor graph key = Map.lookup key (graphRegistry graph)

ruleProgram :: ResolvedRule -> Provision
ruleProgram = rawRuleProgram . resolvedRaw

ruleSource :: ResolvedRule -> Text
ruleSource = rawRuleSource . resolvedRaw

ruleExceptionsFor :: ResolvedRule -> Text -> [ResolvedException]
ruleExceptionsFor rule identifier = Map.findWithDefault [] identifier (resolvedBranches rule)

exceptionDetails :: ResolvedException -> RawException
exceptionDetails (ResolvedException details _) = details

exceptionTarget :: ResolvedException -> RuleKey
exceptionTarget (ResolvedException _ target) = target

sharedFacts :: ValidatedGraph a -> Map Text a
sharedFacts = graphSharedFacts

sharedDate :: ValidatedGraph a -> Day
sharedDate = graphDate

sharedMaxNodes :: ValidatedGraph a -> Int
sharedMaxNodes = graphMaxNodes

validateGraph :: RawGraph a -> Either Diagnostic (ValidatedGraph a)
validateGraph raw = do
  let rules = rawRules raw
      identifiers = [(identifier, "/sources/id", Nothing) | (identifier, _) <- rawSources raw]
        ++ concatMap namedRuleNodes rules
      leaves = concatMap (leafNodes . rawRuleProgram) rules
      knownFacts = Set.fromList (map requirementId leaves)
  if null rules then failInvariant "/registry" "empty rule registry" else pure ()
  if length identifiers > rawMaxNodes raw then
    failInvariant "/registry" "semantic node limit exceeded" else pure ()
  _ <- foldM unique Set.empty identifiers
  mapM_ (\(identifier, _, _) ->
    if qualified identifier then pure () else failInvariant "/registry/id" "unqualified ID")
    (filter isRuleOrSource identifiers)
  root <- requireRule rules "/root_rule" (rawRoot raw)
  mapM_ (validateRule raw) rules
  mapM_ (\leaf -> if Map.member (requirementId leaf) (rawFacts raw) then pure () else
    Left (diagnostic "KINV001" "validate" ("/facts/" <> requirementId leaf)
      (Just (requirementSpan leaf)) [("id", requirementId leaf)])) leaves
  case Set.toList (Map.keysSet (rawFacts raw) `Set.difference` knownFacts) of
    extra : _ -> failInvariant ("/facts/" <> extra) "fact not referenced by registry"
    [] -> pure ()
  let resolved = [(RuleKey (rawRuleId rule), resolveRule rule) | rule <- rules]
      graph = ValidatedGraph (RuleKey (rawRuleId root)) (map fst resolved)
        (Map.fromList resolved) (rawFacts raw) (rawDate raw) (rawMaxNodes raw)
  validateAcyclic graph
  pure graph
  where
    isRuleOrSource (_, pointer, _) = pointer == "/sources/id" || Text.isSuffixOf "/rule_id" pointer
    resolveRule rule = ResolvedRule rule (Map.fromList
      [(provisionId branch, [ResolvedException ex (RuleKey (rawExceptionTarget ex))
         | ex <- rawRuleExceptions rule, rawExceptionBranch ex == provisionId branch])
      | (branch, _) <- branches (rawRuleProgram rule) []])

namedRuleNodes :: RawRule -> [(Text, Text, Maybe Span)]
namedRuleNodes rule =
  (rawRuleId rule, rawRulePointer rule <> "/rule_id", Nothing) :
  provisionNodes (rawRuleProgram rule) ++
  [(rawExceptionId ex, rawExceptionPointer ex <> "/id", Just (rawExceptionSpan ex))
   | ex <- rawRuleExceptions rule]

provisionNodes :: Provision -> [(Text, Text, Maybe Span)]
provisionNodes provision =
  (provisionId provision, provisionPointer provision <> "/id", Just (provisionSpan provision)) :
  concatMap requirementNodes (provisionRequirements provision) ++
  concatMap provisionNodes (provisionChildren provision)

requirementNodes :: Requirement -> [(Text, Text, Maybe Span)]
requirementNodes requirement =
  (requirementId requirement, requirementPointer requirement <> "/id", Just (requirementSpan requirement)) :
  concatMap requirementNodes (requirementMembers requirement)

leafNodes :: Provision -> [Requirement]
leafNodes provision =
  concatMap leaves (provisionRequirements provision) ++ concatMap leafNodes (provisionChildren provision)
  where
    leaves requirement = case requirementKind requirement of
      Leaf -> [requirement]
      All -> concatMap leaves (requirementMembers requirement)
      Any -> concatMap leaves (requirementMembers requirement)

unique :: Set Text -> (Text, Text, Maybe Span) -> Either Diagnostic (Set Text)
unique seen (identifier, pointer, sourceSpan)
  | Text.null identifier = failInvariant pointer "empty semantic ID"
  | Set.member identifier seen = Left (diagnostic "KINV002" "validate" pointer sourceSpan
      [("id", identifier)])
  | otherwise = Right (Set.insert identifier seen)

qualified :: Text -> Bool
qualified value = case Text.splitOn ":" value of
  [package, local] -> not (Text.null package || Text.null local)
  _ -> False

requireRule :: [RawRule] -> Text -> Text -> Either Diagnostic RawRule
requireRule rules pointer identifier
  | not (qualified identifier) = failInvariant pointer "unqualified rule reference"
  | otherwise = case filter ((== identifier) . rawRuleId) rules of
      [rule] -> Right rule
      _ -> Left (diagnostic "KINV005" "validate" pointer Nothing [("target", identifier)])

validateRule :: RawGraph a -> RawRule -> Either Diagnostic ()
validateRule graph rule = do
  let executable = branches (rawRuleProgram rule) []
      branchIds = map (provisionId . fst) executable
  if null executable && not (hasDefinition (rawRuleProgram rule)) then
    failInvariant (rawRulePointer rule <> "/program/definitions") "unmarked empty rule"
    else pure ()
  mapM_ (validateException graph rule branchIds executable) (rawRuleExceptions rule)
  where
    hasDefinition provision = provisionDefinitions provision ||
      any hasDefinition (provisionChildren provision)

validateException :: RawGraph a -> RawRule -> [Text] -> [(Provision, [Requirement])]
  -> RawException -> Either Diagnostic ()
validateException graph rule branchIds executable ex = do
  let pointer = rawExceptionPointer ex
  if rawExceptionBranch ex `elem` branchIds then pure () else
    Left (diagnostic "KINV005" "validate" (pointer <> "/branch_id")
      (Just (rawExceptionSpan ex)) [("id", rawExceptionBranch ex)])
  if rawExceptionSource ex == rawRuleSource rule then pure () else
    failInvariant (pointer <> "/source_id") "exception source differs from branch source"
  case [provisionSpan branch | (branch, _) <- executable,
         provisionId branch == rawExceptionBranch ex] of
    [branchSpan] | spanStart branchSpan <= spanStart (rawExceptionSpan ex)
      && spanEnd (rawExceptionSpan ex) <= spanEnd branchSpan -> pure ()
    _ -> Left (diagnostic "KINV003" "validate" (pointer <> "/span")
      (Just (rawExceptionSpan ex)) [])
  _ <- requireRule (rawRules graph) (pointer <> "/guard/target") (rawExceptionTarget ex)
  pure ()

validateAcyclic :: ValidatedGraph a -> Either Diagnostic ()
validateAcyclic graph = do
  _ <- foldM (visit Set.empty) Set.empty (graphOrder graph)
  pure ()
  where
    visit active complete key
      | Set.member key complete = Right complete
      | Set.member key active = Left (diagnostic "KINV006" "validate"
          "/registry" Nothing [("cycle_rule", ruleKeyText key)])
      | otherwise = case ruleFor graph key of
          Nothing -> Left (diagnostic "KINV005" "validate" "/registry" Nothing [])
          Just rule -> do
            let targets = [exceptionTarget ex | identifier <- map (provisionId . fst)
                  (branches (ruleProgram rule) []), ex <- ruleExceptionsFor rule identifier]
            visited <- foldM (visit (Set.insert key active)) complete targets
            Right (Set.insert key visited)

failInvariant :: Text -> Text -> Either Diagnostic a
failInvariant pointer reason = Left (diagnostic "KINV004" "validate" pointer Nothing
  [("reason", reason)])
