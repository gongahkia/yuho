{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.ActorExceptions
  ( scopedToken, scopeTree, actContextToken, attachmentTargetToken
  , sharedExceptionTree, attachmentRuleId, attachmentProgramId, attachmentPath ) where

import qualified Data.Text as Text
import Yuho.Surface.AST
import Yuho.Surface.Resolve (resolveTree)
import Yuho.Surface.Token (Diagnostic, Token(..))

scopedToken :: Token -> Token -> Token
scopedToken instanceId authored = authored { tokenText = prefix <> ":"
    <> Text.drop 3 (tokenText instanceId) <> "--" <> Text.drop 2 original }
  where
    original = tokenText authored
    prefix = Text.takeWhile (/= ':') original

scopeTree :: Token -> Resolved -> Resolved
scopeTree instanceId (ResolvedLeaf item quote) =
  ResolvedLeaf (scopedToken instanceId item) quote
scopeTree instanceId (ResolvedGroup item combinator members) =
  ResolvedGroup (scopedToken instanceId item) combinator
    (map (scopeTree instanceId) members)

actContextToken :: ActContext -> Token
actContextToken (PrincipalConductContext item) = item
actContextToken (AidConductContext item) = item
actContextToken (AttemptConductContext item) = item

attachmentTargetToken :: AttachmentTargetKind -> Token
attachmentTargetToken (CandidateOffenceTarget item) = item
attachmentTargetToken (ParticipationAttachmentTarget item) = item
attachmentTargetToken (AttemptAttachmentTarget item) = item

sharedExceptionTree :: FilePath -> ActorExceptionDefinition
  -> Either Diagnostic Resolved
sharedExceptionTree path (ActorExceptionDefinition _ rule) =
  case reverse (ruleGroups rule) of
    Group root _ _:_ -> resolveTree path declarations root
    _ -> resolveTree path declarations (ruleIdentifier rule)
  where
    declarations = [Leaf (elementId item) Nothing (elementQuote item) (elementSupport item)
      | item <- ruleElements rule] ++ ruleGroups rule

attachmentRuleId :: Token -> Token
attachmentRuleId item = item { tokenText = "r:" <> Text.drop 3 (tokenText item) <> "--section84" }

attachmentProgramId :: Token -> Token
attachmentProgramId item = item { tokenText = "p:" <> Text.drop 3 (tokenText item) <> "--section84" }

attachmentPath :: Token -> Token
attachmentPath item = item { tokenText = "section84-" <> Text.drop 3 (tokenText item) }
