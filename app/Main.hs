module Main (main) where

import qualified Data.ByteString as BS
import System.IO (hFlush, stdin, stdout)
import Yuho.Kernel.Run (runLine, rejectResource)
import Yuho.Protocol.Json (maxRequestBytes)

main :: IO ()
main = loop BS.empty False

loop :: BS.ByteString -> Bool -> IO ()
loop carry tooLong = do
  chunk <- BS.hGetSome stdin 4096
  if BS.null chunk
    then if tooLong then send rejectResource
         else if BS.null carry then pure () else send (runLine carry)
    else consume carry tooLong chunk

consume :: BS.ByteString -> Bool -> BS.ByteString -> IO ()
consume carry tooLong chunk =
  let (part, rest) = BS.break (== 10) chunk
      exceeds = tooLong || BS.length carry + BS.length part > maxRequestBytes
      accumulated = if exceeds then BS.empty else carry <> part
  in if BS.null rest
       then loop accumulated exceeds
       else do
         send (if exceeds then rejectResource else runLine accumulated)
         if BS.length rest == 1 then loop BS.empty False
           else consume BS.empty False (BS.drop 1 rest)

send :: BS.ByteString -> IO ()
send bytes = BS.hPut stdout bytes >> hFlush stdout
