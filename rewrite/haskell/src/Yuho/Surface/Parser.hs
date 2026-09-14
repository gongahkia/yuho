{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Parser (parseModel, parseScenario) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a, [Token]) }

instance Functor P where
  fmap f (P action) = P $ \path input -> do
    (value, rest) <- action path input
    pure (f value, rest)

instance Applicative P where
  pure value = P $ \_ input -> Right (value, input)
  P function <*> P value = P $ \path input -> do
    (f, rest) <- function path input
    (item, final) <- value path rest
    pure (f item, final)

instance Monad P where
  P action >>= function = P $ \path input -> do
    (value, rest) <- action path input
    runP (function value) path rest

current :: P Token
current = P $ \path input -> case input of
  token:_ -> Right (token, input)
  [] -> at "SFE001" path (Token EndToken "" 1 1) "unexpected end of source"

need :: Text -> P Token
need wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token, rest)
  token:_ -> at (if tokenText token `elem` deferred then "SFE013" else "SFE001")
    path token ("expected " <> wanted)
  [] -> at "SFE001" path (Token EndToken "" 1 1) ("expected " <> wanted)
  where deferred = ["exception", "presumption", "penalty", "sentence", "outcome", "evidence"]

kind :: Kind -> P Token
kind wanted = P $ \path input -> case input of
  token:rest | tokenKind token == wanted -> Right (token, rest)
  token:_ -> at "SFE001" path token "unexpected token kind"
  [] -> at "SFE001" path (Token EndToken "" 1 1) "unexpected end of source"

word :: P Token
word = kind WordToken

string :: P Token
string = kind StringToken

optional :: Text -> P Bool
optional wanted = do
  token <- current
  if tokenText token == wanted then need wanted >> pure True else pure False

manyBefore :: Text -> P a -> P [a]
manyBefore ending action = go []
  where
    go reversed = do
      token <- current
      if tokenText token == ending then pure (reverse reversed)
      else if tokenKind token == EndToken then need ending >> pure []
      else do
        item <- action
        go (item : reversed)

assignment :: P Assignment
assignment = do
  item <- word
  (status, reason) <- assignmentValue
  pure (Assignment item status reason)

assignmentValue :: P (Token, Maybe Token)
assignmentValue = do
  _ <- need "="
  status <- word
  hasReason <- optional "("
  reason <- if hasReason then do
    value <- word
    _ <- need ")"
    pure (Just value)
    else pure Nothing
  _ <- need ";"
  pure (status, reason)

assignments :: P [Assignment]
assignments = do
  _ <- need "{"
  rows <- manyBefore "}" assignment
  _ <- need "}"
  pure rows

group :: Token -> P Proposition
group headToken = do
  item <- word
  _ <- need "("
  first <- word
  more <- manyBefore ")" $ do
    _ <- need ","
    word
  _ <- need ")"
  _ <- need ";"
  pure (Group item (if tokenText headToken == "all" then All else Any) (first : more))

proposition :: P Proposition
proposition = do
  headToken <- word
  case tokenText headToken of
    "leaf" -> do
      item <- word
      _ <- need "proposition"
      propositionId <- word
      _ <- need "quote"
      quoteId <- word
      supported <- optional "support"
      support <- if supported then Just <$> word else pure Nothing
      _ <- need ";"
      pure (Leaf item (Just propositionId) quoteId support)
    "all" -> group headToken
    "any" -> group headToken
    _ -> P $ \path _ -> at "SFE005" path headToken "unsupported proposition"

elementOrGroup :: P (Either Element Proposition)
elementOrGroup = do
  headToken <- word
  case tokenText headToken of
    "element" -> Left <$> typedElement
    "all" -> Right <$> group headToken
    "any" -> Right <$> group headToken
    _ -> P $ \path _ -> at "SFE013" path headToken "unsupported rule declaration"

typedElement :: P Element
typedElement = do
      category <- word
      item <- word
      _ <- need "quote"
      quoteId <- word
      supported <- optional "support"
      support <- if supported then Just <$> word else pure Nothing
      _ <- need ";"
      categoryKind <- case tokenText category of
        "conduct" -> pure Conduct
        "circumstance" -> pure Circumstance
        "fault" -> pure Fault
        "purpose" -> pure Purpose
        "result" -> pure Result
        "causation" -> pure Causation
        "intention" -> pure Intention
        "knowledge" -> pure Knowledge
        "unsoundness" -> pure Unsoundness
        "nature-incapacity" -> pure NatureIncapacity
        "ordinary-wrongfulness" -> pure OrdinaryWrongfulness
        "contrary-law-wrongfulness" -> pure ContraryLawWrongfulness
        "control-incapacity" -> pure ControlIncapacity
        "movable-property" -> pure MovableProperty
        "possession" -> pure Possession
        "consent-absence" -> pure ConsentAbsence
        "dishonest-intention" -> pure DishonestIntention
        "movement" -> pure Movement
        "movement-for-taking" -> pure MovementForTaking
        "aid-act" -> pure AidAct
        "illegal-omission" -> pure IllegalOmission
        "consequence" -> pure Consequence
        _ -> P $ \path _ -> at "SFE017" path category "invalid element category"
      pure (Element categoryKind category item quoteId support)

