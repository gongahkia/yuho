{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.Registry (publicConstructs) where

import Data.Text (Text)

-- Kept in code so the conformance test can reject registry drift.
publicConstructs :: [Text]
publicConstructs =
  [ "model", "scenario", "source", "quote", "scope-assumption"
  , "burden-annotation", "technical-output", "primitive-input"
  , "requirement-all", "requirement-any", "statutory-definition"
  , "definition-reference", "derived-output", "mental-state-target"
  , "offence", "general-exception", "exception-attachment"
  , "actor", "role", "relationship", "actor-scoped-exception"
  , "participation", "s107-instigation", "s107-conspiracy"
  , "s107-intentional-aid", "attempt", "conduct-stage"
  , "target-completion", "candidate-penalty", "penalty-term"
  , "registered-presumption", "statutory-module", "module-import"
  , "module-export", "qualified-reference", "temporal-expression"
  , "conduct-date", "analysis-case", "allegation", "shared-fact"
  , "fact-binding", "limitation"
  ]
