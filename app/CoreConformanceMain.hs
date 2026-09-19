{-# LANGUAGE OverloadedStrings #-}
module Main where

import qualified Data.ByteString as BS
import qualified Data.ByteString.Char8 as BS8
import System.Environment (getArgs)
import System.Exit (die)
import Yuho.CoreYuho.Conformance (evaluateConformanceBytes)

main :: IO ()
main = do
  arguments <- getArgs
  case arguments of
    [path] -> do
      bytes <- BS.readFile path
      case evaluateConformanceBytes bytes of
        Left issue -> die (show issue)
        Right result -> BS8.putStr result
    _ -> die "usage: yuho-core-conformance <vectors.json>"
