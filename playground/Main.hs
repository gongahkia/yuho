{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import qualified Data.ByteString.Lazy as BL
import Euclid.Playground.API

main :: IO ()
main =
    BL.getContents >>= BL.putStr . handlePlaygroundJson
