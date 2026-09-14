{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Case
  ( CheckedCase(..), CheckedIssue(..), caseModelFile, checkAnalysisCase
  , compileAnalysisCase, runAnalysisCase, explainAnalysisCase ) where

import qualified Data.ByteString as BS
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import System.FilePath (isAbsolute, takeDirectory, takeExtension, takeFileName, (</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.CaseFacts
  ( ResolvedCaseFact, caseFactsExplanation, caseFactsValue, checkSharedShapes
  , expandCaseFacts, validateCaseFacts )
import Yuho.Surface.Check (checkModel)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Token

data CheckedIssue = CheckedIssue CaseAllegation Checked BS.ByteString
data CheckedCase = CheckedCase FilePath Token Model [ResolvedCaseFact] [CheckedIssue]

caseModelFile :: FilePath -> AnalysisCase -> Either Diagnostic FilePath
caseModelFile path (AnalysisCase _ location _ _ _) =
  let name = Text.unpack (tokenText location) in
  if not (null name) && not (isAbsolute name) && takeFileName name == name
      && takeExtension name == ".yh" && name /= "." && name /= ".."
    then pure (takeDirectory path </> name)
    else at "SFE106" path location "case model must be a sibling .yh file"

checkAnalysisCase :: FilePath -> AnalysisCase -> FilePath -> Model
  -> Either Diagnostic CheckedCase
checkAnalysisCase casePath declaration@(AnalysisCase caseId _ bindings facts allegations)
  modelPath model = do
  declaredModelPath <- caseModelFile casePath declaration
  if declaredModelPath == modelPath then pure () else
    at "SFE106" casePath caseId "case model path does not match supplied model"
  if "case:" `Text.isPrefixOf` tokenText caseId then pure () else
    at "SFE106" casePath caseId "typed case identifier required"
  _ <- checkModel modelPath model Nothing
  (offence, participation, attempt) <- case modelBody model of
    AbetmentLegal _ _ _ _ candidate abetment attemptDefinition _ _ _ _ ->
      pure (ruleIdentifier candidate, ruleIdentifier (abetmentRule abetment),
        ruleIdentifier (attemptRule attemptDefinition))
    _ -> at "SFE106" casePath caseId
      "bounded case requires the authored offence, abetment and attempt model"
  if length allegations == 3 &&
      Set.fromList [kind | CaseAllegation _ kind _ _ _ _ <- allegations] ==
        Set.fromList [CaseOffence,CaseParticipation,CaseAttempt]
    then pure () else at "SFE106" casePath caseId
      "one offence, one participation and one attempt allegation required"
  let ids = [tokenText item | CaseAllegation item _ _ _ _ _ <- allegations]
  if length (Set.fromList ids) == 3 && all ("a:" `Text.isPrefixOf`) ids then
    pure () else at "SFE106" casePath caseId "duplicate or invalid allegation ID"
  let ordered = [item | kind <- [CaseOffence,CaseParticipation,CaseAttempt],
        item@(CaseAllegation _ actual _ _ _ _) <- allegations, actual == kind]
  resolvedFacts <- validateCaseFacts casePath bindings facts ordered
  checkSharedShapes casePath model bindings ordered resolvedFacts
  issues <- mapM (checkIssue offence participation attempt) ordered
  pure (CheckedCase casePath caseId model resolvedFacts issues)
  where
    checkIssue offence participation attempt allegation@(CaseAllegation item kind target role _ _) = do
      let (wantedTarget,wantedRole) = case kind of
            CaseOffence -> (offence,"role:principal")
            CaseParticipation -> (participation,"role:alleged-abettor")
            CaseAttempt -> (attempt,"role:alleged-attempter")
      if tokenText target == tokenText wantedTarget && tokenText role == wantedRole
        then pure () else at "SFE107" casePath target
          "allegation target or actor role does not match its typed issue"
      expanded <- expandCaseFacts casePath model bindings facts allegation
      scenario <- case expanded of
        ActorScopedScenario _ _ [] observations [] actorRows relationRows stageRows
          completions scopedRows [] acknowledgements ->
            pure (ActorScopedScenario (modelRequest model) (modelIdentifier model)
              [target] observations bindings actorRows relationRows stageRows completions
              scopedRows [] acknowledgements)
        _ -> at "SFE107" casePath item
          "allegation requires scoped inputs; bindings belong to the case"
      checked <- case checkModel modelPath model (Just (casePath,scenario)) of
        Left issue | not (null facts) && diagnosticCode issue == "SFE009" ->
          atRelated "SFE118" casePath item
            "allegation primitive classifications are incomplete after fact expansion"
            modelPath target
        result -> result
      request <- lowerChecked checked
      pure (CheckedIssue allegation checked request)

issueValue :: CheckedIssue -> (CaseTargetKind, Token, Token)
issueValue (CheckedIssue (CaseAllegation item kind target _ _ _) _ _) =
  (kind,item,target)

kindText :: CaseTargetKind -> Text
kindText CaseOffence = "offence"
kindText CaseParticipation = "participation"
kindText CaseAttempt = "attempt"

requestValue :: FilePath -> CheckedIssue -> Either Diagnostic J
requestValue path (CheckedIssue (CaseAllegation item _ _ _ _ _) _ bytes) =
  case decodeJson bytes of
    Right value -> pure value
    Left _ -> at "SFE108" path item "compiled issue request is not JSON"

compileAnalysisCase :: CheckedCase -> Either Diagnostic BS.ByteString
compileAnalysisCase (CheckedCase path caseId model facts issues) = do
  rows <- mapM (\issue -> do
    request <- requestValue path issue
    let (kind,item,target) = issueValue issue
    pure (JObj [("id",JStr (tokenText item)),("kind",JStr (kindText kind)),
      ("target",JStr (tokenText target)),("request",request)])) issues
  pure (encodeJson (JObj ([("format",JStr "yuho.case-input/v0.1"),
    ("case_id",JStr (tokenText caseId)),
    ("model_id",JStr (tokenText (modelIdentifier model))),
    ("scope",JStr "synthetic_research_only"),
    ("issues",JArr rows)] ++ factFields facts)))

runAnalysisCase :: CheckedCase -> Either Diagnostic BS.ByteString
runAnalysisCase (CheckedCase path caseId model facts issues) = do
  rows <- mapM runIssue issues
  pure (encodeJson (JObj ([("format",JStr "yuho.case-result/v0.1"),
    ("case_id",JStr (tokenText caseId)),
    ("model_id",JStr (tokenText (modelIdentifier model))),
    ("scope",JStr "synthetic_research_only"),
    ("issues",JArr rows)] ++ factFields facts)) <> "\n")
  where
    runIssue issue@(CheckedIssue (CaseAllegation item _ _ _ _ _) _ request) = do
      _ <- requestValue path issue
      response <- case decodeJson (runLine request) of
        Right value -> pure value
        Left _ -> at "SFE108" path item "kernel response is not JSON"
      status <- case lookupField "status" response >>= textValue of
        Just value | value /= "rejected" -> pure value
        _ -> at "SFE108" path item "kernel rejected a checked issue"
      let (kind,_,target) = issueValue issue
      pure (JObj [("id",JStr (tokenText item)),("kind",JStr (kindText kind)),
        ("target",JStr (tokenText target)),("status",JStr status),
        ("result",response)])

explainAnalysisCase :: FilePath -> CheckedCase -> Either Diagnostic Text
explainAnalysisCase modelPath (CheckedCase _ caseId _ facts issues) = do
  parts <- mapM explainIssue issues
  pure (Text.unlines (["Analysis case: " <> tokenText caseId,
    "Three independent technical issues; no aggregate case status."] ++
    (if null facts then [] else [caseFactsExplanation facts]) ++ parts ++
    ["No guilt, conviction, acquittal, liability or sentence was determined."]))
  where
    explainIssue (CheckedIssue (CaseAllegation item kind target role _ _) checked _) = do
      detail <- explainChecked modelPath checked
      pure ("\nAllegation " <> tokenText item <> " — " <> kindText kind <>
        " " <> tokenText target <> " for " <> tokenText role <> "\n" <> detail)

factFields :: [ResolvedCaseFact] -> [(Text,J)]
factFields [] = []
factFields facts = [("supplied_facts",caseFactsValue facts)]
