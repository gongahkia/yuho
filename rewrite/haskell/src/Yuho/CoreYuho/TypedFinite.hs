{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.TypedFinite
  ( EntityTypeDecl(..), EntityDecl(..), PredicateDecl(..), PredicateKind(..)
  , ScalarType(..), ScalarDecl(..), ScalarValue(..), Term(..), Comparison(..)
  , FiniteExpr(..), CardinalityKind(..), RulePolarity(..), RuleDecl(..)
  , NormModality(..), NormDecl(..), ResponsibilityKind(..), ResponsibilityRoute(..)
  , PriorityDecl(..), GroundFact(..), TypedFiniteProgram(..)
  , FiniteModule(..)
  , ExprObservation(..), RuleObservation(..), PropositionObservation(..)
  , TypedFiniteResult(..), truthName, groundKey, evaluateTypedFinite
  , negateTruth, compareScalar, cardinalityTruth, resolveProposition
  , substituteTerm
  ) where

import Data.List (nub, sort)
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import Yuho.Exception.Types (Truth(..))
import Yuho.SuppliedProofStatus.Evaluate (allStatus, anyStatus)

data EntityTypeDecl = EntityTypeDecl Text deriving (Eq, Ord, Show)
data EntityDecl = EntityDecl Text Text deriving (Eq, Ord, Show)

data PredicateKind = PredicateConduct | PredicateCircumstance
  | PredicateMentalState | PredicateRelationship
  deriving (Eq, Ord, Show)

data PredicateDecl = PredicateDecl
  { predicateName :: Text
  , predicateArguments :: [Text]
  , predicateKind :: PredicateKind
  } deriving (Eq, Ord, Show)

data ScalarType = IntegerType | DateType | EnumType Text [Text] | MoneyType Text
  deriving (Eq, Ord, Show)

data ScalarDecl = ScalarDecl
  { scalarName :: Text
  , scalarType :: ScalarType
  } deriving (Eq, Ord, Show)

data ScalarValue
  = IntegerValue Integer
  | DateValue Day
  | EnumValue Text Text
  | MoneyValue Text Integer
  | ScalarUnresolved Text ScalarType
  deriving (Eq, Ord, Show)

data Term = EntityTerm Text | VariableTerm Text deriving (Eq, Ord, Show)

data Comparison = Equal | NotEqual | LessThan | LessEqual | GreaterThan
  | GreaterEqual | InHalfOpen
  deriving (Eq, Ord, Show)

data CardinalityKind = AtLeast | AtMost | Exactly deriving (Eq, Ord, Show)

data FiniteExpr
  = PredicateExpr Text [Term]
  | ComparisonExpr Comparison Text Text (Maybe Text)
  | AllExpr [FiniteExpr]
  | AnyExpr [FiniteExpr]
  | NotExpr FiniteExpr
  | ForallExpr Text Text FiniteExpr
  | ExistsExpr Text Text FiniteExpr
  | CardinalityExpr CardinalityKind Int [FiniteExpr]
  | ReferenceExpr Text
  deriving (Eq, Ord, Show)

data RulePolarity = Establish | Defeat deriving (Eq, Ord, Show)

data RuleDecl = RuleDecl
  { ruleName :: Text
  , ruleParameters :: [(Text, Text)]
  , rulePolarity :: RulePolarity
  , ruleConclusion :: Text
  , ruleBody :: FiniteExpr
  , ruleCitation :: Maybe Text
  } deriving (Eq, Ord, Show)

data NormModality = Required | Prohibited | Permitted
  deriving (Eq, Ord, Show)

data NormDecl = NormDecl
  { normName :: Text
  , normSubject :: Text
  , normModality :: NormModality
  , normAction :: Text
  , normApplicability :: FiniteExpr
  , normCitation :: Maybe Text
  } deriving (Eq, Ord, Show)

data ResponsibilityKind = PrincipalConduct | JointConduct | Instigation
  | Conspiracy | IntentionalAid | AttemptRoute | AuthoredContribution Text
  deriving (Eq, Ord, Show)

data ResponsibilityRoute = ResponsibilityRoute
  { routeName :: Text
  , routeSubject :: Text
  , routeKind :: ResponsibilityKind
  , routeTarget :: Text
  , routeRequirements :: FiniteExpr
  , routeCitation :: Maybe Text
  } deriving (Eq, Ord, Show)

data PriorityDecl = PriorityDecl Text Text deriving (Eq, Ord, Show)

data GroundFact = GroundFact
  { groundPredicate :: Text
  , groundArguments :: [Text]
  , groundStatus :: Truth
  , groundReason :: Text
  } deriving (Eq, Ord, Show)

data FiniteModule = FiniteModule
  { finiteModuleName :: Text
  , finiteModuleVersion :: Text
  , finiteModuleAlias :: Text
  , finiteModuleExports :: [(Text,Text)]
  } deriving (Eq, Ord, Show)

data TypedFiniteProgram = TypedFiniteProgram
  { finiteProgramId :: Text
  , finiteEntityTypes :: [EntityTypeDecl]
  , finiteEntities :: [EntityDecl]
  , finitePredicates :: [PredicateDecl]
  , finiteScalars :: [ScalarDecl]
  , finitePropositions :: [Text]
  , finiteRequirements :: [(Text, FiniteExpr)]
  , finiteRules :: [RuleDecl]
  , finiteNorms :: [NormDecl]
  , finiteRoutes :: [ResponsibilityRoute]
  , finitePriorities :: [PriorityDecl]
  , finiteFacts :: [GroundFact]
  , finiteValues :: Map Text ScalarValue
  , finiteModules :: [FiniteModule]
  , finiteLimitations :: [Text]
  } deriving (Eq, Show)

data ExprObservation = ExprObservation
  { expressionLabel :: Text
  , expressionStatus :: Truth
  , expressionBindings :: [(Text, Text)]
  , expressionDetail :: Text
  } deriving (Eq, Show)

data RuleObservation = RuleObservation
  { observedRule :: Text
  , observedPolarity :: RulePolarity
  , observedProposition :: Text
  , observedStatus :: Truth
  , observedBindings :: [[(Text, Text)]]
  , observedDefeatedBy :: [Text]
  } deriving (Eq, Show)

data PropositionObservation = PropositionObservation
  { observedPropositionId :: Text
  , propositionStatus :: Truth
  , propositionState :: Text
  , propositionRules :: [Text]
  } deriving (Eq, Show)

data TypedFiniteResult = TypedFiniteResult
  { finiteResultExpressions :: [ExprObservation]
  , finiteResultRules :: [RuleObservation]
  , finiteResultPropositions :: [PropositionObservation]
  } deriving (Eq, Show)

truthName :: Truth -> Text
truthName TrueValue = "satisfied"
truthName FalseValue = "not_satisfied"
truthName UnresolvedValue = "unresolved"

groundKey :: Text -> [Text] -> Text
groundKey name arguments = name <> "(" <> Text.intercalate "," arguments <> ")"

negateTruth :: Truth -> Truth
negateTruth TrueValue = FalseValue
negateTruth FalseValue = TrueValue
negateTruth UnresolvedValue = UnresolvedValue

compareScalar :: Comparison -> ScalarValue -> ScalarValue -> Maybe ScalarValue -> Either Text Truth
compareScalar _ (ScalarUnresolved _ _) _ _ = Right UnresolvedValue
compareScalar _ _ (ScalarUnresolved _ _) _ = Right UnresolvedValue
compareScalar InHalfOpen value lower (Just upper) = do
  left <- compareScalar GreaterEqual value lower Nothing
  right <- compareScalar LessThan value upper Nothing
  pure (allStatus [left,right])
compareScalar InHalfOpen _ _ Nothing = Left "half-open comparison requires an upper operand"
compareScalar operation left right Nothing = case compatible left right of
  Nothing -> Left "incompatible scalar comparison"
  Just ordering -> Right (if relation operation ordering then TrueValue else FalseValue)
compareScalar _ _ _ (Just _) = Left "upper operand is valid only for half-open membership"

compatible :: ScalarValue -> ScalarValue -> Maybe Ordering
compatible (IntegerValue left) (IntegerValue right) = Just (compare left right)
compatible (DateValue left) (DateValue right) = Just (compare left right)
compatible (EnumValue leftType left) (EnumValue rightType right)
  | leftType == rightType = Just (compare left right)
compatible (MoneyValue leftCurrency left) (MoneyValue rightCurrency right)
  | leftCurrency == rightCurrency = Just (compare left right)
compatible _ _ = Nothing

relation :: Comparison -> Ordering -> Bool
relation Equal EQ = True
relation NotEqual value = value /= EQ
relation LessThan LT = True
relation LessEqual value = value /= GT
relation GreaterThan GT = True
relation GreaterEqual value = value /= LT
relation _ _ = False

cardinalityTruth :: CardinalityKind -> Int -> [Truth] -> Truth
cardinalityTruth kindValue threshold values =
  let satisfied = length (filter (== TrueValue) values)
      unresolved = length (filter (== UnresolvedValue) values)
      upper = satisfied + unresolved
  in case kindValue of
    AtLeast | satisfied >= threshold -> TrueValue
            | upper < threshold -> FalseValue
            | otherwise -> UnresolvedValue
    AtMost | upper <= threshold -> TrueValue
           | satisfied > threshold -> FalseValue
           | otherwise -> UnresolvedValue
    Exactly | satisfied == threshold && unresolved == 0 -> TrueValue
            | satisfied > threshold || upper < threshold -> FalseValue
            | otherwise -> UnresolvedValue

evaluateTypedFinite :: TypedFiniteProgram -> Either Text TypedFiniteResult
evaluateTypedFinite program = do
  let facts = Map.fromList [(groundKey (groundPredicate item) (groundArguments item), groundStatus item)
        | item <- finiteFacts program]
      domains = Map.unionWith (++)
        (Map.fromListWith (++) [(kindValue,[identifier])
          | EntityDecl identifier kindValue <- finiteEntities program])
        (Map.fromList [(kindValue,[]) | EntityTypeDecl kindValue <- finiteEntityTypes program])
      requirements = Map.fromList (finiteRequirements program)
      evaluator bindings seen expression = evaluateExpr program facts domains requirements bindings seen expression
  requirementRows <- traverse (\(identifier,expression) -> do
      (status,detail) <- evaluator Map.empty (Set.singleton identifier) expression
      pure (ExprObservation identifier status [] detail)) (finiteRequirements program)
  rawRuleRows <- traverse (evaluateRule evaluator domains) (finiteRules program)
  let ruleRows = map (annotatePriority (finitePriorities program) rawRuleRows) rawRuleRows
  propositionRows <- traverse (resolveProposition (finitePriorities program) ruleRows)
    (finitePropositions program)
  pure (TypedFiniteResult requirementRows ruleRows propositionRows)

evaluateRule :: (Map Text Text -> Set Text -> FiniteExpr -> Either Text (Truth,Text))
  -> Map Text [Text] -> RuleDecl -> Either Text RuleObservation
evaluateRule evaluator domains declaration = do
  bindings <- parameterBindings domains (ruleParameters declaration)
  rows <- traverse (\binding -> do
    (status,_) <- evaluator (Map.fromList binding) Set.empty (ruleBody declaration)
    pure (binding,status)) bindings
  let status = anyStatus (map snd rows)
      witnesses = [binding | (binding,TrueValue) <- rows]
  pure (RuleObservation (ruleName declaration) (rulePolarity declaration)
    (ruleConclusion declaration) status witnesses [])

parameterBindings :: Map Text [Text] -> [(Text,Text)] -> Either Text [[(Text,Text)]]
parameterBindings _ [] = Right [[]]
parameterBindings domains ((variable,kindValue):rest) = do
  domain <- maybe (Left ("unknown parameter type " <> kindValue)) Right
    (Map.lookup kindValue domains)
  remaining <- parameterBindings domains rest
  pure [[(variable,entity)] ++ suffix | entity <- domain, suffix <- remaining]

evaluateExpr :: TypedFiniteProgram -> Map Text Truth -> Map Text [Text]
  -> Map Text FiniteExpr -> Map Text Text -> Set Text -> FiniteExpr
  -> Either Text (Truth,Text)
evaluateExpr program facts domains requirements bindings seen expression = case expression of
  PredicateExpr name terms -> do
    arguments <- traverse (resolveTerm bindings) terms
    let key = groundKey name arguments
    status <- maybe (Left ("missing ground classification " <> key)) Right (Map.lookup key facts)
    pure (status,key)
  ComparisonExpr operation leftName rightName upperName -> do
    left <- value leftName
    right <- value rightName
    upper <- traverse value upperName
    status <- compareScalar operation left right upper
    pure (status,leftName <> " " <> comparisonName operation <> " " <> rightName
      <> maybe "" (" and " <>) upperName)
  AllExpr members -> aggregate allStatus "all" members
  AnyExpr members -> aggregate anyStatus "any" members
  NotExpr member -> do
    (status,detail) <- recurse member
    pure (negateTruth status,"not(" <> detail <> ")")
  ForallExpr variable kindValue body -> quantify allStatus "forall" variable kindValue body
  ExistsExpr variable kindValue body -> quantify anyStatus "exists" variable kindValue body
  CardinalityExpr kindValue threshold members -> do
    rows <- traverse recurse members
    let statuses = map fst rows
        satisfied = length (filter (== TrueValue) statuses)
        unresolved = length (filter (== UnresolvedValue) statuses)
    pure (cardinalityTruth kindValue threshold statuses,
      cardinalityName kindValue <> " " <> Text.pack (show threshold)
      <> " [s=" <> Text.pack (show satisfied) <> ",u=" <> Text.pack (show unresolved) <> "]")
  ReferenceExpr identifier
    | Set.member identifier seen -> Left ("cyclic requirement reference " <> identifier)
    | otherwise -> case Map.lookup identifier requirements of
        Nothing -> Left ("unknown requirement " <> identifier)
        Just target -> evaluateExpr program facts domains requirements bindings
          (Set.insert identifier seen) target
  where
    recurse = evaluateExpr program facts domains requirements bindings seen
    value identifier = maybe (Left ("missing scalar value " <> identifier)) Right
      (Map.lookup identifier (finiteValues program))
    aggregate operation label members = do
      rows <- traverse recurse members
      pure (operation (map fst rows),label <> "(" <> Text.intercalate "," (map snd rows) <> ")")
    quantify operation label variable kindValue body = do
      domain <- maybe (Left ("unknown quantified type " <> kindValue)) Right
        (Map.lookup kindValue domains)
      rows <- traverse (\entity -> evaluateExpr program facts domains requirements
        (Map.insert variable entity bindings) seen body) domain
      let witnesses = [entity | (entity,(TrueValue,_)) <- zip domain rows]
          counterexamples = [entity | (entity,(FalseValue,_)) <- zip domain rows]
          detail = label <> " " <> variable <> ":" <> kindValue
            <> " witnesses=" <> Text.intercalate "," witnesses
            <> " counterexamples=" <> Text.intercalate "," counterexamples
      pure (operation (map fst rows),detail)

resolveTerm :: Map Text Text -> Term -> Either Text Text
resolveTerm _ (EntityTerm identifier) = Right identifier
resolveTerm bindings (VariableTerm variable) = maybe
  (Left ("free variable " <> variable)) Right (Map.lookup variable bindings)

substituteTerm :: Map Text Text -> Term -> Either Text Text
substituteTerm = resolveTerm

resolveProposition :: [PriorityDecl] -> [RuleObservation] -> Text
  -> Either Text PropositionObservation
resolveProposition priorities observations proposition = do
  let relevant = filter ((== proposition) . observedProposition) observations
      opposing left right = observedPolarity left /= observedPolarity right
      blockers item = [observedRule other | other <- relevant, opposing item other,
        priorityHigher priorities (observedRule other) (observedRule item),
        observedStatus other /= FalseValue]
      active item = observedStatus item == TrueValue && null (blockers item)
      establishes = filter (\item -> active item && observedPolarity item == Establish) relevant
      defeats = filter (\item -> active item && observedPolarity item == Defeat) relevant
      unresolvedBlock = any (\item -> observedStatus item == UnresolvedValue) relevant
        || any (not . null . blockers) [item | item <- relevant, observedStatus item == TrueValue]
      (status,state)
        | not (null establishes) && not (null defeats) = (UnresolvedValue,"conflict")
        | not (null establishes) = (TrueValue,"established")
        | not (null defeats) = (FalseValue,"defeated")
        | unresolvedBlock = (UnresolvedValue,"unresolved")
        | otherwise = (FalseValue,"not_established")
  pure (PropositionObservation proposition status state
    (sort (nub (map observedRule relevant))))

annotatePriority :: [PriorityDecl] -> [RuleObservation] -> RuleObservation -> RuleObservation
annotatePriority priorities observations item = item { observedDefeatedBy = sort
  [observedRule other | other <- observations,
    observedProposition other == observedProposition item,
    observedPolarity other /= observedPolarity item,
    observedStatus other /= FalseValue,
    priorityHigher priorities (observedRule other) (observedRule item)] }

priorityHigher :: [PriorityDecl] -> Text -> Text -> Bool
priorityHigher priorities higher lower = go (Set.singleton lower) lower
  where
    go visited current = any (\next -> next == higher
      || (not (Set.member next visited) && go (Set.insert next visited) next))
      [candidate | PriorityDecl candidate below <- priorities, below == current]

comparisonName :: Comparison -> Text
comparisonName Equal = "eq"
comparisonName NotEqual = "neq"
comparisonName LessThan = "lt"
comparisonName LessEqual = "lte"
comparisonName GreaterThan = "gt"
comparisonName GreaterEqual = "gte"
comparisonName InHalfOpen = "in-half-open"

cardinalityName :: CardinalityKind -> Text
cardinalityName AtLeast = "at-least"
cardinalityName AtMost = "at-most"
cardinalityName Exactly = "exactly"
