{-# LANGUAGE OverloadedStrings #-}
-- External public-only test client. Expectations live in the Python test,
-- independent of the checker/key/rendering implementation.
module Main (main) where
import qualified Yuho.Authoring.Dependency as D
import qualified Data.Aeson as A
import qualified Data.ByteString as B
import qualified Data.ByteString.Lazy.Char8 as L
import System.Environment (getArgs)
import System.Exit (exitFailure)

require :: Either D.DependencyDiagnostic a -> IO a
require=either (\d->L.putStrLn (A.encode d)>>exitFailure) pure
main :: IO ()
main=do
  args<-getArgs
  case args of
    [operation,input,output]->do
      bytes<-B.readFile input
      document<-require (D.decodeDependencyDocument bytes)
      checked<-require (D.checkDependencyPlan document)
      if operation=="check" then L.putStrLn (A.encode (A.object ["checked" A..= True,"evaluated" A..= False])) else do
        execution<-require (D.executeDependencyPlan checked)
        D.publishDependencyPlan output execution >>= require
        L.putStrLn (A.encode (D.reportDependencyPlan execution))
    _->fail "expected check|run DOCUMENT NEW_OUTPUT"