parseDefinitionKind :: P DefinitionKind
parseDefinitionKind = do
  item <- word
  case tokenText item of
    "hurt-result" -> pure HurtResult
    "voluntary-hurt" -> pure VoluntaryHurt
    "wrongful-gain" -> pure WrongfulGain
    "wrongful-loss" -> pure WrongfulLoss
    "dishonesty" -> pure Dishonesty
    _ -> P $ \path _ -> at "SFE051" path item "invalid statutory-definition type"

definitionReference :: P DefinitionReference
definitionReference = do
  _ <- need "use"
  item <- word
  _ <- need "as"
  targetKind <- parseDefinitionKind
  _ <- need ";"
  pure (DefinitionReference item item targetKind)

statutoryDefinition :: P StatutoryDefinition
statutoryDefinition = do
  _ <- need "statutory-definition"
  item <- word
  _ <- need "kind"
  declaredKind <- parseDefinitionKind
  _ <- need "sections"
  first <- StatutorySection <$> word
  more <- manyBefore "{" $ do
    _ <- need ","
    StatutorySection <$> word
  _ <- need "{"
  entries <- manyBefore "}" $ do
    next <- current
    case tokenText next of
      "input" -> need "input" >> (DefinitionEntryInput . DefinitionInput <$> typedElement)
      "mental-state" -> do
        _ <- need "mental-state"
        leaf <- word
        _ <- need "kind"
        kindToken <- word
        mentalKind <- case tokenText kindToken of
          "intention" -> pure MentalIntention
          "knowledge" -> pure MentalKnowledge
          _ -> P $ \path _ -> at "SFE052" path kindToken "invalid mental-state kind"
        _ <- need "target"
        target <- word
        _ <- need "as"
        targetKind <- parseDefinitionKind
        _ <- need "quote"
        quote <- word
        _ <- need ";"
        let category = case mentalKind of
              MentalIntention -> Intention
              MentalKnowledge -> Knowledge
            element = Element category kindToken leaf quote Nothing
        pure (DefinitionEntryMental (MentalStateInput element mentalKind target targetKind))
      "use" -> DefinitionEntryReference <$> definitionReference
      "all" -> need "all" >>= \headToken -> DefinitionEntryGroup <$> group headToken
      "any" -> need "any" >>= \headToken -> DefinitionEntryGroup <$> group headToken
      "output" -> do
        _ <- need "output"
        output <- word
        _ <- need ";"
        pure (DefinitionEntryOutput (DefinitionOutput output))
      _ -> P $ \path _ -> at "SFE051" path next "unsupported statutory-definition declaration"
  _ <- need "}"
  pure (StatutoryDefinition item declaredKind (first:more)
    [value | DefinitionEntryInput value <- entries]
    [value | DefinitionEntryMental value <- entries]
    [value | DefinitionEntryReference value <- entries]
    [value | DefinitionEntryGroup value <- entries]
    [value | DefinitionEntryOutput value <- entries])

definitionsBlock :: P [StatutoryDefinition]
definitionsBlock = do
  _ <- need "definitions"
  _ <- need "{"
  values <- manyBefore "}" statutoryDefinition
  _ <- need "}"
  pure values

partyRoles :: P [PartyRole]
partyRoles = do
  _ <- need "party-roles"
  _ <- need "{"
  values <- manyBefore "}" $ do
    _ <- need "party-role"
    role <- word
    _ <- need ";"
    partyKind <- case tokenText role of
      "role:principal" -> pure PrincipalParty
      "role:alleged-abettor" -> pure AllegedAbettorParty
      _ -> P $ \path _ -> at "SFE063" path role "unsupported party role"
    pure (PartyRole role partyKind)
  _ <- need "}"
  pure values

