{-# LANGUAGE OverloadedStrings #-}
-- Public SDK structural admission/cost probe. No evaluator is invoked.
module Main (main) where
import qualified Data.ByteString.Char8 as B
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Surface.TypedFinite (expandedNodeEstimate)
import Yuho.TypedFiniteRules.Run (decodeTypedFiniteRequest)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson)

main :: IO ()
main = B.getContents >>= mapM_ (B.putStrLn . encodeJson . probe) . B.lines
  where
    probe bytes = case decodeJson bytes >>= decodeTypedFiniteRequest of
      Left reason -> JObj [("admitted",JBool False),("reason",JStr reason)]
      Right program -> case (expandedNodeEstimate program,K.expandedProgramSize program) of
        (Right source,Right kernel) -> JObj [("admitted",JBool True)
          ,("source_cost",JNum source),("kernel_cost",JNum kernel)]
        _ -> JObj [("admitted",JBool False)]
