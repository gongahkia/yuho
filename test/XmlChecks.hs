{-# LANGUAGE OverloadedStrings #-}
module XmlChecks (runXmlChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Protocol.Json (J(..), decodeJson)
import Yuho.Protocol.Xml (encodeXml)
import Yuho.Surface.Compile (compileSource)

runXmlChecks :: FilePath -> IO ()
runXmlChecks root = do
  check "XML escapes values and sorts object members" $
    encodeXml sample == Right expected
  check "XML escapes object member names" $ case encodeXml (JObj [("a\"&", JNull)]) of
    Right output -> "name=\"a&quot;&amp;\"" `BS.isInfixOf` output
    Left _ -> False
  check "XML object order is deterministic" $
    encodeXml (JObj [("z", JNull), ("a", JNull)])
      == encodeXml (JObj [("a", JNull), ("z", JNull)])
  check "XML rejects XML 1.0 control characters" $ case encodeXml (JStr "bad\x1f") of
    Left _ -> True
    Right _ -> False
  source <- BS.readFile (root </> "examples/synthetic/restricted_entry.yh")
  scenario <- BS.readFile (root </> "examples/synthetic/scenario_all_proved.yh")
  let compiled = compileSource "restricted_entry.yh" source
        (Just ("scenario_all_proved.yh", scenario))
      exported = case compiled of
        Left _ -> Left ()
        Right request -> case decodeJson request of
          Left _ -> Left ()
          Right value -> case encodeXml value of
            Left _ -> Left ()
            Right output -> Right output
  check "compiled technical request exports as XML" $ case exported of
    Right output -> BS.isPrefixOf "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<yuho:document"
      output && BS.isSuffixOf "</yuho:document>\n" output
    Left _ -> False
  putStrLn "xml: deterministic technical XML output passed"

sample :: J
sample = JObj
  [("text", JStr "A&B<>'\"")
  ,("array", JArr [JNull, JBool False, JNum (-7)])]

expected :: BS.ByteString
expected = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<yuho:document xmlns:yuho=\"urn:yuho:xml:v1\"><yuho:object><yuho:member name=\"array\"><yuho:array><yuho:item index=\"0\"><yuho:null/></yuho:item><yuho:item index=\"1\"><yuho:boolean>false</yuho:boolean></yuho:item><yuho:item index=\"2\"><yuho:number>-7</yuho:number></yuho:item></yuho:array></yuho:member><yuho:member name=\"text\"><yuho:string>A&amp;B&lt;&gt;'\"</yuho:string></yuho:member></yuho:object></yuho:document>\n"

check :: String -> Bool -> IO ()
check label success = unless success (putStrLn (label <> " failed") >> exitFailure)
