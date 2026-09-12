module Sha256 (sha256) where

import Data.Array (Array, (!), listArray)
import Data.Bits ((.&.), (.|.), complement, rotateR, shiftL, shiftR, xor)
import qualified Data.ByteString as BS
import Data.List (foldl')
import Data.Word (Word8, Word32, Word64)
import Numeric (showHex)

type State = (Word32, Word32, Word32, Word32, Word32, Word32, Word32, Word32)

sha256 :: BS.ByteString -> String
sha256 bytes = concatMap hex32 (stateWords (foldl' process initial (chunks (pad (BS.unpack bytes)))))

initial :: State
initial = (0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
           0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19)

stateWords :: State -> [Word32]
stateWords (a,b,c,d,e,f,g,h) = [a,b,c,d,e,f,g,h]

roundConstants :: Array Int Word32
roundConstants = listArray (0, 63)
  [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
   0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
   0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
   0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
   0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
   0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
   0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
   0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]

pad :: [Word8] -> [Word8]
pad source =
  let byteLength = length source
      zeroCount = mod (56 - mod (byteLength + 1) 64) 64
      bitLength = fromIntegral byteLength * 8 :: Word64
      lengthBytes = [fromIntegral (shiftR bitLength shift) | shift <- [56,48..0]]
  in source ++ [0x80] ++ replicate zeroCount 0 ++ lengthBytes

chunks :: [a] -> [[a]]
chunks [] = []
chunks items =
  let (first, rest) = splitAt 64 items
  in first : chunks rest

groupsOfFour :: [Word8] -> [[Word8]]
groupsOfFour [] = []
groupsOfFour items =
  let (first, rest) = splitAt 4 items
  in first : groupsOfFour rest

wordFromBytes :: [Word8] -> Word32
wordFromBytes = foldl' (\acc byte -> (shiftL acc 8) .|. fromIntegral byte) 0

small0, small1, big0, big1 :: Word32 -> Word32
small0 value = xor (xor (rotateR value 7) (rotateR value 18)) (shiftR value 3)
small1 value = xor (xor (rotateR value 17) (rotateR value 19)) (shiftR value 10)
big0 value = xor (xor (rotateR value 2) (rotateR value 13)) (rotateR value 22)
big1 value = xor (xor (rotateR value 6) (rotateR value 11)) (rotateR value 25)

process :: State -> [Word8] -> State
process (h0,h1,h2,h3,h4,h5,h6,h7) block =
  let firstWords = map wordFromBytes (groupsOfFour block)
      schedule :: Array Int Word32
      schedule = listArray (0, 63)
        (firstWords ++ [small1 (schedule ! (index - 2)) + schedule ! (index - 7)
                       + small0 (schedule ! (index - 15)) + schedule ! (index - 16)
                       | index <- [16..63]])
      (a,b,c,d,e,f,g,h) = foldl' (roundStep schedule) (h0,h1,h2,h3,h4,h5,h6,h7) [0..63]
  in (h0+a,h1+b,h2+c,h3+d,h4+e,h5+f,h6+g,h7+h)

roundStep :: Array Int Word32 -> State -> Int -> State
roundStep schedule (a,b,c,d,e,f,g,h) index =
  let choice = xor (e .&. f) (complement e .&. g)
      majority = xor (xor (a .&. b) (a .&. c)) (b .&. c)
      temp1 = h + big1 e + choice + roundConstants ! index + schedule ! index
      temp2 = big0 a + majority
  in (temp1 + temp2,a,b,c,d + temp1,e,f,g)

hex32 :: Word32 -> String
hex32 value =
  let digits = showHex value ""
  in replicate (8 - length digits) '0' ++ digits
