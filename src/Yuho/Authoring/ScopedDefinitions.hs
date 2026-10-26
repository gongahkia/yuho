{-# LANGUAGE OverloadedStrings #-}
-- | Opt-in scoped typed requirement authoring. These builders emit readable .yh
-- declarations; the ordinary checked-plan compiler remains the authority for
-- types, scopes, assessments, expansion limits and evaluation. Old SDK profiles
-- (including linked-definition AREUSE) are not changed.
module Yuho.Authoring.ScopedDefinitions
  ( module Yuho.ScopedDefinitions.Types, ScopedBody(..)
  , requirementTemplate, requirementUse, inspectScopedDefinitions
  ) where
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import qualified Data.Aeson as A
import Yuho.Dependency.Types (DependencyDiagnostic(..))
import Yuho.Dependency.Run (DependencyExecution,scopedDefinitionEvidence)
import Yuho.ScopedDefinitions.Types
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token (tokenText,tokenKind,Kind(..))

data ScopedBody = ScopedAtom Text [Text] | ScopedAll [ScopedBody] | ScopedAny [ScopedBody]
  | ScopedNot ScopedBody | ScopedForall Text Text ScopedBody | ScopedExists Text Text ScopedBody
  deriving (Eq,Show)

-- | One reusable declaration. Every term in an atom is a formal/locally bound
-- variable; constants, scalar captures and template recursion are not admitted.
requirementTemplate :: Text -> [(Text,Text)] -> ScopedBody -> Either DependencyDiagnostic Text
requirementTemplate name formals body=do
  n<-word name
  ps<-traverse (\(v,t)->do v'<-word v;t'<-word t;pure (v'<>" as "<>t')) formals
  b<-render body
  pure ("requirement-template "<>n<>"("<>T.intercalate "," ps<>") = "<>b<>";")
 where
  render e=case e of
    ScopedAtom n xs->do n'<-word n;xs'<-traverse word xs;pure (n'<>"("<>T.intercalate "," xs'<>")")
    ScopedAll xs->aggregate "all" xs
    ScopedAny xs->aggregate "any" xs
    ScopedNot x->do x'<-render x;pure ("not("<>x'<>")")
    ScopedForall v t x->quantify "forall" v t x
    ScopedExists v t x->quantify "exists" v t x
  aggregate n xs=do xs'<-traverse render xs;pure (n<>"("<>T.intercalate "," xs'<>")")
  quantify k v t x=do v'<-word v;t'<-word t;x'<-render x;pure (k<>" "<>v'<>" as "<>t'<>"("<>x'<>")")

-- | Explicit use and assessment policy. Independent selections are independent
-- checked components/scenarios; sharing an exact tuple within one scenario is
-- explicit and never changes the original definition or source classifications.
requirementUse :: Text -> Text -> [Text] -> Either DependencyDiagnostic Text
requirementUse use target args=do
  u<-word use;t<-word target;as<-traverse word args
  pure ("requirement-use "<>u<>" from "<>t<>"("<>T.intercalate "," as<>") assessments scenario;")

inspectScopedDefinitions :: DependencyExecution -> A.Value
inspectScopedDefinitions=scopedDefinitionEvidence

word :: Text -> Either DependencyDiagnostic Text
word text=case lexSource "<scoped-sdk-identifier>" (U.encodeUtf8 text) of
  Right [t,end] | tokenKind t==WordToken,tokenKind end==EndToken,tokenText t==text->Right text
  _->Left (DependencyDiagnostic "SFNAME" "expected one admitted source identifier, without source interpolation" [text] Nothing [])