actorAttributions :: P ([ActorAttributedFact], [ActorAttributedMentalState])
actorAttributions = do
  _ <- need "actor-attributions"
  _ <- need "{"
  entries <- manyBefore "}" $ do
    kindToken <- word
    item <- word
    _ <- need "to"
    owner <- word
    _ <- need ";"
    case tokenText kindToken of
      "fact" -> pure (Left (ActorAttributedFact item (RoleEndpoint owner)))
      "mental-state" -> pure (Right (ActorAttributedMentalState item (RoleEndpoint owner)))
      "relation-fact" -> pure (Left (ActorAttributedFact item (RelationEndpoint owner)))
      _ -> P $ \path _ -> at "SFE067" path kindToken "unsupported actor attribution"
  _ <- need "}"
  pure ([value | Left value <- entries], [value | Right value <- entries])

participationRoute :: P ParticipationRoute
participationRoute = do
  headToken <- need "participation"
  item <- word
  _ <- need "route"
  route <- word
  if tokenText route == "intentional-aid" then pure () else
    P $ \path _ -> at "SFE070" path route "unsupported participation route"
  _ <- need "target"
  target <- word
  _ <- need "rule"
  declaredRule <- word
  _ <- need "program"
  programId <- word
  _ <- need "path"
  sourcePath <- word
  _ <- need "sections"
  first <- StatutorySection <$> word
  rest <- manyBefore "{" $ do
    _ <- need ","
    StatutorySection <$> word
  _ <- need "{"
  declarations <- manyBefore "}" $ do
    next <- current
    if tokenText next == "relation" then do
      _ <- need "relation"
      relationId <- word
      _ <- need "from"
      source <- word
      _ <- need "to"
      destination <- word
      _ <- need "target"
      relationTargetId <- word
      _ <- need "status"
      statusId <- word
      _ <- need "quote"
      quote <- word
      _ <- need ";"
      pure (Left (ParticipationRelation relationId (RoleEndpoint source)
        (RoleEndpoint destination) (ParticipationTarget relationTargetId) statusId quote))
    else Right <$> ruleEntry
  _ <- need "}"
  relation <- case [value | Left value <- declarations] of
    [value] -> pure value
    [] -> P $ \path _ -> at "SFE068" path item "participation relation required"
    _:second:_ -> P $ \path _ -> at "SFE068" path (relationIdentifier second)
      "one participation relation required"
  let participationRuleId = Rule ParticipationKind headToken item (Just target) declaredRule
        programId sourcePath (first:rest)
        [value | Right (RuleElement value) <- declarations]
        [value | Right (RuleGroup value) <- declarations]
        [value | Right (RuleReference value) <- declarations]
  pure (IntentionalAidRoute participationRuleId relation)

instrument :: P StatutoryInstrument
instrument = do
  item <- word
  case tokenText item of
    "PenalCode1871" -> pure PenalCode1871
    "EvidenceAct1893" -> pure EvidenceAct1893
    _ -> P $ \path _ -> at "SFE073" path item "ambiguous or unknown statutory authority"

authorities :: P [AuthorityReference]
authorities = do
  _ <- need "authorities"
  _ <- need "{"
  values <- manyBefore "}" $ do
    _ <- need "authority"
    use <- word
    citedInstrument <- instrument
    source <- word
    _ <- need "section"
    section <- word
    _ <- need ";"
    pure (AuthorityReference use citedInstrument source section)
  _ <- need "}"
  pure values

data DefinitionEntry = DefinitionEntryInput DefinitionInput
  | DefinitionEntryMental MentalStateInput
  | DefinitionEntryReference DefinitionReference
  | DefinitionEntryGroup Proposition
  | DefinitionEntryOutput DefinitionOutput

data RuleEntry = RuleElement Element | RuleGroup Proposition | RuleReference DefinitionReference

ruleEntry :: P RuleEntry
ruleEntry = do
  next <- current
  if tokenText next == "use" then RuleReference <$> definitionReference
  else do
    declaration <- elementOrGroup
    pure (either RuleElement RuleGroup declaration)

rule :: Text -> P Rule
rule role = do
  headToken <- need role
  item <- word
  target <- if role == "exception" then do
    _ <- need "to"
    Just <$> word
    else pure Nothing
  _ <- need "rule"
  declaredRule <- word
  _ <- need "program"
  programId <- word
  _ <- need "path"
  path <- word
  hasSections <- optional "sections"
  sections <- if hasSections then do
    first <- StatutorySection <$> word
    rest <- manyBefore "{" $ do
      _ <- need ","
      StatutorySection <$> word
    pure (first : rest)
    else pure []
  _ <- need "{"
  declarations <- manyBefore "}" ruleEntry
  _ <- need "}"
  pure (Rule (if role == "offence" then OffenceKind else ExceptionKind) headToken item target declaredRule programId path
    sections [value | RuleElement value <- declarations]
    [value | RuleGroup value <- declarations]
    [value | RuleReference value <- declarations])

