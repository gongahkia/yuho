{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Dependency.Parser (parseDependencyProject) where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import Data.Text (Text)
import Yuho.Dependency.Types
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token
newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a,[Token]) }
instance Functor P where fmap f (P p) = P $ \s ts -> do (a,rest)<-p s ts; pure (f a,rest)
instance Applicative P where
  pure a = P $ \_ ts -> Right (a,ts)
  P f <*> P a = P $ \s ts -> do (g,rest)<-f s ts; (x,end)<-a s rest; pure (g x,end)
instance Monad P where P p >>= f = P $ \s ts -> do (a,rest)<-p s ts; runP (f a) s rest
peek :: P Token
peek = P $ \p ts -> case ts of
  t:_ -> Right (t,ts)
  [] -> at "DEPFORMAT" p (Token EndToken "" 1 1) "unexpected end of checked-project"
takeWhen :: (Token -> Bool) -> Text -> P Token
takeWhen test expected = P $ \p ts -> case ts of
  t:rest | test t -> Right (t,rest)
  t:_ -> at "DEPFORMAT" p t ("expected " <> expected)
  [] -> at "DEPFORMAT" p (Token EndToken "" 1 1) ("expected " <> expected)
keyword :: Text -> P Token
keyword value = takeWhen ((==value) . tokenText) value
word, string :: P Token
word = takeWhen ((==WordToken) . tokenKind) "identifier"
string = takeWhen ((==StringToken) . tokenKind) "quoted text"

