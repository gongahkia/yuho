{-# LANGUAGE OverloadedStrings #-}
-- Public parser probe used by compiler_integrity.py. Hex transport admits every byte.
module Main (main) where
import Control.Monad (unless)
import qualified Data.ByteString as B
import qualified Data.ByteString.Char8 as C
import qualified Data.Text as T
import Numeric (readHex)
import System.IO (isEOF)
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Parser (parseModel, parseScenario, parseAnalysisCase)
import Yuho.Surface.Presumption (parsePresumptionSource)
import Yuho.Surface.TypedFinite (parseTypedFiniteModel, parseTypedFiniteScenario)
import Yuho.Surface.Token

main :: IO ()
main = do
  done <- isEOF
  unless done $ do
    line <- getLine
    let bytes = B.pack (hex line)
        result = JObj
          [("lexer", either diagnosticJson (JArr . map token) (lexSource "probe.yh" bytes))
          ,("parsers", JArr [summary (parseModel "probe.yh" bytes)
            ,summary (parseScenario "probe.yh" bytes),summary (parseAnalysisCase "probe.yh" bytes)
            ,summary (parsePresumptionSource "probe.yh" bytes)
            ,summary (parseTypedFiniteModel "probe.yh" bytes)
            ,summary (parseTypedFiniteScenario "probe.yh" bytes)])]
    C.putStrLn (encodeJson result)
    main
  where
    hex [] = []
    hex (a:b:rest) = case readHex [a,b] of
      [(n,"")] -> n : hex rest
      _ -> error "invalid test transport"
    hex _ = error "odd test transport"
    token t = JArr [JStr (T.pack (show (tokenKind t))), JStr (tokenText t)
      ,JNum (toInteger (tokenLine t)),JNum (toInteger (tokenColumn t))]
    -- Force the entire returned AST, including lazy expression children.
    summary :: Show a => Either Diagnostic a -> J
    summary (Left d) = diagnosticJson d
    summary (Right a) = JObj [("ast_show_length",JNum (toInteger (length (show a))))]
