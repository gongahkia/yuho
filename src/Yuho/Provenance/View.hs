{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Provenance.View where
import Control.Exception (IOException,try,evaluate)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.Aeson.Key as AK
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Data.Text (Text)
import qualified Data.Text as T
import Yuho.Provenance.Types
import Yuho.Dependency.Types (DependencyDiagnostic)
import Yuho.Dependency.Check (ensure,failure,encode)
import Yuho.Diagram.Types
import Yuho.Diagram.Encode
import Yuho.Surface.Publication (publishExport)

-- Opaque outside the public facade. A focus never mutates or executes evidence.
data Focus = Focus { focusProjection :: Text, focusRoot :: Maybe Text
  , focusIncludedNodes :: [Text], focusOmittedNodes :: [Text]
  , focusIncludedEdges :: [Text], focusOmittedEdges :: [Text] } deriving (Eq,Show)
instance A.ToJSON Focus where
  toJSON f=A.object ["format" A..= focusFormat,"projection" A..= focusProjection f
    ,"root" A..= focusRoot f,"included_nodes" A..= focusIncludedNodes f,"omitted_nodes" A..= focusOmittedNodes f
    ,"included_edges" A..= focusIncludedEdges f,"omitted_edges" A..= focusOmittedEdges f
    ,"rendered_nodes" A..= [A.object ["semantic_id" A..= i,"svg_id" A..= nativeSvgId i] | i<-focusIncludedNodes f]
    ,"notice" A..= ("Ancestors of selected result plus its downstream effects; omitted records remain in the complete projection. Eager read evidence does not assert operand decisiveness. No judicial finding or imposed sentence."::Text)]

focusProvenance :: Projection -> Maybe Text -> Either DependencyDiagnostic Focus
focusProvenance p selected=do
  ensure "PVFOCUS" (maybe [] (:[]) selected) "focus target absent from this exact projection"
    (maybe True (`S.member` allNodes) selected)
  let included=case selected of
        Nothing->allNodes
        Just root->closure True (S.singleton root) `S.union` closure False (S.singleton root)
      includedEdges=[edgeIdentity e | e<-edges p,from e `S.member` included,to e `S.member` included]
      edgeSet=S.fromList includedEdges
  pure (Focus (projectionIdentity p) selected (S.toAscList included) (S.toAscList (allNodes S.\\ included))
    includedEdges [edgeIdentity e | e<-edges p,edgeIdentity e `S.notMember` edgeSet])
 where
  allNodes=S.fromList (map identity (nodes p))
  closure backwards seeds=walk seeds seeds
   where
    adjacency=M.fromListWith S.union [(if backwards then to e else from e,S.singleton (if backwards then from e else to e)) | e<-edges p]
    walk visited pending=case S.minView pending of
      Nothing->visited
      Just (current,rest)->let fresh=M.findWithDefault S.empty current adjacency S.\\ visited
        in walk (S.union visited fresh) (S.union rest fresh)

validateProvenanceFocus :: Projection -> A.Value -> Either DependencyDiagnostic ()
validateProvenanceFocus p submitted=case A.fromJSON submitted :: A.Result (M.Map Text A.Value) of
  A.Error _->failure "PVFOCUS" [] "expected focus record"
  A.Success fields->do
    selected<-case M.lookup "root" fields of
      Just A.Null->Right Nothing
      Just (A.String t)->Right (Just t)
      _->failure "PVFOCUS" [] "focus root required"
    expected<-focusProvenance p selected
    ensure "PVFOCUS" [] "focus partition, endpoints or rendered identity differs from the exact projection" (A.toJSON expected==submitted)

provenanceGraph :: Projection -> Focus -> Either DependencyDiagnostic SemanticGraph
provenanceGraph p f=do
  validateProvenanceFocus p (A.toJSON f)
  ensure "PVLIMIT" [] "focused diagram exceeds 512 nodes or 2048 edges; select a narrower result; complete evidence is not truncated"
    (length (focusIncludedNodes f)<=512 && length (focusIncludedEdges f)<=2048)
  let ns=includedNodeSet f;es=includedEdgeSet f
  pure (SemanticGraph (projectionIdentity p) TraceView
    [ (GraphNode (identity n) (category n) (label n) (citation n) (state n) (boundary n))
        {graphNodeObservation=Just (CoreObservation (evaluation n) (state n) Nothing
          (if evaluation n=="not_evaluated" then Just "underlying component did not execute" else Nothing))}
      | n<-nodes p,identity n `S.member` ns]
    [GraphEdge (from e) (to e) (relationship e) (relationship e)
      | e<-edges p,edgeIdentity e `S.member` es]
    ("Typed provenance view: "<>T.pack (show (length (focusIncludedNodes f)))<>" included / "<>
      T.pack (show (length (focusOmittedNodes f)))<>" omitted nodes; "<>
      T.pack (show (length (focusIncludedEdges f)))<>" included / "<>T.pack (show (length (focusOmittedEdges f)))<>
      " omitted edges. Full records: provenance.json. Eager reads are not claims of semantic decisiveness; candidates are not imposed sentences."))

exportTypedProvenance :: Projection -> Maybe Text -> Either DependencyDiagnostic [(FilePath,BS.ByteString)]
exportTypedProvenance p selected=do
  f<-focusProvenance p selected
  graph<-provenanceGraph p f
  xml<-either (failure "PVXML" []) Right (encodeNativeSemanticGraphXml graph)
  let files=[("provenance.json",encode p),("focus.json",encode f),("view.json",encodeNativeSemanticGraph graph)
        ,("view.xml",xml),("view.svg",encodeNativeSvg graph)]
  ensure "PVLIMIT" [] "provenance view export exceeds 32 MiB; choose a narrower focus" (sum (map (BS.length . snd) files)<=33554432)
  pure files

publishTypedProvenance :: FilePath -> [(FilePath,BS.ByteString)] -> IO (Either DependencyDiagnostic ())
publishTypedProvenance out files=do
  attempted<-try (mapM_ (evaluate . BS.length . snd) files >> publishExport out files)
  pure $ case attempted of
    Left (e::IOException)->failure "PVPUBLISH" [T.pack out] (T.pack (show e))
    Right ()->Right ()

explainProvenance :: Projection -> Text -> Either DependencyDiagnostic A.Value
explainProvenance p target=do
  f<-focusProvenance p (Just target)
  let ns=includedNodeSet f;es=includedEdgeSet f
  pure (A.object ["format" A..= ("yuho.typed-explanation/v0.1-experimental"::Text)
    ,"projection" A..= projectionIdentity p,"mode" A..= projectionMode p,"authority" A..= projectionAuthority p
    ,"target" A..= target,"focus" A..= f
    ,"nodes" A..= [n | n<-nodes p,identity n `S.member` ns]
    ,"edges" A..= [e | e<-edges p,edgeIdentity e `S.member` es]
    ,"limitations" A..= domain])

-- Presentation uses actual typed fields; it never decodes the opaque identity.
valueAt :: Text -> A.Value -> A.Value
valueAt k (A.Object o)=maybe A.Null id (KM.lookup (AK.fromText k) o)
valueAt _ _=A.Null
textAt :: Text -> A.Value -> Maybe Text
textAt k v=case valueAt k v of A.String t->Just t;_->Nothing
boundary :: Node -> Maybe Text
boundary n=case scoped (valueAt "scope" (authority n))++scoped (valueAt "scope" (record n)) of
  []->textAt "boundary" (authority n)
  xs->Just (T.intercalate " | " xs)
 where
  scoped scope=[name<>" "<>v | (k,name)<-[("scopeActor","actor"),("scopeContext","context"),("scopeCase","case"),("scopeAllegation","allegation")],Just v<-[textAt k scope]]

citation :: Node -> Maybe Text
citation n=case textAt "qSource" (record n) of
  Nothing->Nothing
  Just file->Just (file<>":"<>number "qLine"<>":"<>number "qColumn")
 where number k=case valueAt k (record n) of A.Number v->T.pack (show (floor v::Integer));_->"?"

includedNodeSet, includedEdgeSet :: Focus -> S.Set Text
includedNodeSet=S.fromList . focusIncludedNodes
includedEdgeSet=S.fromList . focusIncludedEdges
