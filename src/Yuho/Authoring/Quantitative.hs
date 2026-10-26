{-# LANGUAGE OverloadedStrings #-}
-- | Opt-in quantitative source builders. The shared checker/executor and public
-- dependency facade retain scopes, sources, exact results, publication/replay.
module Yuho.Authoring.Quantitative
  ( QType(..), QExpr(..), QItem(..), QValue(..), quantitativeHeader
  , scalarInput, derivedQuantity, suppliedQuantity, suppliedUnknown, inspectQuantitative
  , evaluateExactExpression
  ) where
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import qualified Data.Aeson as A
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Control.Monad (unless)
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Exception.Types (Truth(..))
import Yuho.Quantitative
import Yuho.Dependency.Types (DependencyDiagnostic(..),TechnicalValue(..))
import Yuho.Dependency.Run (DependencyExecution,quantitativeEvidence)
import Yuho.Surface.Token
import Yuho.Surface.Lexer (lexSource)

quantitativeHeader :: Text
quantitativeHeader="quantitative version \""<>quantitativeFormat<>"\";"
scalarInput :: Text -> QType -> Either DependencyDiagnostic Text
scalarInput name ty=do n<-word name;t<-typeText ty;pure ("scalar "<>n<>" type "<>t<>";")
derivedQuantity :: Text -> QType -> QExpr -> Either DependencyDiagnostic Text
derivedQuantity name ty expression=do
  n<-word name;t<-typeText ty;e<-render 0 expression
  pure ("derive "<>n<>" type "<>t<>" = "<>e<>";")
suppliedQuantity :: Text -> QValue -> Text -> Either DependencyDiagnostic Text
suppliedQuantity name value reason=do
  n<-word name;r<-quote reason
  v<-case value of
    QKnown QInteger x->pure ("integer "<>T.pack (show x))
    QKnown (QMoney c) x->do c'<-word c;pure ("money "<>c'<>" "<>T.pack (show x))
    QKnown (QCount d) x->do d'<-word d;pure ("count "<>d'<>" "<>T.pack (show x))
    QUnknown _ _->failure "use suppliedUnknown; its type is selected by the actual authored declaration"
    _->failure "date/enum supplied syntax retains the existing typed source contract"
  pure ("value "<>n<>" = "<>v<>" reason "<>r<>";")
suppliedUnknown :: Text -> Text -> Either DependencyDiagnostic Text
suppliedUnknown name reason=do n<-word name;r<-quote reason;pure ("value "<>n<>" = unresolved reason "<>r<>";")
inspectQuantitative :: DependencyExecution -> A.Value
inspectQuantitative=quantitativeEvidence

-- | Pure mathematical SDK reduction with explicit caller-provided filter
-- values. It creates no legal observation, file authority or assessment claim.
-- Source-backed workflows instead use the public dependency checker/executor.
evaluateExactExpression :: Text -> QType -> QExpr -> [(Text,QValue)] -> [(Text,TechnicalValue)]
  -> Either DependencyDiagnostic QValue
evaluateExactExpression output ty expression supplied filters=do
  unless (length filters==S.size (S.fromList (map fst filters)))
    (failure "duplicate caller filter identity")
  unless (length supplied<=256 && length filters<=256)
    (failure "caller environment exceeds 256 inputs or filters")
  mapM_ word (output:map fst supplied++map fst filters)
  let site n=QSite "<in-memory SDK object>" 0 0 0 0 n
      typ v=case v of QKnown t _->t;QUnknown t _->t
      core v=case v of
        QKnown (QMoney c) n->K.MoneyValue c n
        QKnown _ n->K.IntegerValue n
        QUnknown t rs->K.ScalarUnresolved (T.intercalate "; " rs) (case t of QMoney c->K.MoneyType c;_->K.IntegerType)
      inputs=[QInput i (typ v) (core v) "explicit caller input; no source file claim" (site i) "caller environment" (site i) | (i,v)<-supplied]
      definition=QDefinition output ty expression (site output) [output] quantitativeFormat Nothing [] [] []
      program=K.TypedFiniteProgram "sdk-mathematical-control" [] [] [] [] [] [(i,K.AllExpr []) | (i,_)<-filters] [] [] [] [] [] M.empty [] []
      convert e=Left (DependencyDiagnostic (qFailureCode e) (qFailureMessage e) (maybe [] (:[]) (qFailureOutput e)) Nothing [])
  _<-either convert Right (checkQuantitative program (M.fromList ((output,ty):[(i,typ v) | (i,v)<-supplied])) inputs [definition])
  let condition i=case lookup i filters of
        Just s->Right ((case s of Satisfied->TrueValue;NotSatisfied->FalseValue;Unresolved->UnresolvedValue),[])
        Nothing->qError "QMISSING" ("missing caller filter "<>i)
  fst <$> either convert Right (reduceExact ty output (M.fromList supplied) condition expression)
typeText :: QType -> Either DependencyDiagnostic Text
typeText ty=case ty of
  QInteger->pure "integer";QMoney c->("money "<>) <$> word c
  QCount d->("count "<>) <$> word d;QDate->pure "date";QEnum n->("enum "<>) <$> word n
render :: Int -> QExpr -> Either DependencyDiagnostic Text
render depth _ | depth>16=failure "quantitative expression depth exceeds16"
render depth e=case e of
  QRef i->wrap "ref" <$> word i
  QConstant QInteger n->pure (wrap "integer" (T.pack (show n)))
  QConstant (QMoney c) n->do c'<-word c;pure (wrap "money" (c'<>","<>T.pack (show n)))
  QConstant (QCount d) n->do d'<-word d;pure (wrap "count-value" (d'<>","<>T.pack (show n)))
  QConstant _ _->failure "date/enum arithmetic is unsupported"
  QScale n x->do x'<-render (depth+1) x;pure (wrap "scale" (T.pack (show n)<>","<>x'))
  QSum xs->do
    ys<-traverse (\(QItem i x c)->do
      i'<-word i
      x'<-render (depth+1) x
      c'<-traverse word c
      pure ("item "<>i'<>" value "<>x'<>maybe "" (" when "<>) c')) xs
    pure (wrap "sum" (T.intercalate "," ys))
  QCountItems xs->do
    ys<-traverse (\(i,c)->do i'<-word i;c'<-word c;pure ("item "<>i'<>" when "<>c')) xs
    pure (wrap "count" (T.intercalate "," ys))
 where wrap n x=n<>"("<>x<>")"
word :: Text -> Either DependencyDiagnostic Text
word text=case lexSource "<quantitative-sdk>" (U.encodeUtf8 text) of
  Right [t,end] | tokenKind t==WordToken,tokenKind end==EndToken,tokenText t==text,T.length text<=128->Right text
  _->failure "expected one supported source identifier"
quote :: Text -> Either DependencyDiagnostic Text
quote text | T.null (T.strip text) || T.any (`elem` ['"','\\','\n','\r','\0']) text=failure "reason must be nonblank and contain no unsupported string escapes"
           | otherwise=Right ("\""<>text<>"\"")
failure :: Text -> Either DependencyDiagnostic a
failure message=Left (DependencyDiagnostic "QSOURCE" message [] Nothing [])
