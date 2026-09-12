{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Decode (decodeExceptionRequest) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Diagnostic, Source, diagnostic)
import Yuho.Exception.Types
import Yuho.Protocol.Decode
  ( asArray, asText, closed, countIds, decodeFacts, decodePolicy, decodeProvision
  , decodeSource, decodeSpan, inputDigest, invalid, required
  )
import Yuho.Protocol.Json (J(..))

decodeExceptionRequest :: J -> Either Diagnostic ExceptionRequest
decodeExceptionRequest root = do
  protocol <- required asText "" "protocol" root
  if protocol == "yuho.kernel-protocol/v1" then pure () else
    Left (diagnostic "KPROT001" "protocol" "/protocol" Nothing [("received", protocol)])
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
            , "sources", "policy", "registry", "root_rule", "facts"] root
  requestId <- required asText "" "request_id" root
  if validRequestId requestId then pure () else invalid "/request_id" "invalid request ID"
  schema <- required asText "" "input_schema" root
  if schema == "yuho.kernel-input/v1" then pure () else
    invalid "/input_schema" "unsupported input schema"
  fragment <- required asText "" "fragment" root
  if fragment == "AcyclicGuardedExceptions-v1" then pure () else
    Left (diagnostic "KCAP001" "capability" "/fragment" Nothing [("kind", fragment)])
  operation <- required asText "" "operation" root
  if operation == "evaluate" then pure () else
    Left (diagnostic "KCAP001" "capability" "/operation" Nothing [("kind", operation)])
  sourceValues <- required asArray "" "sources" root
  sources <- traverse (uncurry decodeNamedSource) (zip [0 :: Int ..] sourceValues)
  checkUniqueSources sources
  (date, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  registry <- required asArray "" "registry" root
  if countIds (JArr sourceValues) + countIds (JArr registry) > maxNodes then
    Left (diagnostic "KINV004" "validate" "/registry" Nothing []) else pure ()
  rules <- traverse (uncurry (decodeRule sources)) (zip [0 :: Int ..] registry)
  rootId <- required asText "" "root_rule" root
  facts <- required (\_ -> decodeFacts) "" "facts" root
  pure (ExceptionRequest requestId (inputDigest root)
    (RawGraph rootId sources rules facts date maxNodes))

validRequestId :: Text -> Bool
validRequestId value = case Text.uncons value of
  Just (first, rest) -> first >= 'A' && first <= 'Z'
    && Text.length rest == 2 && Text.all (\ch -> ch >= '0' && ch <= '9') rest
  Nothing -> False

pointerAt :: Text -> Int -> Text
pointerAt prefix index = prefix <> "/" <> Text.pack (show index)

decodeNamedSource :: Int -> J -> Either Diagnostic (Text, Source)
decodeNamedSource index value = do
  let pointer = pointerAt "/sources" index
  closed pointer ["id", "path", "text", "sha256"] value
  identifier <- required asText pointer "id" value
  source <- case value of
    JObj fields -> decodeSource (JObj (filter ((/= "id") . fst) fields))
    _ -> invalid pointer "expected source object"
  pure (identifier, source)

checkUniqueSources :: [(Text, Source)] -> Either Diagnostic ()
checkUniqueSources = go []
  where
    go _ [] = Right ()
    go seen ((identifier, _):rest)
      | Text.null identifier = invalid "/sources/id" "empty source ID"
      | identifier `elem` seen = Left (diagnostic "KINV002" "validate"
          "/sources/id" Nothing [("id", identifier)])
      | otherwise = go (identifier : seen) rest

decodeRule :: [(Text, Source)] -> Int -> J -> Either Diagnostic RawRule
decodeRule sources index value = do
  let pointer = pointerAt "/registry" index
  closed pointer ["id", "source_id", "program", "exceptions"] value
  identifier <- required asText pointer "id" value
  sourceId <- required asText pointer "source_id" value
  source <- findSource sources (pointer <> "/source_id") sourceId
  program <- required (decodeProvision source) pointer "program" value
  exceptionValues <- required asArray pointer "exceptions" value
  exceptions <- traverse (uncurry (decodeException sources pointer))
    (zip [0 :: Int ..] exceptionValues)
  pure (RawRule identifier sourceId program exceptions pointer)

decodeException :: [(Text, Source)] -> Text -> Int -> J -> Either Diagnostic RawException
decodeException sources rulePointer index value = do
  let pointer = pointerAt (rulePointer <> "/exceptions") index
  closed pointer ["id", "branch_id", "source_id", "span", "guard", "effect"] value
  identifier <- required asText pointer "id" value
  branchId <- required asText pointer "branch_id" value
  sourceId <- required asText pointer "source_id" value
  source <- findSource sources (pointer <> "/source_id") sourceId
  sourceSpan <- required (decodeSpan source) pointer "span" value
  effect <- required asText pointer "effect" value
  if effect == "defeat" then pure () else
    Left (diagnostic "KCAP001" "capability" (pointer <> "/effect")
      (Just sourceSpan) [("kind", effect)])
  guardValue <- required (\_ -> Right) pointer "guard" value
  closed (pointer <> "/guard") ["kind", "target"] guardValue
  kind <- required asText (pointer <> "/guard") "kind" guardValue
  if kind == "is_infringed" then pure () else
    Left (diagnostic "KCAP001" "capability" (pointer <> "/guard/kind")
      (Just sourceSpan) [("kind", kind)])
  target <- required asText (pointer <> "/guard") "target" guardValue
  pure (RawException identifier branchId sourceId sourceSpan target pointer)

findSource :: [(Text, Source)] -> Text -> Text -> Either Diagnostic Source
findSource sources pointer identifier = case Map.lookup identifier (Map.fromList sources) of
  Just source -> Right source
  Nothing -> Left (diagnostic "KINV005" "validate" pointer Nothing [("id", identifier)])
