{-# LANGUAGE OverloadedStrings #-}
-- External client imports public facades only. No private compiler/evaluator.
module Main where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import qualified Data.Text.IO as T
import qualified Data.Text.Encoding as U
import Control.Monad (unless)
import qualified Yuho.Authoring as SDK
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring (ScopedBody(..),requirementTemplate,requirementUse,inspectScopedDefinitions)
import Yuho.Authoring.Dependency

ok :: Show e => Either e a -> IO a
ok=either (fail . show) pure
main :: IO ()
main=do
  args<-getArgs
  case args of
    ["builders",folder]->do
      declaration<-ok (requirementTemplate "q:permission" [("var:actor","person"),("var:incident","event")]
        (ScopedAtom "permitted" ["var:actor","var:incident"]))
      use<-ok (requirementUse "q:first" "law::q:permission" ["actor:alpha","event:alpha"])
      T.writeFile (folder</>"template.yh") declaration
      T.writeFile (folder</>"use.yh") use
    ["run",document,folder]->do
      doc<-BS.readFile document >>= ok . decodeDependencyDocument
      checked<-ok (checkDependencyPlan doc)
      result<-ok (executeDependencyPlan checked)
      -- Independent public recovery: this selected component must retain the
      -- one authored definition module, not expanded request text as authority.
      sources<-ok (dependencyComponentSources result "alpha")
      source<-case [s | s<-sources,SDK.sourceId s=="modules/reuse.permission@1.0.0.yh"] of
        [s]->pure s
        _->fail "shared original module missing from component source closure"
      text<-maybe (fail "original text missing") pure (SDK.sourceText source)
      anchor<-ok (SDK.sourceAnchorBytes source 0 (toInteger (BS.length (U.encodeUtf8 text))))
      (_,quote)<-ok (recoverDependencyReference result "alpha" anchor)
      unless (quote==Just text) (fail "original definition source recovery changed bytes")
      publishDependencyPlan folder result >>= ok
      BL.putStr (A.encode (inspectScopedDefinitions result))
    _->fail "builders FOLDER | run DOCUMENT NEW_OUTPUT"
