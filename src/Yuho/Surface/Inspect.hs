{-# LANGUAGE OverloadedStrings #-}
-- Opt-in, non-evaluating compiler inspection. Not an authoring interchange format.
module Yuho.Surface.Inspect (inspectSource, inspectionVersion) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Yuho.Core.Types as Kernel
import Yuho.CoreYuho.Normalize (normalizeCheckedStructure)
import qualified Yuho.CoreYuho.Types as Core
import Yuho.CoreYuho.TypedFinite (finiteProgramId)
import Yuho.Exception.Types (Truth(..))
import Yuho.Presumption.Decode (decodePresumptionRequest)
import Yuho.Presumption.Validate (validatePresumptionRequest)
import qualified Yuho.Presumption.Types as Presumption
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json
import Yuho.Surface.AST hiding (identifier)
import Yuho.Surface.Compile (checkParsed)
import Yuho.Surface.InspectionData (locatedToken, sourceRecord)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Modules (AuthoredModel(..))
import Yuho.Surface.Parser (parseModel, parseScenario)
import Yuho.Surface.Presumption
import Yuho.Surface.Token
import Yuho.Surface.TypedFinite

inspectionVersion :: Text
inspectionVersion = "yuho.compiler-inspection/v0.1-experimental"

-- A selected stage executes only its prerequisites. 'all' lists supported stages;
-- an explicitly requested unavailable stage is an error, never an empty success.
inspectSource :: Text -> FilePath -> BS.ByteString -> Maybe (FilePath,BS.ByteString)
  -> IO (Either Diagnostic J)
inspectSource wanted path bytes scenario
  | wanted `notElem` ["all","parsed","checked","normalized","lowered"] =
      pure (at "SFI001" path origin "unknown inspection stage; expected parsed, checked, normalized, lowered or all")
  | BS.isPrefixOf "{" (BS.dropWhile (`elem` [9,10,13,32]) bytes) =
      pure (at "SFI002" path origin
        "inspect accepts .yh source, not SDK authoring or kernel JSON; use the profile-specific public decoder")
  | otherwise = case lexSource path bytes of
      Left issue -> pure (Left issue)
      Right (first:_) -> case tokenText first of
        "model" -> pure proof
        "typed-rules-model" -> pure typed
        "presumption-program" -> presumption
        _ -> pure (at "SFI002" path first
          "inspection supports direct proof models, ground typed-rules-model and presumption-program; wrappers, imports and SDK JSON are not inspection inputs")
      Right [] -> pure (at "SFI002" path origin "empty inspection input")
  where
    origin = Token EndToken "" 1 1
    loc = locatedToken path bytes
    sources = sourceRecord path bytes : maybe [] (\(p,b) -> [sourceRecord p b]) scenario
    record fragment sourceRows stages unavailable = JObj
      [("format",JStr inspectionVersion),("fragment",JStr fragment)
      ,("evaluated",JBool False),("sources",JArr sourceRows)
      ,("coordinates",JObj [("offsets",JStr "zero-based UTF-8 bytes")
        ,("lines_columns",JStr "one-based; columns count UTF-8 bytes, not display cells")
        ,("source_locations",JStr "token starts only; LF source; no invented end spans")
        ,("kernel_spans",JStr "generated source, zero-based half-open UTF-8 bytes")])
      ,("stages",JArr [s | (name,s) <- stages, wanted == "all" || wanted == name])
      ,("unavailable_stages",JArr [JObj [("stage",JStr name),("reason",JStr reason)]
        | (name,reason) <- unavailable])]
    stage name representation dependencies value = (name,JObj
      [("stage",JStr name),("representation",JStr representation)
      ,("depends_on",JArr (map JStr dependencies)),("data",value)])
    parsedStage representation value = stage "parsed" representation [] value
    normalizedReason = "this pipeline has no separate pre-evaluation normalized representation"
    noNormalized = [("normalized",normalizedReason)]
    refuseNormalized = if wanted == "normalized"
      then at "SFI003" path origin normalizedReason else Right ()
    proof = do
      model <- parseModel path bytes
      modelData <- proofParsed path bytes model
      parsedScenario <- traverse (\(p,b) -> do
        _ <- parseScenario p b
        ts <- lexSource p b
        pure (JArr (map (locatedToken p b) ts))) scenario
      let parsed = appendField "scenario_tokens" (maybe JNull id parsedScenario) modelData
          fragment = tokenText (modelVariant model)
          initial = parsedStage "Surface.Model (bounded source declarations)" parsed
      if wanted == "parsed" then Right (record fragment sources [initial] []) else do
        checked@(Checked _ _ assignments first second) <- checkParsed path model scenario
        let trees = first : maybe [] (:[]) second
            checkedData = JObj [("requirements",JArr (map (resolvedJson loc) trees))
              ,("assignments",JArr [JObj [("input",JStr (tokenText token))
                ,("location",assignmentLocation token),("supplied",proofJson value)]
                | (token,value) <- assignments])]
            checkedStage = stage "checked" "Surface.Checked / Resolved" ["parsed"] checkedData
            normalized = normalizeCheckedStructure (AuthoredModel model Nothing [] [] []) checked
            normalizedStage = stage "normalized" "CoreProgram structural diagram branch" ["checked"]
              (coreJson normalized)
            prefix = [initial,checkedStage]
        case wanted of
          "checked" -> Right (record fragment sources prefix [])
          "normalized" -> Right (record fragment sources (prefix ++ [normalizedStage]) [])
          _ -> do
            request <- lowerChecked checked
            value <- json request
            let lowered = stage "lowered" "kernel request (not executed)" ["checked"]
                  (loweredJson request value (proofMappings loc trees value))
            Right (record fragment sources (prefix ++ [normalizedStage,lowered]) [])
    assignmentLocation token = case scenario of
      Just (p,b) -> locatedToken p b token
      Nothing -> loc token
    typed = do
      modelData <- inspectTypedFiniteModel path bytes
      scenarioData <- traverse (uncurry inspectTypedFiniteScenario) scenario
      let parsed = appendField "scenario" (maybe JNull id scenarioData) modelData
      refuseNormalized
      let initial = parsedStage "Surface.RawModel declarations" parsed
      if wanted == "parsed" then Right (record "TypedFiniteRules-v1" sources [initial] noNormalized)
      else do
        program <- prepareTypedFiniteInspection path bytes scenario
        let request = encodeTypedFiniteRequest (typedRequestId (finiteProgramId program)) program
        value <- json request
        let checkedStage = stage "checked" "TypedFiniteProgram" ["parsed"]
              (field "program" value)
            mappings = typedMappings parsed value
            lowered = stage "lowered" "kernel request (not executed)" ["checked"]
              (loweredJson request value mappings)
        Right (record "TypedFiniteRules-v1" sources [initial,checkedStage,lowered] noNormalized)
    presumption = case parsePresumptionSource path bytes of
      Left issue -> pure (Left issue)
      Right parsed -> case refuseNormalized >> noScenario of
        Left issue -> pure (Left issue)
        Right () | wanted == "parsed" -> pure (Right (record
          "RegisteredPresumptionDerivations-v1" sources
          [parsedStage "Surface.PresumptionSource" (presumptionSourceJson path bytes parsed)] noNormalized))
        Right () -> do
          prepared <- preparePresumptionProgram path bytes
          pure $ do
            item <- prepared
            baseModel <- parseModel (preparedModelPath item) (preparedModelBytes item)
            _ <- proofParsed (preparedModelPath item) (preparedModelBytes item) baseModel
            value <- json (preparedRequest item)
            let sourceRows = sources ++
                  [sourceRecord (preparedModelPath item) (preparedModelBytes item)
                  ,sourceRecord (preparedScenarioPath item) (preparedScenarioBytes item)]
                registrations = presumptionSourceRegistrations parsed
                mappings = [JObj [("category",JStr "registration"),("authored",loc identifier)
                    ,("kernel_pointer",JStr ("/presumptions/" <> Text.pack (show index)))
                    ,("kernel_id",JStr (tokenText identifier))]
                  | (index,Registration identifier _ _ _ _) <- zip [0::Int ..] registrations]
                Checked _ _ _ first second = preparedChecked item
                baseMappings = proofMappings
                  (locatedToken (preparedModelPath item) (preparedModelBytes item))
                  (first : maybe [] (:[]) second) value
                initial = parsedStage "Surface.PresumptionSource" (presumptionSourceJson path bytes parsed)
                lowered = stage "lowered" "proof-checked base plus registered kernel request (not executed)" ["parsed"]
                  (loweredJson (preparedRequest item) value (mappings ++ baseMappings))
                result stages = record "RegisteredPresumptionDerivations-v1" sourceRows stages noNormalized
            -- Registration checking is the backend's validation of the lowered
            -- request, not a fictitious frontend Checked representation.
            if wanted == "lowered" then Right (result [initial,lowered]) else do
              validated <- either (backendIssue (presumptionSourceName parsed)) Right
                (decodePresumptionRequest value >>= validatePresumptionRequest)
              let checkedStage = stage "checked" "ValidatedPresumption registration index" ["lowered"]
                    (JObj [("registrations",field "presumptions" value)
                      ,("by_target",JObj [(target,JArr (map (JStr . Presumption.registrationId) rules))
                        | (target,rules) <- Map.toAscList (Presumption.presumptionByTarget validated)])
                      ,("base_request",field "registry" value)])
              Right (result [initial,lowered,checkedStage])
    noScenario = case scenario of
      Nothing -> Right ()
      Just _ -> at "SFI002" path origin "presumption-program retains its own base-scenario; --scenario is unsupported"
    json = either (at "SFI004" path origin) Right . decodeJson
    backendIssue token issue = at "SFR004" path token
      ("presumption validation: " <> Kernel.diagCode issue <> " at " <> Kernel.diagPath issue
       <> "; " <> Text.intercalate "; " [k <> "=" <> v | (k,v) <- Kernel.diagParameters issue])

appendField :: Text -> J -> J -> J
appendField key value (JObj fields) = JObj (fields ++ [(key,value)])
appendField _ _ value = value

field :: Text -> J -> J
field name = maybe JNull id . lookupField name

loweredJson :: BS.ByteString -> J -> [J] -> J
loweredJson request value mappings = JObj
  [("request",value),("request_sha256",JStr (sha256Text request))
  ,("mappings",JArr mappings),("executed",JBool False)]

proofJson :: Proof -> J
proofJson value = case value of
  Proved -> JObj [("kind",JStr "proved")]
  NotProved -> JObj [("kind",JStr "not_proved")]
  Unresolved reason -> JObj [("kind",JStr "unresolved"),("reason",JStr reason)]

resolvedJson :: (Token -> J) -> Resolved -> J
resolvedJson loc tree = case tree of
  ResolvedLeaf token quote -> JObj [("kind",JStr "input"),("id",loc token),("quote",loc quote)]
  ResolvedGroup token combinator members -> JObj
    [("kind",JStr (combinatorName combinator)),("id",loc token)
    ,("members",JArr (map (resolvedJson loc) members))]

combinatorName :: Combinator -> Text
combinatorName All = "all"
combinatorName Any = "any"

proofParsed :: FilePath -> BS.ByteString -> Model -> Either Diagnostic J
proofParsed path bytes model = do
  body <- case modelBody model of
    Section section rule program sourcePath root propositions assignments -> Right (JObj
      [("kind",JStr "section"),("section",loc section),("rule",loc rule),("program",loc program)
      ,("path",loc sourcePath),("root",loc root),("propositions",JArr (map proposition propositions))
      ,("assignments",JArr [JObj [("id",loc i),("status",loc s),("reason",maybe JNull loc r)]
        | Assignment i s r <- assignments])])
    Synthetic offence exception outputs -> Right (JObj
      [("kind",JStr "synthetic"),("rules",JArr (map ruleJson [offence,exception]))
      ,("outputs",JArr [JObj [("kind",loc k),("target",loc t)] | TechnicalOutput k t <- outputs])])
    _ -> unsupported
  if null (modelCandidatePenalties model) then pure () else at "SFI002" path (modelIdentifier model) "candidate penalties are not inspected in this round"
  let BurdenAnnotation a b c d = modelBurden model
  pure (JObj [("id",loc (modelIdentifier model)),("variant",loc (modelVariant model))
    ,("jurisdiction",loc (modelJurisdiction model)),("purpose",loc (modelPurpose model))
    ,("request",loc (modelRequest model)),("reference_date",loc (modelDate model))
    ,("limit",loc (modelLimit model)),("body",body)
    ,("burden",JArr (map loc [a,b,c,d]))
    ,("sources",JArr [JObj [("id",loc i),("kind",loc k),("locator",loc l)]
      | SourceDecl i k l <- modelSources model])
    ,("quotes",JArr [JObj [("id",loc i),("text",loc t)] | (i,t) <- modelQuotes model])
    ,("limitations",JArr (map loc (modelLimitations model)))])
  where
    loc = locatedToken path bytes
    unsupported = at "SFI002" path (modelIdentifier model)
      "proof inspection currently supports Section and Synthetic bodies without candidate penalties; use existing compile/explain/diagram for other proof forms"
    proposition (Leaf i p q note) = JObj [("kind",JStr "leaf"),("id",loc i)
      ,("proposition",maybe JNull loc p),("quote",loc q),("note",maybe JNull loc note)]
    proposition (Group i c children) = JObj [("kind",JStr (combinatorName c))
      ,("id",loc i),("members",JArr (map loc children))]
    ruleJson rule = JObj [("id",loc (ruleIdentifier rule)),("kind",loc (ruleKindSource rule))
      ,("technical_id",loc (ruleId rule)),("program",loc (ruleProgram rule))
      ,("target",maybe JNull loc (ruleTarget rule)),("path",loc (rulePath rule))
      ,("sections",JArr [loc t | StatutorySection t <- ruleSections rule])
      ,("elements",JArr [JObj [("id",loc (elementId e)),("category",loc (elementCategorySource e))
        ,("quote",loc (elementQuote e)),("support",maybe JNull loc (elementSupport e))]
        | e <- ruleElements rule])
      ,("groups",JArr (map proposition (ruleGroups rule)))]

-- Correspondence is limited to resolved requirement identities emitted unchanged
-- by Lower, not arbitrary overlapping origins or display labels. Each occurrence
-- is identified by its JSON pointer; generated spans remain in the request.
proofMappings :: (Token -> J) -> [Resolved] -> J -> [J]
proofMappings loc trees request = concatMap visitRegistry (indexed (field "registry" request))
  where
    declarations = concatMap flatten trees
    flatten (ResolvedLeaf token _) = [(tokenText token,token)]
    flatten (ResolvedGroup token _ members) = (tokenText token,token) : concatMap flatten members
    visitRegistry (index,row) = concatMap (uncurry (walk (field "source_id" row) ("/registry/" <> index <> "/program/requirements")))
      (indexed (field "requirements" (field "program" row)))
    walk source prefix index node =
      [JObj [("category",JStr "requirement"),("authored",loc token)
        ,("kernel_id",JStr name),("kernel_pointer",JStr pointer)
        ,("generated_span",field "span" node),("generated_source_id",source)]
      | (name,token) <- declarations, field "id" node == JStr name]
      ++ concatMap (uncurry (walk source (pointer <> "/members"))) (indexed (field "members" node))
      where pointer = prefix <> "/" <> index

indexed :: J -> [(Text,J)]
indexed (JArr values) = zip (map (Text.pack . show) [0::Int ..]) values
indexed _ = []

typedMappings :: J -> J -> [J]
typedMappings parsed request = concat
  [ [JObj [("category",JStr category),("authored",field "id" declaration)
      ,("kernel_id",field "id" row),("kernel_pointer",JStr ("/program/" <> category <> "/" <> index))]
    | declaration <- rows (field category parsed), (index,row) <- indexed (field category program)
    , field "text" (field "id" declaration) == field "id" row]
  | category <- ["entities","predicates","scalars","requirements","rules"]]
  where
    program = field "program" request
    rows (JArr values) = values
    rows _ = []

coreJson :: Core.CoreProgram -> J
coreJson program = JObj
  [("id",JStr (Core.coreProgramId program)),("jurisdiction",JStr (Core.coreProgramJurisdiction program))
  ,("roots",JArr (map requirement (Core.coreProgramRoots program)))
  ,("rules",JArr [JObj [("id",JStr (Core.coreRuleId r)),("technical_id",JStr (Core.coreRuleTechnicalId r))
      ,("kind",JStr (ruleKindName (Core.coreRuleKind r)))
      ,("sections",JArr (map JStr (Core.coreRuleSections r)))
      ,("elements",JArr [JObj [("id",JStr (Core.coreElementId e))
        ,("category",JStr (Core.coreElementCategory e)),("citation",JStr (Core.coreElementCitation e))]
        | e <- Core.coreRuleElements r])
      ,("requirements",JArr (map requirement (Core.coreRuleRequirements r)))]
    | r <- Core.coreProgramRules program])
  ,("attachments",JArr [JObj [("id",JStr (Core.coreAttachmentId a))
    ,("exception",JStr (Core.coreAttachmentException a)),("target",JStr (Core.coreAttachmentTarget a))
    ,("actor",maybe JNull JStr (Core.coreAttachmentActor a))
    ,("role",maybe JNull JStr (Core.coreAttachmentRole a))
    ,("context",maybe JNull JStr (Core.coreAttachmentContext a))] | a <- Core.coreProgramAttachments program])
  ,("supplied_assignments",JObj [(k,JStr (truth v)) | (k,v) <- Map.toAscList (Core.coreProgramAssignments program)])
  ,("limitations",JArr (map JStr (Core.coreProgramLimitations program)))
  ,("purpose",JStr "structural diagram normalization; lowering consumes Checked directly")
  ,("observations",JNull)]
  where
    ruleKindName Core.CoreOffence = "offence"
    ruleKindName Core.CoreException = "exception"
    ruleKindName Core.CoreParticipation = "participation"
    ruleKindName Core.CoreAttempt = "attempt"
    requirement (Core.CoreInput i quote value) = JObj [("kind",JStr "input"),("id",JStr i)
      ,("quote",JStr quote),("supplied",maybe JNull (JStr . truth) value)]
    requirement (Core.CoreAll i children) = group "all" i children
    requirement (Core.CoreAny i children) = group "any" i children
    group kind i children = JObj [("kind",JStr kind),("id",JStr i),("members",JArr (map requirement children))]
    truth TrueValue = "satisfied"
    truth FalseValue = "not_satisfied"
    truth UnresolvedValue = "unresolved"
