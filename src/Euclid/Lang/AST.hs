{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE PatternSynonyms #-}

module Euclid.Lang.AST
    ( AnnotationDecl(..)
    , AppearanceDecl(..)
    , ConstraintDecl(..)
    , ScenarioDecl(..)
    , ViewDecl(..)
    , EntityDecl(..)
    , StateChangeDecl(..)
    , Expr(..)
    , FnDecl(..)
    , ForDecl(..)
    , ForIterable(..)
    , IfDecl(..)
    , LetDecl(..)
    , MatchArm(..)
    , MatchDecl(..)
    , MatchPattern(..)
    , Program(..)
    , pattern Program
    , Quantifier(..)
    , RepeatDecl(..)
    , CausalDeclKind(..)
    , RelationshipDecl(..)
    , RelationshipTypeDecl(..)
    , DeadlineRuleDecl(..)
    , IssueElementDecl(..)
    , LegalIssueDecl(..)
    , RulesetDecl(..)
    , SourceBundleDecl(..)
    , SourceLocatorDecl(..)
    , SourceDecl(..)
    , Stmt(..)
    , pattern StmtAssign
    , pattern StmtConstraint
    , pattern StmtView
    , pattern StmtScenario
    , pattern StmtEntity
    , pattern StmtExpr
    , pattern StmtFor
    , pattern StmtFunction
    , pattern StmtIf
    , pattern StmtImport
    , pattern StmtLet
    , pattern StmtMatch
    , pattern StmtRelationship
    , pattern StmtRelationshipType
    , pattern StmtRepeat
    , pattern StmtReturn
    , pattern StmtDeadlineRule
    , pattern StmtIssue
    , pattern StmtIssueElement
    , pattern StmtRuleset
    , pattern StmtSourceBundle
    , pattern StmtSourceLocator
    , pattern StmtSource
    , pattern StmtTimeline
    , pattern StmtType
    , pattern StmtWhile
    , StmtNode(..)
    , TimelineDecl(..)
    , TypeDecl(..)
    , WhileDecl(..)
    ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Euclid.Model.Types (BinaryOp(..), RelationshipTemporalRule(..), UnaryOp(..), SourceSpan, TypeField(..), Value(..), noSourceSpan)

data Quantifier
    = QuantifierForAll
    | QuantifierExists
    deriving (Eq, Show)

data Expr
    = ExprValue Value
    | ExprIdent Text
    | ExprList [Expr]
    | ExprRange Expr Expr
    | ExprQuantifier Quantifier Text Expr Expr
    | ExprIndex Expr Expr
    | ExprField Expr Text
    | ExprCall Expr [Expr]
    | ExprClosure [(Text, Text)] Expr
    | ExprBinary BinaryOp Expr Expr
    | ExprUnary UnaryOp Expr
    | ExprTemporalAccess Expr Text Expr -- obj.field @ time
    deriving (Eq, Show)

data TypeDecl = TypeDecl
    { typeDeclName :: Text
    , typeDeclParent :: Maybe Text
    , typeDeclFields :: [TypeField]
    , typeDeclMeta :: Map Text Expr
    }
    deriving (Eq, Show)

data TimelineDecl = TimelineDecl
    { timelineDeclName :: Text
    , timelineDeclKind :: Maybe Expr
    , timelineDeclStart :: Expr
    , timelineDeclEnd :: Expr
    , timelineDeclParent :: Maybe Text
    , timelineDeclJurisdiction :: Maybe Expr
    , timelineDeclCourt :: Maybe Expr
    , timelineDeclProcedure :: Maybe Expr
    , timelineDeclForkFrom :: Maybe (Text, Expr)
    , timelineDeclMergeInto :: Maybe (Text, Expr)
    , timelineDeclLoopCount :: Maybe Expr
    }
    deriving (Eq, Show)

data SourceDecl = SourceDecl
    { sourceDeclName :: Text
    , sourceDeclKind :: Text
    , sourceDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data SourceBundleDecl = SourceBundleDecl
    { sourceBundleDeclName :: Text
    , sourceBundleDeclSources :: [Text]
    , sourceBundleDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data SourceLocatorDecl = SourceLocatorDecl
    { sourceLocatorDeclName :: Text
    , sourceLocatorDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data RulesetDecl = RulesetDecl
    { rulesetDeclName :: Text
    , rulesetDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data DeadlineRuleDecl = DeadlineRuleDecl
    { deadlineRuleDeclName :: Text
    , deadlineRuleDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data LegalIssueDecl = LegalIssueDecl
    { legalIssueDeclName :: Text
    , legalIssueDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data IssueElementDecl = IssueElementDecl
    { issueElementDeclName :: Text
    , issueElementDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data AppearanceDecl = AppearanceDecl
    { appearanceDeclTimeline :: Text
    , appearanceDeclStart :: Expr
    , appearanceDeclEnd :: Expr
    }
    deriving (Eq, Show)

data StateChangeDecl = StateChangeDecl
    { stateChangeDeclTime :: Expr
    , stateChangeDeclFields :: Map Text Expr
    }
    deriving (Eq, Show)

data AnnotationDecl = AnnotationDecl
    { annotationDeclNote :: Maybe Expr
    , annotationDeclSource :: Maybe Expr
    , annotationDeclConfidence :: Maybe Expr
    , annotationDeclTags :: [Expr]
    }
    deriving (Eq, Show)

data EntityDecl = EntityDecl
    { entityDeclName :: Text
    , entityDeclType :: Maybe Text
    , entityDeclFields :: Map Text Expr
    , entityDeclAppearances :: [AppearanceDecl]
    , entityDeclStateChanges :: [StateChangeDecl]
    , entityDeclAnnotation :: AnnotationDecl
    , entityDeclRecurrence :: Maybe Expr -- e.g. ExprCall "every" [interval]
    , entityDeclSkip :: [Expr]
    }
    deriving (Eq, Show)

data ViewDecl = ViewDecl
    { viewDeclName :: Text
    , viewDeclTimelines :: [Text]
    , viewDeclFilter :: Maybe Text
    , viewDeclTimeRange :: Maybe (Expr, Expr)
    , viewDeclHighlight :: [Text]
    }
    deriving (Eq, Show)

data ScenarioDecl = ScenarioDecl
    { scenarioDeclName :: Text
    , scenarioDeclForkFrom :: Maybe Text -- timeline to fork from
    , scenarioDeclBody :: [Stmt]
    }
    deriving (Eq, Show)

data ConstraintDecl = ConstraintDecl
    { constraintDeclName :: Text
    , constraintDeclBody :: [Stmt]
    }
    deriving (Eq, Show)

data CausalDeclKind = CausalDeclNone | CausalDeclCauses | CausalDeclEnables
    deriving (Eq, Show)

data RelationshipDecl = RelationshipDecl
    { relationshipDeclSource :: Text
    , relationshipDeclLabel :: Maybe Text
    , relationshipDeclTarget :: Text
    , relationshipDeclDirected :: Bool
    , relationshipDeclCausalKind :: CausalDeclKind
    , relationshipDeclTemporalScope :: Maybe (Expr, Expr)
    }
    deriving (Eq, Show)

data RelationshipTypeDecl = RelationshipTypeDecl
    { relationshipTypeDeclName :: Text
    , relationshipTypeDeclSources :: [Text]
    , relationshipTypeDeclTargets :: [Text]
    , relationshipTypeDeclTemporalRule :: Maybe RelationshipTemporalRule
    , relationshipTypeDeclRequired :: Bool
    , relationshipTypeDeclMinInbound :: Maybe Expr
    , relationshipTypeDeclMaxInbound :: Maybe Expr
    , relationshipTypeDeclMinOutbound :: Maybe Expr
    , relationshipTypeDeclMaxOutbound :: Maybe Expr
    }
    deriving (Eq, Show)

data LetDecl = LetDecl
    { letName :: Text
    , letMutable :: Bool
    , letTypeAnnotation :: Maybe Text
    , letValue :: Expr
    }
    deriving (Eq, Show)

data ForIterable
    = ForRange Expr Expr
    | ForList [Expr]
    | ForExpr Expr
    deriving (Eq, Show)

data ForDecl = ForDecl
    { forVar :: Text
    , forIterable :: ForIterable
    , forBody :: [Stmt]
    }
    deriving (Eq, Show)

data RepeatDecl = RepeatDecl
    { repeatCount :: Expr
    , repeatBody :: [Stmt]
    }
    deriving (Eq, Show)

data WhileDecl = WhileDecl
    { whileCondition :: Expr
    , whileBody :: [Stmt]
    }
    deriving (Eq, Show)

data FnDecl = FnDecl
    { fnName :: Text
    , fnParams :: [(Text, Text)]
    , fnReturnType :: Maybe Text
    , fnBody :: [Stmt]
    }
    deriving (Eq, Show)

data IfDecl = IfDecl
    { ifCondition :: Expr
    , ifThenBlock :: [Stmt]
    , ifElseIfBlocks :: [(Expr, [Stmt])]
    , ifElseBlock :: Maybe [Stmt]
    }
    deriving (Eq, Show)

data MatchPattern
    = MatchPatternValue Value
    | MatchPatternBind Text
    | MatchPatternWildcard
    deriving (Eq, Show)

data MatchArm = MatchArm
    { matchArmPattern :: MatchPattern
    , matchArmBody :: [Stmt]
    }
    deriving (Eq, Show)

data MatchDecl = MatchDecl
    { matchSubject :: Expr
    , matchArms :: [MatchArm]
    }
    deriving (Eq, Show)

data StmtNode
    = StmtTypeNode TypeDecl
    | StmtSourceNode SourceDecl
    | StmtSourceBundleNode SourceBundleDecl
    | StmtSourceLocatorNode SourceLocatorDecl
    | StmtRulesetNode RulesetDecl
    | StmtDeadlineRuleNode DeadlineRuleDecl
    | StmtIssueNode LegalIssueDecl
    | StmtIssueElementNode IssueElementDecl
    | StmtTimelineNode TimelineDecl
    | StmtEntityNode EntityDecl
    | StmtRelationshipNode RelationshipDecl
    | StmtRelationshipTypeNode RelationshipTypeDecl
    | StmtConstraintNode ConstraintDecl
    | StmtViewNode ViewDecl
    | StmtScenarioNode ScenarioDecl
    | StmtImportNode Text
    | StmtLetNode LetDecl
    | StmtForNode ForDecl
    | StmtRepeatNode RepeatDecl
    | StmtWhileNode WhileDecl
    | StmtFunctionNode FnDecl
    | StmtIfNode IfDecl
    | StmtMatchNode MatchDecl
    | StmtReturnNode (Maybe Expr)
    | StmtAssignNode Text Expr
    | StmtExprNode Expr
    deriving (Eq, Show)

data Stmt = StmtData
    { stmtSpan :: SourceSpan
    , stmtNode :: StmtNode
    }
    deriving (Show)

instance Eq Stmt where
    left == right = stmtNode left == stmtNode right

pattern StmtType :: TypeDecl -> Stmt
pattern StmtType decl <- StmtData _ (StmtTypeNode decl)
  where
    StmtType decl = StmtData noSourceSpan (StmtTypeNode decl)

pattern StmtSource :: SourceDecl -> Stmt
pattern StmtSource decl <- StmtData _ (StmtSourceNode decl)
  where
    StmtSource decl = StmtData noSourceSpan (StmtSourceNode decl)

pattern StmtSourceBundle :: SourceBundleDecl -> Stmt
pattern StmtSourceBundle decl <- StmtData _ (StmtSourceBundleNode decl)
  where
    StmtSourceBundle decl = StmtData noSourceSpan (StmtSourceBundleNode decl)

pattern StmtSourceLocator :: SourceLocatorDecl -> Stmt
pattern StmtSourceLocator decl <- StmtData _ (StmtSourceLocatorNode decl)
  where
    StmtSourceLocator decl = StmtData noSourceSpan (StmtSourceLocatorNode decl)

pattern StmtRuleset :: RulesetDecl -> Stmt
pattern StmtRuleset decl <- StmtData _ (StmtRulesetNode decl)
  where
    StmtRuleset decl = StmtData noSourceSpan (StmtRulesetNode decl)

pattern StmtDeadlineRule :: DeadlineRuleDecl -> Stmt
pattern StmtDeadlineRule decl <- StmtData _ (StmtDeadlineRuleNode decl)
  where
    StmtDeadlineRule decl = StmtData noSourceSpan (StmtDeadlineRuleNode decl)

pattern StmtIssue :: LegalIssueDecl -> Stmt
pattern StmtIssue decl <- StmtData _ (StmtIssueNode decl)
  where
    StmtIssue decl = StmtData noSourceSpan (StmtIssueNode decl)

pattern StmtIssueElement :: IssueElementDecl -> Stmt
pattern StmtIssueElement decl <- StmtData _ (StmtIssueElementNode decl)
  where
    StmtIssueElement decl = StmtData noSourceSpan (StmtIssueElementNode decl)

pattern StmtTimeline :: TimelineDecl -> Stmt
pattern StmtTimeline decl <- StmtData _ (StmtTimelineNode decl)
  where
    StmtTimeline decl = StmtData noSourceSpan (StmtTimelineNode decl)

pattern StmtEntity :: EntityDecl -> Stmt
pattern StmtEntity decl <- StmtData _ (StmtEntityNode decl)
  where
    StmtEntity decl = StmtData noSourceSpan (StmtEntityNode decl)

pattern StmtRelationship :: RelationshipDecl -> Stmt
pattern StmtRelationship decl <- StmtData _ (StmtRelationshipNode decl)
  where
    StmtRelationship decl = StmtData noSourceSpan (StmtRelationshipNode decl)

pattern StmtRelationshipType :: RelationshipTypeDecl -> Stmt
pattern StmtRelationshipType decl <- StmtData _ (StmtRelationshipTypeNode decl)
  where
    StmtRelationshipType decl = StmtData noSourceSpan (StmtRelationshipTypeNode decl)

pattern StmtConstraint :: ConstraintDecl -> Stmt
pattern StmtConstraint decl <- StmtData _ (StmtConstraintNode decl)
  where
    StmtConstraint decl = StmtData noSourceSpan (StmtConstraintNode decl)

pattern StmtView :: ViewDecl -> Stmt
pattern StmtView decl <- StmtData _ (StmtViewNode decl)
  where
    StmtView decl = StmtData noSourceSpan (StmtViewNode decl)

pattern StmtScenario :: ScenarioDecl -> Stmt
pattern StmtScenario decl <- StmtData _ (StmtScenarioNode decl)
  where
    StmtScenario decl = StmtData noSourceSpan (StmtScenarioNode decl)

pattern StmtImport :: Text -> Stmt
pattern StmtImport pathValue <- StmtData _ (StmtImportNode pathValue)
  where
    StmtImport pathValue = StmtData noSourceSpan (StmtImportNode pathValue)

pattern StmtLet :: LetDecl -> Stmt
pattern StmtLet decl <- StmtData _ (StmtLetNode decl)
  where
    StmtLet decl = StmtData noSourceSpan (StmtLetNode decl)

pattern StmtFor :: ForDecl -> Stmt
pattern StmtFor decl <- StmtData _ (StmtForNode decl)
  where
    StmtFor decl = StmtData noSourceSpan (StmtForNode decl)

pattern StmtRepeat :: RepeatDecl -> Stmt
pattern StmtRepeat decl <- StmtData _ (StmtRepeatNode decl)
  where
    StmtRepeat decl = StmtData noSourceSpan (StmtRepeatNode decl)

pattern StmtWhile :: WhileDecl -> Stmt
pattern StmtWhile decl <- StmtData _ (StmtWhileNode decl)
  where
    StmtWhile decl = StmtData noSourceSpan (StmtWhileNode decl)

pattern StmtFunction :: FnDecl -> Stmt
pattern StmtFunction decl <- StmtData _ (StmtFunctionNode decl)
  where
    StmtFunction decl = StmtData noSourceSpan (StmtFunctionNode decl)

pattern StmtIf :: IfDecl -> Stmt
pattern StmtIf decl <- StmtData _ (StmtIfNode decl)
  where
    StmtIf decl = StmtData noSourceSpan (StmtIfNode decl)

pattern StmtMatch :: MatchDecl -> Stmt
pattern StmtMatch decl <- StmtData _ (StmtMatchNode decl)
  where
    StmtMatch decl = StmtData noSourceSpan (StmtMatchNode decl)

pattern StmtReturn :: Maybe Expr -> Stmt
pattern StmtReturn maybeExpr <- StmtData _ (StmtReturnNode maybeExpr)
  where
    StmtReturn maybeExpr = StmtData noSourceSpan (StmtReturnNode maybeExpr)

pattern StmtAssign :: Text -> Expr -> Stmt
pattern StmtAssign name expr <- StmtData _ (StmtAssignNode name expr)
  where
    StmtAssign name expr = StmtData noSourceSpan (StmtAssignNode name expr)

pattern StmtExpr :: Expr -> Stmt
pattern StmtExpr expr <- StmtData _ (StmtExprNode expr)
  where
    StmtExpr expr = StmtData noSourceSpan (StmtExprNode expr)

{-# COMPLETE
    StmtType,
    StmtSource,
    StmtSourceBundle,
    StmtSourceLocator,
    StmtRuleset,
    StmtDeadlineRule,
    StmtIssue,
    StmtIssueElement,
    StmtTimeline,
    StmtEntity,
    StmtRelationship,
    StmtRelationshipType,
    StmtConstraint,
    StmtView,
    StmtScenario,
    StmtImport,
    StmtLet,
    StmtFor,
    StmtRepeat,
    StmtWhile,
    StmtFunction,
    StmtIf,
    StmtMatch,
    StmtReturn,
    StmtAssign,
    StmtExpr
    #-}

data Program = ProgramData
    { programFile :: FilePath
    , programStatements :: [Stmt]
    }
    deriving (Show)

instance Eq Program where
    left == right = programStatements left == programStatements right

pattern Program :: [Stmt] -> Program
pattern Program statements <- ProgramData _ statements
  where
    Program statements = ProgramData "<unknown>" statements

{-# COMPLETE Program #-}
