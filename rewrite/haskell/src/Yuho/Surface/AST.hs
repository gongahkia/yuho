module Yuho.Surface.AST
  ( Combinator(..), Category(..), RuleKind(..), Proof(..), Assignment(..), SourceDecl(..)
  , BurdenAnnotation(..), TechnicalOutput(..), Proposition(..), Element(..), Rule(..), Body(..), Model(..), Scenario(..)
  , Resolved(..), Checked(..), identifier, leafTokens ) where

import Data.Text (Text)
import Yuho.Surface.Token (Token(..))

data Combinator = All | Any deriving (Eq, Show)
data Category = Conduct | Circumstance | Fault | Purpose deriving (Eq, Ord, Show)
data RuleKind = OffenceKind | ExceptionKind deriving (Eq, Show)
data Proof = Proved | NotProved | Unresolved Text deriving (Eq, Show)
data Assignment = Assignment Token Token (Maybe Token) deriving (Eq, Show)
data SourceDecl = SourceDecl Token Token Token deriving (Eq, Show)
data BurdenAnnotation = BurdenAnnotation Token Token Token Token deriving (Eq, Show)
data TechnicalOutput = TechnicalOutput Token Token deriving (Eq, Show)
data Proposition = Leaf Token (Maybe Token) Token (Maybe Token)
  | Group Token Combinator [Token] deriving (Eq, Show)
data Element = Element
  { elementCategory :: Category, elementCategorySource :: Token
  , elementId :: Token, elementQuote :: Token }
  deriving (Eq, Show)
data Rule = Rule
  { ruleKind :: RuleKind, ruleKindSource :: Token, ruleIdentifier :: Token, ruleTarget :: Maybe Token
  , ruleId :: Token, ruleProgram :: Token, rulePath :: Token
  , ruleElements :: [Element], ruleGroups :: [Proposition] }
  deriving (Eq, Show)
data Body = Section Token Token Token Token Token [Proposition] [Assignment]
  | Synthetic Rule Rule [TechnicalOutput] deriving (Eq, Show)
data Model = Model
  { modelIdentifier :: Token
  , modelVariant :: Token
  , modelJurisdiction :: Token
  , modelPurpose :: Token
  , modelRequest :: Token
  , modelDate :: Token
  , modelLimit :: Token
  , modelSources :: [SourceDecl]
  , modelQuotes :: [(Token, Token)]
  , modelBurden :: BurdenAnnotation
  , modelBody :: Body
  , modelLimitations :: [Token]
  } deriving (Eq, Show)
data Scenario = Scenario Token Token [Assignment] deriving (Eq, Show)
data Resolved = ResolvedLeaf Token Token | ResolvedGroup Token Combinator [Resolved]
  deriving (Eq, Show)
data Checked = Checked Model (Maybe Scenario) [(Token, Proof)] Resolved (Maybe Resolved)
  deriving (Eq, Show)

identifier :: Proposition -> Token
identifier (Leaf token _ _ _) = token
identifier (Group token _ _) = token

leafTokens :: Resolved -> [Token]
leafTokens (ResolvedLeaf token _) = [token]
leafTokens (ResolvedGroup _ _ members) = concatMap leafTokens members