provenance :: P ([SourceDecl], Maybe Token, [(Token, Token)])
provenance = do
  _ <- need "provenance"
  _ <- need "{"
  rows <- manyBefore "}" $ do
    headToken <- word
    case tokenText headToken of
      "source" -> do
        item <- word
        role <- word
        location <- string
        _ <- need ";"
        pure (Left (Left (SourceDecl item role location)))
      "mapping_source" -> do
        item <- word
        _ <- need ";"
        pure (Left (Right item))
      "quote" -> do
        item <- word
        value <- string
        _ <- need ";"
        pure (Right (item, value))
      _ -> P $ \path _ -> at "SFE013" path headToken "unsupported provenance declaration"
  _ <- need "}"
  let mappings = [item | Left (Right item) <- rows]
  case mappings of
    [] -> pure ([item | Left (Left item) <- rows], Nothing, [item | Right item <- rows])
    [mapping] -> pure ([item | Left (Left item) <- rows], Just mapping, [item | Right item <- rows])
    second:_ -> P $ \path _ -> at "SFE002" path second "duplicate mapping source"

annotations :: P BurdenAnnotation
annotations = do
  _ <- need "annotations"
  _ <- need "{"
  _ <- need "burden"
  a <- word
  b <- word
  c <- word
  d <- word
  _ <- need ";"
  _ <- need "}"
  pure (BurdenAnnotation a b c d)

limitations :: P [Token]
limitations = do
  _ <- need "limitations"
  _ <- need "{"
  values <- manyBefore "}" $ do
    value <- string
    _ <- need ";"
    pure value
  _ <- need "}"
  pure values

scopeAssumptions :: P [ScopeAssumption]
scopeAssumptions = do
  _ <- need "scope-assumptions"
  _ <- need "{"
  assumptions <- manyBefore "}" $ do
    _ <- need "scope-assumption"
    item <- word
    targeted <- optional "for"
    target <- if targeted then Just <$> word else pure Nothing
    _ <- need ";"
    pure (maybe (ScopeAssumption item) (TargetScopeAssumption item) target)
  _ <- need "}"
  pure assumptions

outputs :: P [TechnicalOutput]
outputs = do
  _ <- need "outputs"
  _ <- need "{"
  values <- manyBefore "}" $ do
    label <- word
    target <- word
    _ <- need ";"
    pure (TechnicalOutput label target)
  _ <- need "}"
  pure values

body :: P ([SourceDecl], [(Token, Token)], BurdenAnnotation, Body)
body = do
  next <- current
  if tokenText next == "root" then do
    _ <- need "root"
    rootId <- word
    _ <- need "program"
    programId <- word
    _ <- need "path"
    path <- word
    _ <- need "requires"
    requirement <- word
    _ <- need ";"
    (sources, mapping, quotes) <- provenance
    burden <- annotations
    _ <- need "propositions"
    _ <- need "{"
    declarations <- manyBefore "}" proposition
    _ <- need "}"
    _ <- need "proof_assignments"
    assigned <- assignments
    case mapping of
      Nothing -> P $ \file _ -> at "SFE014" file rootId "mapping source required"
      Just source -> pure (sources, quotes, burden,
        Section rootId programId path requirement source declarations assigned)
  else do
    (sources, mapping, quotes) <- provenance
    case mapping of
      Just item -> P $ \file _ -> at "SFE014" file item "mapping source is unsupported for synthetic model"
      Nothing -> pure ()
    burden <- annotations
    bodyNext <- current
    if tokenText bodyNext == "party-roles" then do
      roles <- partyRoles
      definitions <- definitionsBlock
      (attributedFacts, attributedMentalStates) <- actorAttributions
      assumptions <- scopeAssumptions
      offence <- rule "offence"
      participation <- participationRoute
      citations <- authorities
      declaredOutputs <- outputs
      pure (sources, quotes, burden,
        ParticipationLegal roles definitions attributedFacts attributedMentalStates
          assumptions offence participation citations declaredOutputs)
    else if tokenText bodyNext == "definitions" then do
      definitions <- definitionsBlock
      assumptions <- scopeAssumptions
      offence <- rule "offence"
      moreOffences <- whileWord "offence" (rule "offence")
      exceptions <- whileWord "general-exception"
        (GeneralException <$> rule "general-exception")
      attachments <- whileWord "attach" attachment
      declaredOutputs <- outputs
      pure (sources, quotes, burden,
        DefinitionsLegal definitions assumptions (offence:moreOffences)
          exceptions attachments declaredOutputs)
    else if tokenText bodyNext == "scope-assumptions" then do
      assumptions <- scopeAssumptions
      offence <- rule "offence"
      moreOffences <- whileWord "offence" (rule "offence")
      bodyAfterOffences <- current
      if tokenText bodyAfterOffences == "general-exception" then do
        exceptions <- whileWord "general-exception"
          (GeneralException <$> rule "general-exception")
        attachments <- whileWord "attach" attachment
        declaredOutputs <- outputs
        pure (sources, quotes, burden,
          MultiLegal assumptions (offence : moreOffences) exceptions attachments declaredOutputs)
      else do
        exception <- rule "exception"
        declaredOutputs <- outputs
        pure (sources, quotes, burden, Legal assumptions offence exception declaredOutputs)
    else do
      offence <- rule "offence"
      exception <- rule "exception"
      declaredOutputs <- outputs
      pure (sources, quotes, burden, Synthetic offence exception declaredOutputs)

