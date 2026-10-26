{-# LANGUAGE OverloadedStrings #-}
-- Public facades only: no private parser, numeric engine or protocol imports.
module Main where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import qualified Data.Map.Strict as M
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import qualified Data.Text.Encoding as U
import Control.Monad (unless)
import System.Environment (getArgs)
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import Yuho.Authoring.Quantitative
import Yuho.Authoring.Dependency
import qualified Yuho.Authoring as SDK

ok :: Show e => Either e a -> IO a
ok=either (fail . show) pure
known :: Integer -> QValue
known=QKnown QInteger
display :: QValue -> String
display (QKnown _ n)="K:"++show n
display (QUnknown _ _)="U"
vectors :: IO ()
vectors=do
  let pair a b=QSum [QItem "one" (QRef "a") Nothing,QItem "two" (QRef "b") Nothing]
        `with` [("a",a),("b",b)]
      with expr env=evaluateExactExpression "out" QInteger expr env []
      filtered x y first second=evaluateExactExpression "out" QInteger
        (QSum [QItem "one" (QRef "a") (Just "first"),QItem "two" (QRef "b") (Just "second")])
        [("a",x),("b",y)] [("first",first),("second",second)]
      scale n v=evaluateExactExpression "out" QInteger (QScale n (QRef "a")) [("a",v)] []
      count fs=evaluateExactExpression "out" (QCount "occasions")
        (QCountItems [(i,i) | (i,_)<-fs]) [] fs
      cases=[pair (known 400000) (known 600000),pair (known 400000) (known 599999)
        ,pair (known 1) (known (-4))
        ,filtered (known 4) (QUnknown QInteger ["missing valuation"]) Satisfied Satisfied
        ,filtered (known 4) (QUnknown QInteger ["missing valuation"]) Satisfied NotSatisfied
        ,filtered (known 4) (known 0) Satisfied Unresolved
        ,evaluateExactExpression "out" QInteger (QScale 3 (QSum [QItem "one" (QConstant QInteger 125) Nothing,QItem "two" (QConstant QInteger 275) Nothing])) [] []
        ,scale 0 (QUnknown QInteger ["zero does not erase uncertainty"])
        ,count [("a",Satisfied),("b",NotSatisfied),("c",Satisfied)]
        ,count [("a",Satisfied),("b",Unresolved)]
        ,evaluateExactExpression "out" QInteger (QSum []) [] []
        ,scale 3 (known 9007199254740993),count [],scale (-2) (known 7)
        ,filtered (known 0) (known 0) Satisfied Unresolved]
  values<-traverse ok cases
  let expected=["K:1000000","K:999999","K:-3","U","K:4","U","K:1200","U","K:2","U","K:0","K:27021597764222979","K:0","K:-14","U"]
  unless (map display values==expected) (fail "independent exact SDK oracle mismatch")
  let invalid=[evaluateExactExpression "out" (QMoney "SGD") (QRef "usd") [("usd",QKnown (QMoney "USD") 1)] []
        ,evaluateExactExpression "out" (QCount "occasions") (QRef "a") [("a",known 1)] []
        ,evaluateExactExpression "out" QInteger (QRef "missing") [] []
        ,evaluateExactExpression "out" (QMoney "SGD") (QScale (-1) (QConstant (QMoney "SGD") 1)) [] []]
  unless (all (either (const True) (const False)) invalid) (fail "unsafe scalar/type operation admitted")
  mapM_ (putStrLn . display) values

main :: IO ()
main=do
  args<-getArgs
  case args of
    ["vectors"]->vectors
    ["builders",folder]->do
      createDirectoryIfMissing True folder
      inputs<-traverse (\n->ok (scalarInput n (QMoney "SGD"))) ["v:first","v:second","v:threshold"]
      expression<-ok (derivedQuantity "v:total" (QMoney "SGD")
        (QSum [QItem "first" (QRef "v:first") Nothing,QItem "second" (QRef "v:second") Nothing]))
      supplied<-sequence [ok (suppliedQuantity "v:first" (QKnown (QMoney "SGD") 125) "first independently authored source")
        ,ok (suppliedQuantity "v:second" (QKnown (QMoney "SGD") 275) "second independently authored source")
        ,ok (suppliedQuantity "v:threshold" (QKnown (QMoney "SGD") 400) "authored exact boundary")]
      TIO.writeFile (folder</>"model.yh") (T.unlines (["typed-rules-model Quantities {",quantitativeHeader
        ,"entity-type person; entity-type event; entity actor as person; entity incident as event;"]++inputs++[expression
        ,"requirement q:result = compare(v:total,eq,v:threshold); proposition p; rule r establishes proposition p when q:result; limitation \"Fictional SDK mathematical control\"; }"]))
      TIO.writeFile (folder</>"scenario.yh") ("typed-rules-scenario SDK for Quantities {\n"<>T.unlines supplied<>"}")
    ["run",document,folder]->do
      doc<-BS.readFile document >>= ok . decodeDependencyDocument
      checked<-ok (checkDependencyPlan doc)
      execution<-ok (executeDependencyPlan checked)
      projection<-ok (projectDependencyPlan execution)
      ok (validateDependencyProjection execution projection)
      ok (validateDependencyViewBindings execution (dependencyViewBindings execution))
      let first=case planComponents (dependencyPlan doc) of c:_->componentIdentity c;_->""
      sources<-ok (dependencyComponentSources execution first)
      source<-case [s | s<-sources,T.unpack (SDK.sourceId s) `M.member` dependencySources doc] of
        s:_->pure s;_->fail "original scalar source missing"
      text<-maybe (fail "source bytes absent") pure (SDK.sourceText source)
      anchor<-ok (SDK.sourceAnchorBytes source 0 (toInteger (BS.length (U.encodeUtf8 text))))
      (_,quote)<-ok (recoverDependencyReference execution first anchor)
      unless (quote==Just text) (fail "source recovery changed original bytes")
      saved<-ok (decodeDependencyArtifact (encodeDependencyArtifact (saveDependencyArtifact execution)))
      replayed<-ok (replayDependencyPlan saved)
      unless (reportDependencyPlan execution==reportDependencyPlan replayed) (fail "immutable replay changed exact values/provenance")
      publishDependencyPlan folder execution >>= ok
      BL.putStr (A.encode (inspectQuantitative execution))
    _->fail "vectors | builders EXTERNAL_DIRECTORY | run DOCUMENT NEW_OUTPUT"
