module Json (J(..), parseJson, encodeJson, field, object) where

import Data.Char (chr, digitToInt, isControl)
import Data.List (intercalate, sortOn)
import Numeric (showHex)
import Text.Parsec
import Text.Parsec.String (Parser)

data J = JNull | JBool Bool | JNum Integer | JStr String | JArr [J] | JObj [(String, J)]
  deriving (Eq, Show)

parseJson :: String -> Either String J
parseJson source =
  case parse (white *> value <* white <* eof) "request" source of
    Left err -> Left (show err)
    Right result -> if uniqueObjects result then Right result else Left "duplicate JSON object key"

uniqueObjects :: J -> Bool
uniqueObjects (JObj pairs) =
  let keys = map fst pairs
  in length keys == length (unique keys) && all (uniqueObjects . snd) pairs
uniqueObjects (JArr items) = all uniqueObjects items
uniqueObjects _ = True

unique :: Eq a => [a] -> [a]
unique = foldr (\item rest -> if elem item rest then rest else item : rest) []

white :: Parser ()
white = skipMany (oneOf " \t\r\n")

lexeme :: Parser a -> Parser a
lexeme parser = parser <* white

value :: Parser J
value = choice
  [ JNull <$ try (string "null")
  , JBool True <$ try (string "true")
  , JBool False <$ try (string "false")
  , JStr <$> jsonString
  , JArr <$> between (lexeme (char '[')) (char ']') (value `sepBy` lexeme (char ','))
  , JObj <$> between (lexeme (char '{')) (char '}') (pair `sepBy` lexeme (char ','))
  , JNum <$> number
  ] <* white

pair :: Parser (String, J)
pair = do
  key <- jsonString
  white
  _ <- lexeme (char ':')
  item <- value
  pure (key, item)

number :: Parser Integer
number = do
  sign <- optionMaybe (char '-')
  digits <- (:) <$> oneOf "123456789" <*> many digit <|> string "0"
  let magnitude = foldl (\acc d -> acc * 10 + toInteger (digitToInt d)) 0 digits
  pure (if sign == Just '-' then negate magnitude else magnitude)

jsonString :: Parser String
jsonString = char '"' *> many charInString <* char '"'

charInString :: Parser Char
charInString = escaped <|> satisfy (\c -> c /= '"' && c /= '\\' && not (isControl c))

escaped :: Parser Char
escaped = do
  _ <- char '\\'
  choice
    [ char '"' *> pure '"'
    , char '\\' *> pure '\\'
    , char '/' *> pure '/'
    , char 'b' *> pure '\b'
    , char 'f' *> pure '\f'
    , char 'n' *> pure '\n'
    , char 'r' *> pure '\r'
    , char 't' *> pure '\t'
    , char 'u' *> unicodeEscape
    ]

unicodeEscape :: Parser Char
unicodeEscape = do
  digits <- count 4 hexDigit
  let codepoint = foldl (\acc d -> acc * 16 + digitToInt d) 0 digits
  if codepoint >= 0xd800 && codepoint <= 0xdfff
    then fail "surrogate escape is unsupported"
    else pure (chr codepoint)

encodeJson :: J -> String
encodeJson JNull = "null"
encodeJson (JBool True) = "true"
encodeJson (JBool False) = "false"
encodeJson (JNum numberValue) = show numberValue
encodeJson (JStr valueText) = "\"" ++ concatMap encodeChar valueText ++ "\""
encodeJson (JArr items) = "[" ++ intercalate "," (map encodeJson items) ++ "]"
encodeJson (JObj pairs) =
  "{" ++ intercalate "," [encodeJson (JStr key) ++ ":" ++ encodeJson item
                         | (key, item) <- sortOn fst pairs] ++ "}"

encodeChar :: Char -> String
encodeChar '"' = "\\\""
encodeChar '\\' = "\\\\"
encodeChar '\b' = "\\b"
encodeChar '\f' = "\\f"
encodeChar '\n' = "\\n"
encodeChar '\r' = "\\r"
encodeChar '\t' = "\\t"
encodeChar character
  | fromEnum character < 32 =
      let hex = showHex (fromEnum character) ""
      in "\\u" ++ replicate (4 - length hex) '0' ++ hex
  | otherwise = [character]

field :: String -> J -> Either String J
field name (JObj pairs) =
  case lookup name pairs of
    Just item -> Right item
    Nothing -> Left ("missing field " ++ name)
field _ _ = Left "expected object"

object :: [(String, J)] -> J
object = JObj
