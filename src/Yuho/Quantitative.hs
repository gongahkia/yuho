{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Versioned exact reductions above the unchanged typed-finite kernel.
-- This module is the sole arithmetic implementation used by source and SDK.
module Yuho.Quantitative where

import Prelude hiding (reads)

import Control.Monad (foldM,unless,when)
import qualified Data.Aeson as A
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Data.List (sort,nub)
import Data.Text (Text)
import qualified Data.Text as T
import GHC.Generics (Generic)
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Exception.Types (Truth(..))

quantitativeFormat :: Text
quantitativeFormat="yuho.quantitative/v0.1-experimental"

data QType = QInteger | QMoney Text | QCount Text | QDate | QEnum Text
  deriving (Eq,Ord,Show,Generic)
instance A.ToJSON QType
data QExpr = QRef Text | QConstant QType Integer | QSum [QItem]
  | QScale Integer QExpr | QCountItems [(Text,Text)] deriving (Eq,Show,Generic)
instance A.ToJSON QExpr where
  toJSON e=A.object (case e of
    QRef i->["operation" A..= ("ref"::Text),"scalar" A..= i]
    QConstant t n->["operation" A..= ("constant"::Text),"type" A..= t,"integer" A..= T.pack (show n)]
    QScale n x->["operation" A..= ("scale"::Text),"factor" A..= T.pack (show n),"operand" A..= x]
    QSum xs->["operation" A..= ("sum"::Text),"items" A..= xs]
    QCountItems xs->["operation" A..= ("count"::Text),"items" A..=
      [A.object ["identity" A..= i,"condition" A..= c] | (i,c)<-xs]])
data QItem = QItem Text QExpr (Maybe Text) deriving (Eq,Show,Generic)
instance A.ToJSON QItem where
  toJSON (QItem i e c)=A.object ["identity" A..= i,"value" A..= e,"condition" A..= c]
data QSite = QSite { qSource :: FilePath, qLine :: Int, qColumn :: Int
  , qStart :: Int, qEnd :: Int, qToken :: Text } deriving (Eq,Show,Generic)
instance A.ToJSON QSite
data QDefinition = QDefinition
  { qName :: Text, qType :: QType, qExpression :: QExpr, qSite :: QSite
  , qDefinitionKey :: [Text], qDefinitionVersion :: Text
  , qUseSite :: Maybe QSite, qSignatures :: [(Text,QType)]
  , qInputOrigins :: [(Text,QSite)], qFilterOrigins :: [(Text,QSite)] }
  deriving (Eq,Show,Generic)
instance A.ToJSON QDefinition
data QInput = QInput
  { qInputName :: Text, qInputType :: QType, qInputValue :: K.ScalarValue
  , qInputReason :: Text, qInputSite :: QSite, qInputSnapshot :: Text
  , qInputDeclaration :: QSite }
  deriving (Eq,Show)
instance A.ToJSON QInput where
  toJSON i=A.object ["name" A..= qInputName i,"type" A..= qInputType i
    ,"value" A..= scalarRecord (qInputValue i),"reason" A..= qInputReason i
    ,"source" A..= qInputSite i,"snapshot" A..= qInputSnapshot i,"declaration" A..= qInputDeclaration i
    ,"origin" A..= ("externally supplied; not a derived observation"::Text)]
data QValue = QKnown QType Integer | QUnknown QType [Text] deriving (Eq,Show,Generic)
instance A.ToJSON QValue where
  toJSON (QKnown t v)=A.object ["type" A..= t,"state" A..= ("known_exact"::Text),"integer" A..= T.pack (show v)]
  toJSON (QUnknown t rs)=A.object ["type" A..= t,"state" A..= ("explicitly_unresolved"::Text),"reasons" A..= rs]
data QPlan = QPlan { qDefinitions :: [QDefinition], qInputs :: [QInput]
  , qTypes :: M.Map Text QType, qOrder :: [Text], qConditions :: [(Text,QSite)] } deriving (Eq,Show,Generic)
instance A.ToJSON QPlan
data QStep = QStep
  { qOutput :: Text, qPath :: [Int], qOperation :: Text, qResult :: QValue
  , qOperands :: [QValue], qItems :: [(Text,Text)], qReads :: [K.FiniteInput]
  , qFilterReads :: [(Text,[K.FiniteRead])], qNode :: QExpr } deriving (Eq,Show)
instance A.ToJSON QStep where
  toJSON s=A.object ["output" A..= qOutput s,"path" A..= qPath s
    ,"operation" A..= qOperation s,"expression" A..= qNode s,"result" A..= qResult s,"operands" A..= qOperands s
    ,"items" A..= qItems s,"contributing_inputs" A..= map inputRecord (qReads s)
    ,"filters" A..= [A.object ["requirement" A..= name,"actual_reads" A..= map readRecord rs]
                      | (name,rs)<-qFilterReads s]]
data QExecution = QExecution { qCheckedPlan :: QPlan, qValues :: M.Map Text QValue
  , qSteps :: [QStep] } deriving (Eq,Show)
instance A.ToJSON QExecution where
  toJSON e=A.object ["format" A..= quantitativeFormat,"evaluation" A..= ("evaluated"::Text)
    ,"plan" A..= qCheckedPlan e,"values" A..= qValues e,"steps" A..= qSteps e
    ,"notice" A..= ("Exact technical derivations; calculated values are not independent supplied facts."::Text)]

scalarRecord :: K.ScalarValue -> A.Value
scalarRecord v=case v of
  K.IntegerValue n->A.object ["integer" A..= T.pack (show n)]
  K.MoneyValue c n->A.object ["currency" A..= c,"minor_units" A..= T.pack (show n)]
  K.DateValue d->A.object ["date" A..= show d]
  K.EnumValue t x->A.object ["enum" A..= t,"member" A..= x]
  K.ScalarUnresolved r _->A.object ["unresolved" A..= r]
inputRecord :: K.FiniteInput -> A.Value
inputRecord x=case x of
  K.ScalarInput i->A.object ["kind" A..= ("scalar"::Text),"identity" A..= i]
  K.RequirementInput i->A.object ["kind" A..= ("requirement"::Text),"identity" A..= i]
  K.GroundInput f->A.object ["kind" A..= ("ground_application"::Text)
    ,"predicate" A..= K.groundPredicate f,"arguments" A..= K.groundArguments f
    ,"classification" A..= K.truthName (K.groundStatus f),"reason" A..= K.groundReason f]
readRecord :: K.FiniteRead -> A.Value
readRecord r=A.object ["root" A..= K.readRoot r,"path" A..= K.readPath r
  ,"bindings" A..= K.readBindings r,"kind" A..= K.readKind r
  ,"status" A..= K.truthName (K.readStatus r),"inputs" A..= map inputRecord (K.readInputs r)]

data QFailure = QFailure { qFailureCode :: Text, qFailureMessage :: Text, qFailureOutput :: Maybe Text } deriving (Eq,Show)
qError :: Text -> Text -> Either QFailure a
qError c m=Left (QFailure c m Nothing)
annotate :: Text -> Either QFailure a -> Either QFailure a
annotate name=either (\e->Left e {qFailureOutput=Just name}) Right
bounded :: Integer -> Bool
bounded n=abs n<2^(4096::Int)
numeric :: QType -> Bool
numeric QInteger=True
numeric (QMoney c)=T.length c==3 && T.all (`elem` ['A'..'Z']) c
numeric (QCount d)=not (T.null (T.strip d)) && T.length d<=128
numeric _=False
validNumber :: QType -> Integer -> Bool
validNumber t n=numeric t && bounded n && (t==QInteger || n>=0)

-- | Checking performs no arithmetic reduction or filter evaluation.
checkQuantitative :: K.TypedFiniteProgram -> M.Map Text QType -> [QInput] -> [QDefinition]
  -> Either QFailure QPlan
checkQuantitative program types inputs definitions=do
  when (length definitions>64) (qError "QLIMIT" "at most 64 derived scalars")
  unique "derived writer" (map qName definitions)
  unique "supplied input" (map qInputName inputs)
  let outputs=S.fromList (map qName definitions)
  when (any ((`S.member` outputs) . qInputName) inputs) (qError "QWRITER" "a derived output cannot be supplied")
  mapM_ (\i->do
    unless (not (T.null (T.strip (qInputReason i))) && T.length (qInputReason i)<=4096)
      (qError "QREASON" ("input reason must be nonblank and <=4096 characters: "<>qInputName i))
    case qInputValue i of
      K.IntegerValue n->unless (validNumber (qInputType i) n) (qError "QLIMIT" "integer/count input outside admitted sign/magnitude")
      K.MoneyValue _ n->unless (validNumber (qInputType i) n) (qError "QLIMIT" "money input outside admitted sign/magnitude")
      _->pure ()) inputs
  deps<-traverse (checkDefinition outputs) definitions
  when (sum (map (nodes . qExpression) definitions)>2048) (qError "QLIMIT" "at most 2048 quantitative AST nodes")
  order<-topological (sort (map qName definitions)) (M.fromList deps)
  let domains=M.fromListWith (+) [(t,1::Integer) | K.EntityDecl _ t<-K.finiteEntities program]
      cost seen e=1+case e of
        K.ReferenceExpr i | i `S.member` seen->16385
          | otherwise->maybe 16385 (cost (S.insert i seen)) (lookup i (K.finiteRequirements program))
        K.ForallExpr _ t x->M.findWithDefault 0 t domains*cost seen x
        K.ExistsExpr _ t x->M.findWithDefault 0 t domains*cost seen x
        _->sum (map (cost seen) (children e))
      allRequirementsCost=sum [cost (S.singleton i) e | (i,e)<-K.finiteRequirements program]
      filters e=case e of
        QSum xs->sum [filters x+maybe 0 (const 1) c | QItem _ x c<-xs]
        QCountItems xs->toInteger (length xs)
        QScale _ x->filters x
        _->0
      work=sum [toInteger (nodes (qExpression d))+filters (qExpression d)*allRequirementsCost | d<-definitions]
  when (work>16384) (qError "QLIMIT" "expanded quantitative/filter read work exceeds 16384")
  mapM_ checkComparisons (map snd (K.finiteRequirements program)++map K.ruleBody (K.finiteRules program))
  pure (QPlan definitions inputs types order [])
  where
    unique label xs=unless (length xs==S.size (S.fromList xs)) (qError "QWRITER" ("duplicate "<>label))
    checkDefinition outputs d=annotate (qName d) $ do
      unless (qDefinitionVersion d==quantitativeFormat) (qError "QFORMAT" "an authored derivation requires the exact quantitative version")
      unless (M.lookup (qName d) types==Just (qType d) && numeric (qType d)) (qError "QTYPE" "derived output type is not an admitted quantity")
      mapM_ (\(i,t)->unless (M.lookup i types==Just t) (qError "QTYPE" ("authored scalar signature differs at "<>i))) (qSignatures d)
      checkExpr (qType d) 0 (qExpression d)
      refs<-exprRefs S.empty (qExpression d)
      pure (qName d,filter (`S.member` outputs) (nub refs))
    checkExpr :: QType -> Int -> QExpr -> Either QFailure ()
    checkExpr t depth e=do
      when (depth>16) (qError "QLIMIT" "quantitative expression depth exceeds 16")
      case e of
        QRef i->unless (M.lookup i types==Just t) (qError "QTYPE" ("unknown or incompatible scalar "<>i))
        QConstant ty n->unless (ty==t && validNumber ty n) (qError "QTYPE" "incompatible/out-of-bounds exact constant")
        QScale factor child->do
          unless (bounded factor && (t==QInteger || factor>=0)) (qError "QTYPE" "invalid dimensionless integer factor")
          checkExpr t (depth+1) child
        QSum xs->do
          when (length xs>256) (qError "QLIMIT" "sum exceeds 256 identified items")
          unique "aggregate item" [i | QItem i _ _<-xs]
          mapM_ (\(QItem _ x condition)->checkExpr t (depth+1) x>>mapM_ filterRefs condition>>pure ()) xs
        QCountItems xs->do
          case t of QCount domain | not (T.null domain)->pure ();_->qError "QTYPE" "count requires an explicit Count[domain] output"
          when (length xs>256) (qError "QLIMIT" "count exceeds 256 identified items")
          unique "count item" (map fst xs)
          mapM_ (filterRefs . snd) xs>>pure ()
    exprRefs seen e=case e of
      QRef i->Right [i];QConstant {}->Right []
      QScale _ x->exprRefs seen x
      QSum xs->concat <$> traverse (\(QItem _ x c)->(++) <$> exprRefs seen x <*> maybe (Right []) (conditionRefs seen) c) xs
      QCountItems xs->concat <$> traverse (conditionRefs seen . snd) xs
    filterRefs=conditionRefs S.empty
    conditionRefs seen i
      | i `S.member` seen=qError "QCYCLE" ("cyclic inclusion requirement "<>i)
      | otherwise=maybe (qError "QNAME" ("unknown inclusion requirement "<>i))
          (finiteRefs (S.insert i seen)) (lookup i (K.finiteRequirements program))
    finiteRefs seen e=case e of
      K.ComparisonExpr _ l r u->Right (l:r:maybe [] (:[]) u)
      K.ReferenceExpr i->conditionRefs seen i
      _->concat <$> traverse (finiteRefs seen) (children e)
    checkComparisons e=do
      case e of
        K.ComparisonExpr _ l r u->do
          let ts=map (`M.lookup` types) (l:r:maybe [] (:[]) u)
          unless (case ts of first:rest->all (==first) rest;_->False) (qError "QTYPE" "comparison types/count domains must agree exactly")
        _->pure ()
      mapM_ checkComparisons (children e)
    topological [] _=Right []
    topological pending dependencies=case [i | i<-pending,null [d | d<-M.findWithDefault [] i dependencies,d `elem` pending]] of
      []->qError "QCYCLE" ("cyclic scalar/filter dependencies: "<>T.intercalate ", " pending)
      i:_->(i:) <$> topological (filter (/=i) pending) dependencies

children :: K.FiniteExpr -> [K.FiniteExpr]
children e=case e of
  K.AllExpr xs->xs;K.AnyExpr xs->xs;K.NotExpr x->[x];K.ForallExpr _ _ x->[x]
  K.ExistsExpr _ _ x->[x];K.CardinalityExpr _ _ xs->xs;_->[]
nodes :: QExpr -> Int
nodes e=1+case e of QScale _ x->nodes x;QSum xs->sum [nodes x | QItem _ x _<-xs];QCountItems xs->length xs;_->0

-- | Authoritative pure arithmetic. Unknowns propagate conservatively, including
-- zero factors. False inclusion excludes a value, never a missing-input check.
reduceExact :: QType -> Text -> M.Map Text QValue
  -> (Text -> Either QFailure (Truth,[K.FiniteRead])) -> QExpr -> Either QFailure (QValue,[QStep])
reduceExact expected output values condition=go []
  where
    go path expression=do
      (value,operands,items,reads,filters,steps,operation)<-case expression of
        QRef i->case M.lookup i values of
          Nothing->qError "QMISSING" ("missing exact scalar "<>i)
          Just v->Right (v,[],[],[K.ScalarInput i],[],[],"ref "<>i)
        QConstant t n->Right (QKnown t n,[],[],[],[],[],"constant")
        QScale factor e->do
          (v,ss)<-go (path++[0]) e
          let result=case v of QKnown t n->QKnown t (factor*n);QUnknown t rs->QUnknown t rs
          pure (result,[v],[],rootReads ss,[],ss,"scale "<>T.pack (show factor))
        QSum xs->do
          rows<-traverse (\(index,QItem identity e guard)->do
            (s,rs)<-maybe (Right (TrueValue,[])) condition guard
            (v,ss)<-go (path++[index]) e
            pure (identity,s,v,ss,[(n,rs) | Just n<-[guard]])) (zip [0..] xs)
          let included=[v | (_,s,v,_,_)<-rows,s/=FalseValue]
              reasons=S.toAscList (S.fromList (concat [unknownReasons v | v<-included]++["unresolved inclusion: "<>i | (i,UnresolvedValue,_,_,_)<-rows]))
              unknown=any (\v->case v of QUnknown {}->True;_->False) included
                || any (\(_,s,_,_,_)->s==UnresolvedValue) rows
              result=if not unknown then QKnown expected (sum [n | QKnown _ n<-included]) else QUnknown expected reasons
              filters=concat [fs | (_,_,_,_,fs)<-rows]
              reads=concat [rootReads ss | (_,s,_,ss,_)<-rows,s/=FalseValue]++concatMap (concatMap K.readInputs . snd) filters
          pure (result,map (\(_,_,v,_,_)->v) rows,[(i,K.truthName s) | (i,s,_,_,_)<-rows],reads,filters,concat [ss | (_,_,_,ss,_)<-rows],"identified sum")
        QCountItems xs->do
          rows<-traverse (\(i,c)->do (s,rs)<-condition c;pure (i,c,s,rs)) xs
          let unresolved=["unresolved inclusion: "<>i | (i,_,UnresolvedValue,_)<-rows]
              result=if null unresolved then QKnown expected (toInteger (length [() | (_,_,TrueValue,_)<-rows])) else QUnknown expected unresolved
          pure (result,[],[(i,K.truthName s) | (i,_,s,_)<-rows],concat [concatMap K.readInputs rs | (_,_,_,rs)<-rows],[(c,rs) | (_,c,_,rs)<-rows],[],"identified count")
      case value of
        QKnown t n->unless (t==expected && validNumber t n) (qError "QLIMIT" "computed intermediate exceeds type/sign/4096-bit bound")
        QUnknown t _->unless (t==expected) (qError "QTYPE" "runtime unknown type mismatch")
      pure (value,QStep output path operation value operands items reads filters expression:steps)
    rootReads []=[]
    rootReads (s:_)=qReads s
    unknownReasons (QUnknown _ rs)=rs
    unknownReasons _=[]

executeQuantitative :: K.TypedFiniteProgram -> QPlan -> Either QFailure (K.TypedFiniteProgram,QExecution)
executeQuantitative program plan=do
  initial<-traverse inputValue (M.fromList [(qInputName i,i) | i<-qInputs plan,numeric (qInputType i)])
  (values,steps)<-foldM step (initial,[]) (qOrder plan)
  let generated=M.fromList [(name,lower v) | (name,v)<-M.toAscList values,name `elem` qOrder plan]
  pure (program {K.finiteValues=M.union generated (K.finiteValues program)},QExecution plan values steps)
  where
    inputValue i=case qInputValue i of
      K.IntegerValue n->Right (QKnown (qInputType i) n)
      K.MoneyValue _ n->Right (QKnown (qInputType i) n)
      K.ScalarUnresolved reason _->Right (QUnknown (qInputType i) [qInputName i<>": "<>reason])
      _->qError "QTYPE" "non-numeric scalar used in arithmetic"
    lower v=case v of
      QKnown (QMoney c) n->K.MoneyValue c n
      QKnown _ n->K.IntegerValue n
      QUnknown t rs->K.ScalarUnresolved (T.intercalate "; " rs) (case t of QMoney c->K.MoneyType c;_->K.IntegerType)
    step (env,allSteps) name=do
      d<-maybe (qError "QNAME" "checked derivation disappeared") Right (lookup name [(qName x,x) | x<-qDefinitions plan])
      let condition ident=do
            reqs<-closure S.empty ident
            let p=program {K.finiteValues=M.union (M.map lower env) (K.finiteValues program)
                  ,K.finiteRequirements=reqs,K.finiteRules=[],K.finitePropositions=[]}
            (r,rs)<-either (qError "QOBSERVATION") Right (K.evaluateTypedFiniteObserved p)
            case [K.expressionStatus x | x<-K.finiteResultExpressions r,K.expressionLabel x==ident] of
              [v]->Right (v,[x | x<-rs,K.readRoot x==["expression",ident]])
              _->qError "QOBSERVATION" "inclusion produced no unique actual observation"
      (v,ss)<-annotate name (reduceExact (qType d) name env condition (qExpression d))
      pure (M.insert name v env,allSteps++ss)
    closure seen i
      | i `S.member` seen=Right []
      | otherwise=case lookup i (K.finiteRequirements program) of
          Nothing->qError "QNAME" ("unknown inclusion "<>i)
          Just e->do rest<-concat <$> traverse (closure (S.insert i seen)) (references e);pure (nub ((i,e):rest))
    references e=case e of K.ReferenceExpr i->[i];_->concatMap references (children e)

-- | Structural causal expansion, never a join against a printable input key.
quantitativeInputs :: QExecution -> [Text] -> [K.FiniteInput]
quantitativeInputs e=concatMap (walk S.empty)
  where
    walk seen i | i `S.member` seen=[]
    walk seen i=case [s | s<-qSteps e,qOutput s==i,null (qPath s)] of
      []->[K.ScalarInput i]
      [s]->concatMap (expand (S.insert i seen)) (qReads s)
      _->[] -- A checked single-writer plan cannot construct this case.
    expand seen (K.ScalarInput i)=walk seen i
    expand _ x=[x]
