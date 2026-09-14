{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Lower (lowerChecked) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.Surface.AST
import Yuho.Surface.Definitions
  ( definitionIndex, definitionQuoteKeys, reachableDefinitions )
import Yuho.Surface.Token

object :: [(Text, J)] -> J
object = JObj

string :: Text -> J
string = JStr

array :: [J] -> J
array = JArr

tokenValue :: Token -> J
tokenValue = string . tokenText

spanValue :: BS.ByteString -> Int -> Int -> J
spanValue bytes start end = object
  [ ("start", JNum (toInteger start)), ("end", JNum (toInteger end))
  , ("start_line", JNum (toInteger firstLine)), ("start_col", JNum (toInteger firstCol))
  , ("end_line", JNum (toInteger lastLine)), ("end_col", JNum (toInteger lastCol))
  ]
  where
    position offset =
      let prefix = BS.take offset bytes
          pieces = BS.split 10 prefix
          column = case reverse pieces of
            current:_ -> BS.length current + 1
            [] -> 1
      in (1 + BS.count 10 prefix, column)
    (firstLine, firstCol) = position start
    (lastLine, lastCol) = position end

wholeSpan :: BS.ByteString -> J
wholeSpan bytes = spanValue bytes 0 (BS.length bytes)

quoteSource :: [(Token, Token)] -> (BS.ByteString, Map.Map Text J)
quoteSource quotes = (text, Map.fromList (snd (foldl add (0, []) quotes)))
  where
    text = Encoding.encodeUtf8 (Text.intercalate "\n" (map (tokenText . snd) quotes) <> "\n")
    add (offset, rows) (key, value) =
      let size = BS.length (Encoding.encodeUtf8 (tokenText value))
      in (offset + size + 1, rows ++ [(tokenText key, spanValue text offset (offset + size))])

sourceValue :: Token -> Token -> BS.ByteString -> J
sourceValue sourceIdentifier location bytes = object
  [ ("id", tokenValue sourceIdentifier), ("path", tokenValue location)
  , ("text", string (Encoding.decodeUtf8 bytes)), ("sha256", string (sha256Text bytes))]

statusBytes :: BS.ByteString
statusBytes = "synthetic proof classifications only\n"

factValue :: Bool -> Text -> Text -> J -> (Token, Proof) -> (Text, J)
factValue section issuer statusId context (key, proof) = (tokenText key, object (base ++ metadata))
  where
    proofValue = case proof of
      Proved -> object [("kind", string "proved")]
      NotProved -> object [("kind", string "not_proved")]
      Unresolved reason -> object [("kind", string "unresolved"), ("reason", string reason)]
    assignment = "assignment:" <> Text.drop 2 (tokenText key)
    base =
      [ ("proof_status", proofValue)
      , ("status_source", object
          [("assignment_id", string assignment)
          ,("issuer_label", string issuer)
          ,("origin", string "synthetic_fixture")
          ,("source_id", string statusId)
          ,("span", wholeSpan statusBytes)])
      ]
    metadata = if section then
      [("burden", context), ("standard_of_proof", string "balance_of_probabilities")]
      else []

requirement :: Bool -> J -> BS.ByteString -> Map.Map Text J -> Token -> Resolved -> Either Diagnostic J
requirement section burden text quoteSpans path node = case node of
  ResolvedLeaf key quote -> case Map.lookup (tokenText quote) quoteSpans of
    Nothing -> at "SFE003" "<lower>" quote "unknown source quote"
    Just sourceSpan -> Right (object
      ([ ("id", tokenValue key), ("kind", string "leaf")
       , ("path", array [tokenValue path]), ("span", sourceSpan) ] ++
       if section then [("declared_metadata", object
           [("burden", burden), ("standard_of_proof", string "balance_of_probabilities")])]
       else []))
  ResolvedGroup key combinator members -> do
    lowered <- mapM (requirement section burden text quoteSpans path) members
    pure (object
      [("id", tokenValue key)
      ,("kind", string (case combinator of All -> "all"; Any -> "any"))
      ,("path", array [tokenValue path])
      ,("span", wholeSpan text)
      ,("members", array lowered)])

program :: Token -> BS.ByteString -> J -> J -> J
program path text programId root = object
  [("id", programId), ("path", array [tokenValue path])
  ,("span", wholeSpan text), ("definitions", JBool False)
  ,("requirements", array [root]), ("children", array []), ("penalties", array [])]

sourceDecl :: Text -> [SourceDecl] -> Either Diagnostic (Token, Token)
sourceDecl role rows = case [(item, location) | SourceDecl item kind location <- rows,
    tokenText kind == role] of
  [(item, location)] -> Right (item, location)
  _ -> at "SFE014" "<lower>" (Token WordToken role 1 1) "missing source role"

lowerChecked :: Checked -> Either Diagnostic BS.ByteString
lowerChecked (Checked model scenario assignments firstTree secondTree) = do
  let quoted = case (modelBody model, scenario) of
        (MultiLegal _ offences exceptions attachments _, Just (Scenario _ _ _ _ [target])) ->
          case [(offence, exception) | offence <- offences,
            tokenText (ruleIdentifier offence) == tokenText target,
            Attachment _ exceptionId owner <- attachments,
            tokenText owner == tokenText target,
            GeneralException exception <- exceptions,
            tokenText (ruleIdentifier exception) == tokenText exceptionId] of
            [(offence, exception)] ->
              let references = Set.fromList [tokenText item | rule <- [offence, exception],
                    element <- ruleElements rule,
                    item <- elementQuote element : maybe [] (:[]) (elementSupport element)]
              in filter (\(key,_) -> Set.member (tokenText key) references) (modelQuotes model)
            _ -> modelQuotes model
        (DefinitionsLegal definitions _ offences exceptions attachments _,
          Just (Scenario _ _ _ _ [target])) ->
          case [(offence, exception) | offence <- offences,
            tokenText (ruleIdentifier offence) == tokenText target,
            Attachment _ exceptionId owner <- attachments,
            tokenText owner == tokenText target,
            GeneralException exception <- exceptions,
            tokenText (ruleIdentifier exception) == tokenText exceptionId] of
            [(offence, exception)] ->
              let index = Map.fromList [(tokenText (definitionId item), item)
                    | item <- definitions]
                  selected = reachableDefinitions index offence
                  references = Set.fromList (map tokenText
                    ([item | rule <- [offence, exception], element <- ruleElements rule,
                       item <- elementQuote element : maybe [] (:[]) (elementSupport element)]
                    ++ concatMap definitionQuoteKeys selected))
              in filter (\(key,_) -> Set.member (tokenText key) references)
                   (modelQuotes model)
            _ -> modelQuotes model
        _ -> modelQuotes model
      (text, quoteSpans) = quoteSource quoted
  (sourceId, sourcePath) <- sourceDecl sourceRole (modelSources model)
  (statusId, statusPath) <- sourceDecl "synthetic_status" (modelSources model)
  request <- case modelBody model of
    Section rootRuleId programId path _ _ _ _ -> do
      root <- requirement True burden text quoteSpans path firstTree
      pure (baseRequest model rootRuleId
        [sourceValue sourceId sourcePath text, sourceValue statusId statusPath statusBytes]
        [object [("id", tokenValue rootRuleId), ("source_id", tokenValue sourceId)
          ,("program", program path text (tokenValue programId) root)
          ,("exceptions", array [])]]
        (object (map (factValue True "synthetic research fixture" (tokenText statusId) burden) assignments)))
    Synthetic offence exception _ -> case secondTree of
      Nothing -> at "SFE007" "<lower>" (ruleIdentifier exception) "exception tree missing"
      Just exceptionTree -> do
        if scenario == Nothing
          then at "SFE009" "<lower>" (modelIdentifier model) "scenario required"
          else pure ()
        offenceRoot <- requirement False burden text quoteSpans (rulePath offence) firstTree
        exceptionRoot <- requirement False burden text quoteSpans (rulePath exception) exceptionTree
        let exceptionBinding = object
              [("id", tokenValue (ruleIdentifier exception))
              ,("branch_id", tokenValue (ruleProgram offence))
              ,("source_id", tokenValue sourceId), ("span", wholeSpan text)
              ,("guard", object [("kind", string "is_infringed")
                  ,("target", tokenValue (ruleId exception))])
              ,("effect", string "defeat")]
            registry =
              [object [("id", tokenValue (ruleId offence)), ("source_id", tokenValue sourceId)
                ,("program", program (rulePath offence) text (tokenValue (ruleProgram offence)) offenceRoot)
                ,("exceptions", array [exceptionBinding])]
              ,object [("id", tokenValue (ruleId exception)), ("source_id", tokenValue sourceId)
                ,("program", program (rulePath exception) text (tokenValue (ruleProgram exception)) exceptionRoot)
                ,("exceptions", array [])]]
        pure (baseRequest model (ruleId offence)
          [sourceValue sourceId sourcePath text, sourceValue statusId statusPath statusBytes]
          registry (object (map (factValue False "fictional compiler fixture" (tokenText statusId) burden) assignments)))
    Legal _ offence exception _ -> case secondTree of
      Nothing -> at "SFE007" "<lower>" (ruleIdentifier exception) "exception tree missing"
      Just exceptionTree -> do
        if scenario == Nothing
          then at "SFE009" "<lower>" (modelIdentifier model) "scenario and scope acknowledgements required"
          else pure ()
        offenceRoot <- requirement False burden text quoteSpans (rulePath offence) firstTree
        exceptionRoot <- requirement True burden text quoteSpans (rulePath exception) exceptionTree
        let exceptionBinding = object
              [("id", tokenValue (ruleIdentifier exception))
              ,("branch_id", tokenValue (ruleProgram offence))
              ,("source_id", tokenValue sourceId), ("span", wholeSpan text)
              ,("guard", object [("kind", string "is_infringed")
                  ,("target", tokenValue (ruleId exception))])
              ,("effect", string "defeat")]
            registry =
              [object [("id", tokenValue (ruleId offence)), ("source_id", tokenValue sourceId)
                ,("program", program (rulePath offence) text (tokenValue (ruleProgram offence)) offenceRoot)
                ,("exceptions", array [exceptionBinding])]
              ,object [("id", tokenValue (ruleId exception)), ("source_id", tokenValue sourceId)
                ,("program", program (rulePath exception) text (tokenValue (ruleProgram exception)) exceptionRoot)
                ,("exceptions", array [])]]
            exceptionIds = Set.fromList (map (tokenText . elementId) (ruleElements exception))
            fact (key, value) = factValue (Set.member (tokenText key) exceptionIds)
              "synthetic research fixture" (tokenText statusId) burden (key, value)
        pure (baseRequest model (ruleId offence)
          [sourceValue sourceId sourcePath text, sourceValue statusId statusPath statusBytes]
          registry (object (map fact assignments)))
    MultiLegal _ offences exceptions attachments _ -> case (scenario, secondTree) of
      (Just (Scenario _ _ _ _ [target]), Just exceptionTree) ->
        case [(offence, exception) | offence <- offences,
          tokenText (ruleIdentifier offence) == tokenText target,
          Attachment _ exceptionId owner <- attachments,
          tokenText owner == tokenText target,
          GeneralException exception <- exceptions,
          tokenText (ruleIdentifier exception) == tokenText exceptionId] of
          [(offence, exception)] -> do
            offenceRoot <- requirement False burden text quoteSpans (rulePath offence) firstTree
            exceptionRoot <- requirement True burden text quoteSpans (rulePath exception) exceptionTree
            let binding = object
                  [("id", tokenValue (ruleIdentifier exception))
                  ,("branch_id", tokenValue (ruleProgram offence))
                  ,("source_id", tokenValue sourceId), ("span", wholeSpan text)
                  ,("guard", object [("kind", string "is_infringed")
                    ,("target", tokenValue (ruleId exception))])
                  ,("effect", string "defeat")]
                registry =
                  [object [("id", tokenValue (ruleId offence)), ("source_id", tokenValue sourceId)
                    ,("program", program (rulePath offence) text (tokenValue (ruleProgram offence)) offenceRoot)
                    ,("exceptions", array [binding])]
                  ,object [("id", tokenValue (ruleId exception)), ("source_id", tokenValue sourceId)
                    ,("program", program (rulePath exception) text (tokenValue (ruleProgram exception)) exceptionRoot)
                    ,("exceptions", array [])]]
                exceptionIds = Set.fromList (map (tokenText . elementId) (ruleElements exception))
                fact (key, value) = factValue (Set.member (tokenText key) exceptionIds)
                  "synthetic research fixture" (tokenText statusId) burden (key, value)
            pure (baseRequest model (ruleId offence)
              [sourceValue sourceId sourcePath text, sourceValue statusId statusPath statusBytes]
              registry (object (map fact assignments)))
          _ -> at "SFE040" "<lower>" target "selected attachment is not unique"
      _ -> at "SFE036" "<lower>" (modelIdentifier model) "one scenario analysis target required"
    DefinitionsLegal definitions _ offences exceptions attachments _ ->
      case (scenario, secondTree) of
        (Just (Scenario _ _ _ _ [target]), Just exceptionTree) ->
          case [(offence, exception) | offence <- offences,
            tokenText (ruleIdentifier offence) == tokenText target,
            Attachment _ exceptionId owner <- attachments,
            tokenText owner == tokenText target,
            GeneralException exception <- exceptions,
            tokenText (ruleIdentifier exception) == tokenText exceptionId] of
            [(offence, exception)] -> do
              _ <- definitionIndex "<lower>" definitions
              offenceRoot <- requirement False burden text quoteSpans (rulePath offence) firstTree
              exceptionRoot <- requirement True burden text quoteSpans (rulePath exception) exceptionTree
              let binding = object
                    [("id", tokenValue (ruleIdentifier exception))
                    ,("branch_id", tokenValue (ruleProgram offence))
                    ,("source_id", tokenValue sourceId), ("span", wholeSpan text)
                    ,("guard", object [("kind", string "is_infringed")
                      ,("target", tokenValue (ruleId exception))])
                    ,("effect", string "defeat")]
                  registry =
                    [object [("id", tokenValue (ruleId offence)), ("source_id", tokenValue sourceId)
                      ,("program", program (rulePath offence) text
                        (tokenValue (ruleProgram offence)) offenceRoot)
                      ,("exceptions", array [binding])]
                    ,object [("id", tokenValue (ruleId exception)), ("source_id", tokenValue sourceId)
                      ,("program", program (rulePath exception) text
                        (tokenValue (ruleProgram exception)) exceptionRoot)
                      ,("exceptions", array [])]]
                  exceptionIds = Set.fromList
                    (map (tokenText . elementId) (ruleElements exception))
                  fact (key, value) = factValue (Set.member (tokenText key) exceptionIds)
                    "synthetic research fixture" (tokenText statusId) burden (key, value)
              pure (baseRequest model (ruleId offence)
                [sourceValue sourceId sourcePath text,
                 sourceValue statusId statusPath statusBytes]
                registry (object (map fact assignments)))
            _ -> at "SFE040" "<lower>" target "selected attachment is not unique"
        _ -> at "SFE036" "<lower>" (modelIdentifier model)
          "one scenario analysis target required"
  pure (encodeJson request)
  where
    sourceRole = case modelBody model of
      Section _ _ _ _ _ _ _ -> "excerpt"
      Synthetic _ _ _ -> "source_text"
      Legal _ _ _ _ -> "source_text"
      MultiLegal _ _ _ _ _ -> "source_text"
      DefinitionsLegal _ _ _ _ _ _ -> "source_text"
    BurdenAnnotation _ holder kind _ = modelBurden model
    burden = object [("holder", tokenValue holder), ("kind", tokenValue kind)]

baseRequest :: Model -> Token -> [J] -> [J] -> J -> J
baseRequest model root sources registry facts = object
  [("protocol", string "yuho.kernel-protocol/v1")
  ,("request_id", tokenValue (modelRequest model))
  ,("operation", string "evaluate")
  ,("input_schema", string "yuho.kernel-input/v1")
  ,("fragment", tokenValue (modelVariant model))
  ,("root_rule", tokenValue root)
  ,("policy", object [("max_nodes", JNum 1024), ("reference_date", tokenValue (modelDate model))])
  ,("sources", array sources), ("registry", array registry), ("facts", facts)]
