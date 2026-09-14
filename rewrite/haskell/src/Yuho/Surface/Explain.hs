{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Explain (explainChecked) where

import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Protocol.Json (decodeJson)
import Yuho.Surface.AST
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Token (Diagnostic, Token(..), at)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)
import Yuho.SuppliedProofStatus.Types
  ( ProofBranch(..), ProofReason(..), ProofResult(..), ProofRule(..), ProofTrace(..)
  , satisfactionText )
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

explainChecked :: FilePath -> Checked -> Either Diagnostic Text
explainChecked path checked@(Checked model scenario assignments offenceTree exceptionTree) =
  case (scenario, exceptionTree) of
    (Just (Scenario _ _ _ acknowledgements targets), Just defenceTree) -> do
      (offence, exception, introduction, sourceReferences, offenceHeading) <-
        case modelBody model of
          Legal _ selected shared _ | null targets -> Right
            (selected, shared, [], [], "Candidate offence chain (Penal Code ss 319, 321, 323):")
          MultiLegal _ offences exceptions attachments _ -> case targets of
            [target] -> case [(selected, shared) | selected <- offences,
              tokenText (ruleIdentifier selected) == tokenText target,
              Attachment _ exceptionId owner <- attachments,
              tokenText owner == tokenText target,
              GeneralException shared <- exceptions,
              tokenText (ruleIdentifier shared) == tokenText exceptionId] of
              [(selected, shared)] -> Right
                (selected, shared,
                 ["Selected candidate offence: " <> tokenText target
                 ,"Candidate statutory sections: Penal Code ss " <>
                    sectionList (ruleSections selected)
                 ,"General exception: Penal Code s " <> sectionList (ruleSections shared)
                 ,"Attachment: s " <> sectionList (ruleSections shared)
                    <> " -> candidate " <> tokenText target
                 ,"Definition instance: shared " <> tokenText (ruleIdentifier shared)],
                 ["  " <> tokenText (elementId item) <> " -> "
                   <> tokenText (elementQuote item)
                   <> maybe "" (\support -> " + " <> tokenText support) (elementSupport item)
                  | item <- ruleElements shared],
                 "Selected candidate offence requirements:")
              _ -> at "SFE040" path target "selected exception attachment is not unique"
            _ -> at "SFE036" path (modelIdentifier model) "one analysis target required"
          _ -> at "SFE013" path (modelIdentifier model)
            "explain requires a checked research offence model and scenario"
      request <- lowerChecked checked
      value <- either (const (at "SFE014" path (modelIdentifier model) "compiled request is invalid JSON"))
        Right (decodeJson request)
      decoded <- kernel (decodeProofRequest value)
      validated <- kernel (validateProofRequest decoded)
      result <- kernel (evaluateProof validated)
      _ <- kernel (selectProofPenalties validated result)
      offenceResult <- case [item | item <- proofResultRules result,
        proofRuleId item == tokenText (ruleId offence)] of
        [item] -> Right item
        _ -> at "SFE014" path (ruleId offence) "candidate rule result missing"
      branch <- case proofRuleBranches offenceResult of
        [item] -> Right item
        _ -> at "SFE014" path (ruleId offence) "candidate branch result missing"
      let defenceResult = case [item | item <- proofResultRules result,
            proofRuleId item == tokenText (ruleId exception)] of
            [item] -> Just item
            _ -> Nothing
          supplied = Map.fromList [(tokenText item, proofText status)
            | (item, status) <- assignments]
          offenceValues = traceValues offenceResult
          defenceValues = maybe Map.empty traceValues defenceResult
          acknowledged = [tokenText item | ScopeAcknowledgement item <- acknowledgements]
          BurdenAnnotation annotation holder burdenKind standard = modelBurden model
          linesOfText =
            ["Model: " <> tokenText (modelIdentifier model)
            ,"Jurisdiction: " <> tokenText (modelJurisdiction model)
              <> " — research POC; synthetic classifications only"
            ] ++ introduction ++
            ["Scope assumptions: acknowledged by scenario, not inferred or proved"]
            ++ map ("  " <>) acknowledged
            ++ [offenceHeading]
            ++ renderTree 1 supplied offenceValues offenceTree
            ++ ["Section 84 general exception:"]
            ++ renderTree 1 supplied defenceValues defenceTree
            ++ (if null sourceReferences then [] else
                  "Section 84 source references:" : sourceReferences)
            ++ ["Section 84 kernel rule: " <>
                  maybe "not_evaluated" (satisfactionText . proofRuleStatus) defenceResult
                ,"Section 107 context: " <> tokenText annotation <> "; "
                  <> tokenText holder <> " " <> tokenText burdenKind <> " burden; "
                  <> tokenText standard <> ". This annotation does not classify evidence."
                ,"Final technical status: " <> satisfactionText (proofResultStatus result)
                  <> " (" <> reasonText (proofBranchReason branch) <> ")"
                ,"No guilt, conviction, acquittal or sentence was determined."]
      Right (Text.unlines linesOfText)
    _ -> at "SFE013" path (modelIdentifier model)
      "explain requires a checked research offence model and scenario"
  where
    kernel result = either (const (at "SFE014" path (modelIdentifier model)
      "Haskell kernel rejected the compiled research model")) Right result

traceValues :: ProofRule -> Map Text Text
traceValues item = Map.fromList
  [(proofTraceId trace, satisfactionText (proofTraceStatus trace))
  | trace <- proofRuleTrace item]

renderTree :: Int -> Map Text Text -> Map Text Text -> Resolved -> [Text]
renderTree depth supplied evaluated node = case node of
  ResolvedLeaf item _ ->
    [indent <> tokenText item <> " — supplied "
      <> Map.findWithDefault "missing" (tokenText item) supplied
      <> "; technical " <> Map.findWithDefault "not_evaluated" (tokenText item) evaluated]
  ResolvedGroup item combinator members ->
    (indent <> tokenText item <> " — " <> combinatorText combinator <> "; technical "
      <> Map.findWithDefault "not_evaluated" (tokenText item) evaluated)
      : concatMap (renderTree (depth + 1) supplied evaluated) members
  where indent = Text.replicate depth "  "

combinatorText :: Combinator -> Text
combinatorText All = "all"
combinatorText Any = "any"

proofText :: Proof -> Text
proofText Proved = "proved"
proofText NotProved = "not_proved"
proofText (Unresolved reason) = "unresolved(" <> reason <> ")"

reasonText :: ProofReason -> Text
reasonText ProofSatisfied = "candidate requirements technically satisfied; no section 84 defeat"
reasonText ProofRequirementsNotSatisfied = "candidate requirements not technically satisfied"
reasonText ProofRequirementsUnresolved = "candidate requirements unresolved"
reasonText ProofDefeated = "candidate branch technically defeated by section 84"
reasonText ProofExceptionUnresolved = "section 84 guard unresolved"

sectionList :: [StatutorySection] -> Text
sectionList sections = Text.intercalate ", "
  [tokenText item | StatutorySection item <- sections]
