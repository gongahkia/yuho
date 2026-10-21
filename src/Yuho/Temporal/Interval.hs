{-# LANGUAGE OverloadedStrings #-}
-- | Pure temporal policy shared by file-based and graph authoring adapters.
module Yuho.Temporal.Interval (Interval(..), parseDate, intervalProblem, orderIntervals, matchIntervals) where
import Data.List (sortOn)
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (Day, defaultTimeLocale, parseTimeM)

data Interval a = Interval { intervalObject :: a, intervalStart :: Day, intervalEnd :: Maybe Day }
  deriving (Eq, Show)
parseDate :: Text -> Maybe Day
parseDate = parseTimeM True defaultTimeLocale "%F" . T.unpack

-- | The caller checks cardinality, IDs and individual dates first. Error object
-- is the later expression, matching the established Surface.Temporal contract.
intervalProblem :: [Interval a] -> Maybe (a,Text)
intervalProblem [] = Nothing
intervalProblem [_] = Nothing
intervalProblem (Interval _ _ Nothing:Interval next _ _:_) = Just (next,"open-ended expression overlaps a later expression")
intervalProblem (Interval _ _ (Just finish):rest@(Interval next from _:_))
  | finish < from = Just (next,"gap between authored effective intervals")
  | finish > from = Just (next,"overlapping authored effective intervals")
  | otherwise = intervalProblem rest
orderIntervals :: [Interval a] -> [Interval a]
orderIntervals = sortOn intervalStart
matchIntervals :: Day -> [Interval a] -> [a]
matchIntervals day xs = [x | Interval x from to <- xs, from <= day, maybe True (day <) to]
