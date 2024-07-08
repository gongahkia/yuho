module YuhoREPL where

import System.Console.Haskeline
import Text.Parsec (parse)
import Parser (parseProgram)
import AST (Statement)

-- main execution code

startYuhoREPL :: IO ()
startYuhoREPL = runInputT defaultSettings loop
  where
    loop :: InputT IO ()
    loop = do
        minput <- getInputLine "Yuho > "
        case minput of
            Nothing -> outputStrLn "Goodbye."
            Just input -> do
                processInput input
                loop

processInput :: String -> InputT IO ()
processInput input = do
    case parse parseProgram "" input of
        Left err -> outputStrLn $ "Error: " ++ show err
        Right program -> outputStrLn $ "Parsed program: " ++ show program
