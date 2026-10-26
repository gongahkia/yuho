{-# LANGUAGE OverloadedStrings #-}
-- Only public interfaces. Projection validation tests semantic correspondence,
-- not merely structural endpoint existence or matching display labels.
module Main where
import Control.Monad (unless,forM_)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as M
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import qualified Data.Text as T
import System.Environment (getArgs)
import System.Directory (createDirectory)
import System.FilePath ((</>),takeExtension)
import Yuho.Authoring.Dependency
import Yuho.Authoring.Provenance
import Yuho.Surface.Dependency (loadDependencyProject)

require :: Show e => Either e a -> IO a
require=either (fail . show) pure
refuse :: Either e a -> IO ()
refuse (Left _)=pure ()
refuse (Right _)=fail "tampered provenance was accepted"
set :: A.Key -> A.Value -> A.Value -> A.Value
set k v (A.Object o)=A.Object (M.insert k v o)
set _ _ v=v

main :: IO ()
main=do
 [source,out]<-getArgs
 checked<-if takeExtension source==".json" then BS.readFile source >>= require . decodeDependencyDocument >>= require . checkDependencyPlan
   else loadDependencyProject source >>= require
 static<-require (projectStaticProvenance checked)
 unless (all ((/="evaluated") . evaluation) (nodes static)) (fail "static projection evaluated")
 execution<-require (executeDependencyPlan checked)
 p<-require (projectTypedProvenance execution)
 require (validateTypedProvenance execution (A.toJSON p))
 let ns=nodes p;es=edges p
 unless (not (null ns) && not (null es)) (fail "empty provenance")
 case (ns,es) of
  (first:second:_,firstEdge:_) ->do
    forM_ [set "nodes" (A.toJSON (map (\n->if identity n==identity first then set "record" (A.String "tampered observation") (A.toJSON n) else A.toJSON n) ns)) (A.toJSON p)
          ,set "nodes" (A.toJSON (first:ns)) (A.toJSON p)
          ,set "edges" (A.toJSON (set "from" (A.String (identity second)) (A.toJSON firstEdge):map A.toJSON (tail es))) (A.toJSON p)
          ,set "authority" (A.String "wrong snapshot") (A.toJSON p)] (refuse . validateTypedProvenance execution)
  _->fail "too small test"
 target<-case [identity n | n<-ns,category n=="expression_observation"] of
   x:_->pure x;_->fail "no actual expression"
 f<-require (focusProvenance p (Just target))
 require (validateProvenanceFocus p (A.toJSON f))
 refuse (validateProvenanceFocus p (set "omitted_nodes" (A.toJSON ([]::[T.Text])) (A.toJSON f)))
 refuse (focusProvenance p (Just "wrong-but-existing-source"))
 explanation<-require (explainProvenance p target)
 saved<-require (decodeDependencyArtifact (encodeDependencyArtifact (saveDependencyArtifact execution)))
 replay<-require (replayDependencyPlan saved)
 pp<-require (projectTypedProvenance replay)
 unless (A.toJSON pp==A.toJSON p) (fail "public replay projection differs")
 files<-require (exportTypedProvenance p Nothing)
 createDirectory out
 BS.writeFile (out</>"artifact.json") (encodeDependencyArtifact (saveDependencyArtifact execution))
 forM_ files $ \(name,bytes)->BS.writeFile (out</>name) bytes
 BS.writeFile (out</>"explanation.json") (BL.toStrict (A.encode explanation))
 putStrLn "public provenance SDK: static, exact correspondence, tamper, focus, explanation and immutable replay checks passed"