whileWord :: Text -> P a -> P [a]
whileWord wanted action = do
  next <- current
  if tokenText next == wanted then do
    item <- action
    (item :) <$> whileWord wanted action
  else pure []

attachment :: P Attachment
attachment = do
  keyword <- need "attach"
  exception <- word
  _ <- need "to"
  offence <- word
  _ <- need ";"
  pure (Attachment keyword exception offence)

modelParser :: P Model
modelParser = do
  _ <- need "model"
  item <- word
  _ <- need "{"
  _ <- need "variant"
  variant <- word
  _ <- need ";"
  _ <- need "jurisdiction"
  jurisdiction <- word
  _ <- need ";"
  _ <- need "purpose"
  purpose <- word
  _ <- need ";"
  _ <- need "request"
  requestId <- word
  _ <- need ";"
  _ <- need "policy"
  referenceDate <- word
  limit <- word
  _ <- need ";"
  (sources, quotes, burden, parsedBody) <- body
  limits <- limitations
  _ <- need "}"
  _ <- kind EndToken
  pure (Model item variant jurisdiction purpose requestId referenceDate limit
    sources quotes burden parsedBody limits)

parseModel :: FilePath -> BS.ByteString -> Either Diagnostic Model
parseModel path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP modelParser path tokens

scenarioParser :: P Scenario
scenarioParser = do
  _ <- need "scenario"
  requestId <- word
  _ <- need "for"
  modelId <- word
  _ <- need "{"
  entries <- manyBefore "}" $ do
    next <- current
    if tokenText next == "analyse" then do
      _ <- need "analyse"
      item <- word
      _ <- need ";"
      pure (ScenarioTarget item)
    else if tokenText next == "assume" then do
      _ <- need "assume"
      item <- word
      _ <- need ";"
      pure (ScenarioAssumption (ScopeAcknowledgement item))
    else if tokenText next == "bind" then do
      _ <- need "bind"
      role <- word
      _ <- need "to"
      actor <- word
      _ <- need ";"
      pure (ScenarioBinding (ActorBinding role actor))
    else do
      item <- word
      if "rel:" `Text.isPrefixOf` tokenText item then do
        _ <- need "from"
        source <- word
        _ <- need "to"
        destination <- word
        (status,reason) <- assignmentValue
        pure (ScenarioRelation (RelationAssignment item source destination status reason))
      else do
        attributed <- optional "by"
        if attributed then do
          actor <- word
          (status,reason) <- assignmentValue
          pure (ScenarioActorAssignment (ActorAssignment item actor status reason))
        else do
          (status,reason) <- assignmentValue
          pure (ScenarioPlainAssignment (Assignment item status reason))
  _ <- need "}"
  _ <- kind EndToken
  let bindings = [item | ScenarioBinding item <- entries]
      actors = [item | ScenarioActorAssignment item <- entries]
      relations = [item | ScenarioRelation item <- entries]
      plain = [item | ScenarioPlainAssignment item <- entries]
      acknowledgements = [item | ScenarioAssumption item <- entries]
      targets = [item | ScenarioTarget item <- entries]
  if null bindings && null actors && null relations then
    pure (Scenario requestId modelId plain acknowledgements targets)
  else pure (ParticipationScenario requestId modelId bindings actors relations
    plain acknowledgements targets)

data ScenarioEntry = ScenarioTarget Token | ScenarioAssumption ScopeAcknowledgement
  | ScenarioBinding ActorBinding | ScenarioActorAssignment ActorAssignment
  | ScenarioRelation RelationAssignment | ScenarioPlainAssignment Assignment

parseScenario :: FilePath -> BS.ByteString -> Either Diagnostic Scenario
parseScenario path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP scenarioParser path tokens
