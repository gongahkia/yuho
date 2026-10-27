{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.TypedFinite
  ( EntityTypeDecl(..), EntityDecl(..), PredicateDecl(..), PredicateKind(..)
  , ScalarType(..), ScalarDecl(..), ScalarValue(..), Term(..), Comparison(..)
  , FiniteExpr(..), CardinalityKind(..), RulePolarity(..), RuleDecl(..)
  , NormModality(..), NormDecl(..), ResponsibilityKind(..), ResponsibilityRoute(..)
  , PriorityDecl(..), GroundFact(..), TypedFiniteProgram(..)
  , FiniteModule(..)
  , ExprObservation(..), RuleObservation(..), PropositionObservation(..)
  , TypedFiniteResult(..), truthName, groundKey, GroundIdentity, groundIdentity, groundIdentityText, evaluateTypedFinite
  , negateTruth, compareScalar, cardinalityTruth, resolveProposition
  , FiniteRead(..), FiniteInput(..), inputDisplay, evaluateTypedFiniteObserved, checkTypedFiniteInputs
  , expandedProgramSize, substituteTerm
  ) where

import Control.Monad (foldM)
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

-- Display text above is deliberately not a lookup key. Argument boundaries and
-- predicate identity remain structural, including admitted punctuation/Unicode.
type GroundIdentity = (Text,[Text])
groundIdentity :: Text -> [Text] -> GroundIdentity
groundIdentity = (,)

-- Existing opaque textual mapping/graph IDs remain byte-compatible on the
-- unambiguous legacy alphabet. The escaped namespace starts with '(', which
-- no legacy-safe predicate can start with. Its length-prefixed tuple is
-- reversible and includes arity/order; neither branch aliases the other.
groundIdentityText :: Text -> [Text] -> Text
groundIdentityText name arguments
  | all (Text.all (`notElem` ("(),"::String))) (name:arguments) = groundKey name arguments
  | otherwise = "(tuple)" <> Text.concat [Text.pack (show (Text.length x)) <> ":" <> x | x<-name:arguments]

factTable :: [GroundFact] -> Either Text (Map GroundIdentity GroundFact)
factTable facts =
  let table=Map.fromList [(groundIdentity (groundPredicate f) (groundArguments f),f) | f<-facts]
  in if Map.size table==length facts then Right table else Left "duplicate ground fact"

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

-- | Actual eager evaluation ledger. Paths are occurrence paths within a named
-- expression or a grounded rule invocation; reference expansion is retained.
-- This ledger is opt-in: the established result encoder remains unchanged.
data FiniteInput = GroundInput GroundFact | RequirementInput Text | ScalarInput Text
  deriving (Eq, Show)

-- Only a legacy human-readable description. Never use this to join provenance.
inputDisplay :: FiniteInput -> Text
inputDisplay (GroundInput f)=groundKey (groundPredicate f) (groundArguments f)
inputDisplay (RequirementInput i)=i
inputDisplay (ScalarInput i)=i

data FiniteRead = FiniteRead
  { readRoot :: [Text], readPath :: [Int], readBindings :: [(Text,Text)]
  , readKind :: Text, readStatus :: Truth, readDetail :: Text
  , readInputs :: [FiniteInput]
  } deriving (Eq, Show)

evaluateTypedFinite :: TypedFiniteProgram -> Either Text TypedFiniteResult
evaluateTypedFinite program = fst <$> evaluateTypedFiniteObserved program

evaluateTypedFiniteObserved :: TypedFiniteProgram -> Either Text (TypedFiniteResult,[FiniteRead])
evaluateTypedFiniteObserved program = do
  facts <- factTable (finiteFacts program)
  let domains = programDomains program
      requirements = Map.fromList (finiteRequirements program)
      evaluator root bindings seen = evaluateExpr program facts domains requirements root [] bindings seen
  requirementRows <- traverse (\(identifier,expression) -> do
      (status,detail,ledger) <- evaluator ["expression",identifier] Map.empty (Set.singleton identifier) expression
      pure (ExprObservation identifier status [] detail,ledger)) (finiteRequirements program)
  rawRuleRows <- traverse (\declaration -> do
    bindings <- parameterBindings domains (ruleParameters declaration)
    rows <- traverse (\binding -> do
      (status,_,ledger) <- evaluator (["rule",ruleName declaration] ++ concatMap (\(k,v)->[k,v]) binding)
        (Map.fromList binding) Set.empty (ruleBody declaration)
      pure (binding,status,ledger)) bindings
    pure (RuleObservation (ruleName declaration) (rulePolarity declaration)
      (ruleConclusion declaration) (anyStatus [status | (_,status,_) <- rows])
      [binding | (binding,TrueValue,_) <- rows] [], concat [ledger | (_,_,ledger) <- rows])) (finiteRules program)
  let ruleRows = map (annotatePriority (finitePriorities program) (map fst rawRuleRows)) (map fst rawRuleRows)
  propositionRows <- traverse (resolveProposition (finitePriorities program) ruleRows) (finitePropositions program)
  pure (TypedFiniteResult (map fst requirementRows) ruleRows propositionRows,
    concatMap snd requirementRows ++ concatMap snd rawRuleRows)

programDomains :: TypedFiniteProgram -> Map Text [Text]
programDomains program = Map.unionWith (++)
  (Map.fromListWith (++) [(kindValue,[identifier]) | EntityDecl identifier kindValue <- finiteEntities program])
  (Map.fromList [(kindValue,[]) | EntityTypeDecl kindValue <- finiteEntityTypes program])

parameterBindings :: Map Text [Text] -> [(Text,Text)] -> Either Text [[(Text,Text)]]
parameterBindings _ [] = Right [[]]
parameterBindings domains ((variable,kindValue):rest) = do
  domain <- maybe (Left ("unknown parameter type " <> kindValue)) Right (Map.lookup kindValue domains)
  remaining <- parameterBindings domains rest
  pure [[(variable,entity)] ++ suffix | entity <- domain, suffix <- remaining]

-- | Structural input readiness traverses all groundings without computing a
-- technical value. Used only by the new plan checker, not as an evaluation.
checkTypedFiniteInputs :: TypedFiniteProgram -> Either Text ()
checkTypedFiniteInputs program = do
  _ <- factTable (finiteFacts program)
  mapM_ (\(i,e)->walk Map.empty (Set.singleton i) e) (finiteRequirements program)
  mapM_ (\r->parameterBindings domains (ruleParameters r) >>= mapM_
    (\bs->walk (Map.fromList bs) Set.empty (ruleBody r))) (finiteRules program)
  where
    domains = programDomains program
    facts = Set.fromList [groundIdentity (groundPredicate f) (groundArguments f) | f <- finiteFacts program]
    walk bindings seen expression = case expression of
      PredicateExpr name terms -> do
        arguments <- traverse (resolveTerm bindings) terms
        let key = groundKey name arguments
        if Set.member (groundIdentity name arguments) facts then Right () else Left ("missing ground classification " <> key)
      ComparisonExpr _ l r u -> mapM_ (\i->if Map.member i (finiteValues program)
        then Right () else Left ("missing scalar value "<>i)) (l:r:maybe [] (:[]) u)
      AllExpr xs -> mapM_ (walk bindings seen) xs
      AnyExpr xs -> mapM_ (walk bindings seen) xs
      NotExpr x -> walk bindings seen x
      CardinalityExpr _ _ xs -> mapM_ (walk bindings seen) xs
      ForallExpr v t x -> quant v t x
      ExistsExpr v t x -> quant v t x
      ReferenceExpr i | Set.member i seen -> Left ("cyclic requirement reference "<>i)
        | otherwise -> maybe (Left ("unknown requirement "<>i))
            (walk bindings (Set.insert i seen)) (lookup i (finiteRequirements program))
      where quant v t x = maybe (Left ("unknown quantified type "<>t))
              (mapM_ (\e->walk (Map.insert v e bindings) seen x)) (Map.lookup t domains)

evaluateExpr :: TypedFiniteProgram -> Map GroundIdentity GroundFact -> Map Text [Text]
  -> Map Text FiniteExpr -> [Text] -> [Int] -> Map Text Text -> Set Text -> FiniteExpr
  -> Either Text (Truth,Text,[FiniteRead])
evaluateExpr program facts domains requirements root path bindings seen expression = do
  (status,detail,inputs,children) <- case expression of
    PredicateExpr name terms -> do
      arguments <- traverse (resolveTerm bindings) terms
      let key = groundKey name arguments
      fact <- maybe (Left ("missing ground classification " <> key)) Right (Map.lookup (groundIdentity name arguments) facts)
      pure (groundStatus fact,key,[GroundInput fact],[])
    ComparisonExpr operation leftName rightName upperName -> do
      left <- value leftName
      right <- value rightName
      upper <- traverse value upperName
      status <- compareScalar operation left right upper
      pure (status,leftName <> " " <> comparisonName operation <> " " <> rightName
        <> maybe "" (" and " <>) upperName,map ScalarInput (leftName:rightName:maybe [] (:[]) upperName),[])
    AllExpr members -> aggregate allStatus "all" members
    AnyExpr members -> aggregate anyStatus "any" members
    NotExpr member -> do
      (status,detail,ledger) <- recurse 0 member
      pure (negateTruth status,"not(" <> detail <> ")",[],ledger)
    ForallExpr variable kindValue body -> quantify allStatus "forall" variable kindValue body
    ExistsExpr variable kindValue body -> quantify anyStatus "exists" variable kindValue body
    CardinalityExpr kindValue threshold members -> do
      rows <- traverse (uncurry recurse) (zip [0..] members)
      let statuses = [s | (s,_,_) <- rows]
          satisfied = length (filter (== TrueValue) statuses)
          unresolved = length (filter (== UnresolvedValue) statuses)
      pure (cardinalityTruth kindValue threshold statuses,
        cardinalityName kindValue <> " " <> Text.pack (show threshold)
        <> " [s=" <> Text.pack (show satisfied) <> ",u=" <> Text.pack (show unresolved) <> "]",[],concat [rs | (_,_,rs)<-rows])
    ReferenceExpr identifier
      | Set.member identifier seen -> Left ("cyclic requirement reference " <> identifier)
      | otherwise -> case Map.lookup identifier requirements of
          Nothing -> Left ("unknown requirement " <> identifier)
          Just target -> do
            (s,d,rs) <- evaluateExpr program facts domains requirements root (path++[0]) bindings
              (Set.insert identifier seen) target
            pure (s,d,[RequirementInput identifier],rs)
  pure (status,detail,FiniteRead root path (Map.toAscList bindings) (kind expression) status detail inputs:children)
  where
    recurse index = evaluateExpr program facts domains requirements root (path++[index]) bindings seen
    value identifier = maybe (Left ("missing scalar value " <> identifier)) Right
      (Map.lookup identifier (finiteValues program))
    aggregate operation label members = do
      rows <- traverse (uncurry recurse) (zip [0..] members)
      pure (operation [s | (s,_,_)<-rows],label <> "(" <> Text.intercalate "," [d | (_,d,_)<-rows] <> ")",[],concat [rs | (_,_,rs)<-rows])
    quantify operation label variable kindValue body = do
      domain <- maybe (Left ("unknown quantified type " <> kindValue)) Right (Map.lookup kindValue domains)
      rows <- traverse (\(index,entity) -> evaluateExpr program facts domains requirements root (path++[index])
        (Map.insert variable entity bindings) seen body) (zip [0..] domain)
      let witnesses = [entity | (entity,(TrueValue,_,_)) <- zip domain rows]
          counterexamples = [entity | (entity,(FalseValue,_,_)) <- zip domain rows]
          detail = label <> " " <> variable <> ":" <> kindValue
            <> " witnesses=" <> Text.intercalate "," witnesses
            <> " counterexamples=" <> Text.intercalate "," counterexamples
      pure (operation [s | (s,_,_)<-rows],detail,[],concat [rs | (_,_,rs)<-rows])
    kind e = case e of
      PredicateExpr {} -> "predicate"; ComparisonExpr op _ _ _ -> comparisonName op
      AllExpr {} -> "all"; AnyExpr {} -> "any"; NotExpr {} -> "not"
      ForallExpr {} -> "forall"; ExistsExpr {} -> "exists"
      CardinalityExpr k _ _ -> cardinalityName k; ReferenceExpr {} -> "reference"

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
priorityHigher priorities higher lower = go (Set.singleton lower) (parents lower)
  where
    parents current = [candidate | PriorityDecl candidate below <- priorities, below == current]
    go _ [] = False
    go visited (next:rest)
      | next == higher = True
      | Set.member next visited = go visited rest
      | otherwise = go (Set.insert next visited) (parents next ++ rest)

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

-- | Authoritative expanded structural cost for the frozen typed kernel request.
expandedProgramSize :: TypedFiniteProgram -> Either Text Integer
expandedProgramSize program = do
  let domains = Map.unionWith (+)
        (Map.fromListWith (+)
          [(kindValue,1 :: Integer) | EntityDecl _ kindValue <- finiteEntities program])
        (Map.fromList [(kindValue,0) | EntityTypeDecl kindValue <- finiteEntityTypes program])
      requirements = Map.fromList (finiteRequirements program)
      -- Cache named sizes, not expanded trees. A short reference DAG can denote
      -- exponentially many nodes; estimating it must not perform that expansion.
      named active cache identifier
        | Set.member identifier active = Left "cyclic requirement expansion"
        | Just size <- Map.lookup identifier cache = Right (size,cache)
        | otherwise = do
            target <- maybe (Left "unknown requirement expansion") Right
              (Map.lookup identifier requirements)
            (size,next) <- expression (Set.insert identifier active) cache target
            pure (size,Map.insert identifier size next)
      expression active cache item = case item of
        AllExpr members -> aggregate active cache members
        AnyExpr members -> aggregate active cache members
        NotExpr member -> bump <$> expression active cache member
        ForallExpr _ kindValue member -> quantified active cache kindValue member
        ExistsExpr _ kindValue member -> quantified active cache kindValue member
        CardinalityExpr _ _ members -> aggregate active cache members
        ReferenceExpr identifier -> bump <$> named active cache identifier
        _ -> Right (1,cache)
      bump (size,cache) = (1+size,cache)
      aggregate active cache members = foldM
        (\(total,known) member -> do
          (size,next) <- expression active known member
          pure (total+size,next)) (1,cache) members
      quantified active cache kindValue member = do
        count <- maybe (Left "unknown quantified domain") Right (Map.lookup kindValue domains)
        (size,next) <- expression active cache member
        pure (1 + count * size,next)
      parameterCount declaration = product <$> traverse
        (\(_,kindValue) -> maybe (Left "unknown rule parameter domain") Right
          (Map.lookup kindValue domains)) (ruleParameters declaration)
      ruleSize (total,cache) declaration = do
        bindings <- parameterCount declaration
        (body,next) <- expression Set.empty cache (ruleBody declaration)
        pure (total + 1 + bindings * body,next)
  (requirementsSize,cache) <- foldM
    (\(total,known) (identifier,_) -> do
      (size,next) <- named Set.empty known identifier
      pure (total+size,next)) (0,Map.empty) (finiteRequirements program)
  (rulesSize,_) <- foldM ruleSize (0,cache) (finiteRules program)
  pure (fromIntegral (length (finiteEntityTypes program) + length (finiteEntities program)
    + length (finitePredicates program) + length (finiteScalars program)
    + length (finitePropositions program) + length (finitePriorities program)
    + length (finiteFacts program) + Map.size (finiteValues program))
    + requirementsSize + rulesSize)