parseDependencyProject :: FilePath -> BS.ByteString -> Either Diagnostic DependencyPlan
parseDependencyProject path bytes=lexSource path bytes >>= fmap fst . runP parser path
 where
  loc t=let prefix=BS.intercalate "\n" (take (tokenLine t-1) (BS.split 10 bytes))
            offset=(if tokenLine t==1 then 0 else BS.length prefix+1)+tokenColumn t-1
        in Just (Location path (tokenLine t) (tokenColumn t) offset (offset+BS.length (U.encodeUtf8 (tokenText t))))
  parser=do
    _<-keyword "checked-project"; i<-word; _<-keyword "version"; v<-string
    if tokenText v/=planFormat then P (\p _->at "DEPFORMAT" p v "unsupported checked-project version") else pure ()
    _<-keyword "{"
    declarations<-manyUntil "}" declaration
    _<-keyword "}"; _<-takeWhen ((==EndToken) . tokenKind) "end of source"
    pure (DependencyPlan (tokenText i) [o | DOrigin o<-declarations] [s | DScope s<-declarations]
      [c | DComponent c<-declarations] [b | DBinding b<-declarations] [c | DCandidate c<-declarations])
  declaration=do
    headToken<-word
    case tokenText headToken of
      "source"->do i<-word;_<-keyword "locator";l<-string;_<-keyword ";";pure (DOrigin (SourceOrigin (tokenText i) (tokenText l)))
      "scope"->do
        i<-word;_<-keyword "actor";a<-word;_<-keyword "context";c<-word
        t<-peek
        ca<-if tokenText t=="case" then do _<-keyword "case";ci<-word;_<-keyword "allegation";al<-word;pure (Just (tokenText ci),Just (tokenText al)) else pure (Nothing,Nothing)
        _<-keyword "{";entities<-manyUntil "}" (do _<-keyword "identity";e<-word;_<-keyword "nominal";n<-word;_<-keyword ";";pure (tokenText e,tokenText n));_<-keyword "}"
        pure (DScope (PlanScope (tokenText i) (tokenText a) (tokenText c) (fst ca) (snd ca) entities))
      "component"->do
        i<-word;_<-keyword "profile";p<-word;_<-keyword "model";m<-string
        t<-peek;sc<-if tokenText t=="scenario" then keyword "scenario" >> Just . T.unpack . tokenText <$> string else pure Nothing
        t2<-peek;entry<-if tokenText t2=="entry" then do _<-keyword "entry";k<-word;e<-word;pure (Just (tokenText k,tokenText e)) else pure Nothing
        _<-keyword "scope";s<-word;_<-keyword "{";maps<-manyUntil "}" mapping;_<-keyword "}";_<-keyword "rationale";r<-string;_<-keyword ";"
        pure (DComponent (PlanComponent (tokenText i) (tokenText p) (T.unpack (tokenText m)) sc entry (tokenText s)
          [(a,b) | ("nominal",a,b)<-maps] [(a,b) | ("entity",a,b)<-maps] (tokenText r) Nothing (loc i)))
      "bind"->do
        i<-word;_<-keyword "from";src<-port;_<-keyword "to";d<-word;_<-keyword ".";_<-keyword "condition";slot<-word
        (policy,rationale,refs)<-authorization
        _<-keyword ";"
        pure (DBinding (PlanBinding (tokenText i) src (tokenText d) (tokenText slot) policy rationale refs (loc i)))
      "candidate"->do
        i<-word;_<-keyword "scope";s<-word;_<-keyword "guard";g<-port;_<-keyword "mapping";pol<-string;_<-keyword "modality";modality<-word
        _<-keyword "rationale";r<-string;_<-keyword "refs";refs<-references
        _<-keyword "{";term<-penaltyTerm;_<-keyword "}"
        pure (DCandidate (PlanCandidate (tokenText i) (tokenText s) g (tokenText pol) (tokenText modality) (tokenText r) refs (DataTerm term) (loc i)))
      _->P (\p _->at "DEPFORMAT" p headToken "unsupported checked-project declaration")
  mapping=do
    k<-word
    if tokenText k `elem` ["nominal","entity"] then pure () else P (\p _->at "DEPFORMAT" p k "expected nominal or entity map")
    l<-word;_<-keyword "as";r<-word;_<-keyword ";";pure (tokenText k,tokenText l,tokenText r)
  port=do
    c<-word;_<-keyword ".";k<-word;i<-word
    category<-case tokenText k of
      "expression"->pure "typed.expression.truth";"proposition"->pure "typed.proposition.resolution"
      _->P (\p _->at "DEPCATEGORY" p k "only expression/proposition ports are admitted")
    pure (ObservationPort (tokenText c) category (tokenText i))
  authorization=do _<-keyword "mapping";p<-string;_<-keyword "rationale";r<-string;_<-keyword "refs";rs<-references;pure (tokenText p,tokenText r,rs)
  references=do i<-word;rest<-commas;pure (tokenText i:rest)
  commas=do t<-peek;if tokenText t=="," then keyword "," >> word >>= \i->(tokenText i:) <$> commas else pure []
  penaltyTerm=do
    k<-word;i<-word
    let spanValue=A.object ["start" A..= maybe 0 locationStart (loc k),"end" A..= maybe 0 locationEnd (loc i)
          ,"start_line" A..= tokenLine k,"start_col" A..= tokenColumn k,"end_line" A..= tokenLine i
          ,"end_col" A..= (tokenColumn i+T.length (tokenText i))]
        common kind=["kind" A..= (kind::Text),"term_id" A..= tokenText i,"span" A..= spanValue]
        endPoint fine=do t<-word
                         pure (if tokenText t `elem` ["not-stated","unbounded"] then A.object ["kind" A..= (if tokenText t=="not-stated" then "not_stated" else "unbounded"::Text)]
                           else A.object ["kind" A..= ("specified"::Text),"value" A..= (if fine then A.String (tokenText t) else case reads (T.unpack (tokenText t)) of [(n,"")]->A.toJSON (n::Integer);_->A.String (tokenText t))])
        bounds fine=do _<-keyword "minimum";l<-endPoint fine;_<-keyword "maximum";u<-endPoint fine;_<-keyword ";";pure ["minimum" A..= l,"maximum" A..= u]
    case tokenText k of
      "life-imprisonment"->keyword ";" >> pure (A.object (common "life_imprisonment"))
      "death"->keyword ";" >> pure (A.object (common "death"))
      "caning"->do bs<-bounds False;pure (A.object (common "caning"++bs))
      "fine"->do _<-keyword "currency";currency<-word;bs<-bounds True;pure (A.object (common "fine"++["currency" A..= tokenText currency]++bs))
      "term-imprisonment"->do _<-keyword "unit";u<-word;bs<-bounds False;pure (A.object (common "term_imprisonment"++["unit" A..= tokenText u]++bs))
      group | group `elem` ["all-of","exactly-one-of","one-or-more-of"] ->do
        _<-keyword "{";children<-manyUntil "}" penaltyTerm;_<-keyword "}"
        -- Group span covers all nested declarations, using the actual closing token.
        rest<-peek
        let start=maybe 0 locationStart (loc k);end=maybe start locationStart (loc rest)
            groupSpan=A.object ["start" A..= start,"end" A..= end,"start_line" A..= tokenLine k,"start_col" A..= tokenColumn k
              ,"end_line" A..= tokenLine rest,"end_col" A..= tokenColumn rest]
        pure (A.object ["kind" A..= T.replace "-" "_" group,"term_id" A..= tokenText i,"span" A..= groupSpan,"terms" A..= children])
      _->P (\p _->at "DEPUNSUPPORTED" p k "unsupported candidate term")

manyUntil :: Text -> P a -> P [a]
manyUntil end item=do t<-peek;if tokenText t==end then pure [] else do x<-item; (x:) <$> manyUntil end item

data Decl=DOrigin SourceOrigin | DScope PlanScope | DComponent PlanComponent | DBinding PlanBinding | DCandidate PlanCandidate
