{-# LANGUAGE OverloadedStrings #-}

module Euclid.Import.GEDCOM
    ( importGedcomToEuclid
    ) where

import Data.List (foldl', sortOn)
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

data GedcomPerson = GedcomPerson
    { gpId :: Text
    , gpName :: Maybe Text
    , gpSex :: Maybe Text
    , gpBirth :: Maybe Text
    , gpDeath :: Maybe Text
    }

data GedcomFamily = GedcomFamily
    { gfId :: Text
    , gfHusband :: Maybe Text
    , gfWife :: Maybe Text
    , gfChildren :: [Text]
    }

data CurrentRecord
    = CurrentNone
    | CurrentPerson Text
    | CurrentFamily Text

data PendingTag
    = PendingBirth
    | PendingDeath
    | PendingNone

data GedcomState = GedcomState
    { gsCurrent :: CurrentRecord
    , gsPending :: PendingTag
    , gsPeople :: Map Text GedcomPerson
    , gsFamilies :: Map Text GedcomFamily
    }

importGedcomToEuclid :: Text -> Either [Diagnostic] Text
importGedcomToEuclid input
    | null persons =
        Left
            [ Diagnostic DiagnosticError "import:gedcom" "no INDI records found in GEDCOM input" Nothing
            ]
    | otherwise =
        Right $
            T.unlines $
                [ "timeline gedcom_import {"
                , "    kind: linear,"
                , "    start: 1900-01-01,"
                , "    end: 2100-12-31,"
                , "}"
                , ""
                ]
                    ++ concatMap renderPerson persons
                    ++ renderRelationships people families
  where
    finalState = collectGedcom (T.lines input)
    people = gsPeople finalState
    families = gsFamilies finalState
    persons = sortOn gpId (Map.elems people)

collectGedcom :: [Text] -> GedcomState
collectGedcom =
    foldl' step initialState
  where
    initialState =
        GedcomState
            { gsCurrent = CurrentNone
            , gsPending = PendingNone
            , gsPeople = Map.empty
            , gsFamilies = Map.empty
            }

    step state lineValue =
        case T.words (T.strip lineValue) of
            ["0", recordId, "INDI"] ->
                state
                    { gsCurrent = CurrentPerson (normalizeRecordId recordId)
                    , gsPending = PendingNone
                    , gsPeople =
                        Map.insertWith
                            (\_ existing -> existing)
                            (normalizeRecordId recordId)
                            emptyPerson
                            (gsPeople state)
                    }
              where
                emptyPerson =
                    GedcomPerson
                        { gpId = normalizeRecordId recordId
                        , gpName = Nothing
                        , gpSex = Nothing
                        , gpBirth = Nothing
                        , gpDeath = Nothing
                        }
            ["0", recordId, "FAM"] ->
                state
                    { gsCurrent = CurrentFamily (normalizeRecordId recordId)
                    , gsPending = PendingNone
                    , gsFamilies =
                        Map.insertWith
                            (\_ existing -> existing)
                            (normalizeRecordId recordId)
                            emptyFamily
                            (gsFamilies state)
                    }
              where
                emptyFamily =
                    GedcomFamily
                        { gfId = normalizeRecordId recordId
                        , gfHusband = Nothing
                        , gfWife = Nothing
                        , gfChildren = []
                        }
            ("1" : "NAME" : restWords) ->
                updateCurrentPerson state (\person -> person{gpName = Just (cleanName (T.unwords restWords))})
            ["1", "SEX", sexValue] ->
                updateCurrentPerson state (\person -> person{gpSex = Just sexValue})
            ["1", "BIRT"] ->
                state{gsPending = PendingBirth}
            ["1", "DEAT"] ->
                state{gsPending = PendingDeath}
            ("2" : "DATE" : restWords) ->
                updatePendingDate state (T.unwords restWords)
            ["1", "HUSB", husbandId] ->
                updateCurrentFamily state (\family -> family{gfHusband = Just (normalizeRecordId husbandId)})
            ["1", "WIFE", wifeId] ->
                updateCurrentFamily state (\family -> family{gfWife = Just (normalizeRecordId wifeId)})
            ["1", "CHIL", childId] ->
                updateCurrentFamily state (\family -> family{gfChildren = gfChildren family ++ [normalizeRecordId childId]})
            "1" : _ ->
                state{gsPending = PendingNone}
            _ ->
                state

updateCurrentPerson :: GedcomState -> (GedcomPerson -> GedcomPerson) -> GedcomState
updateCurrentPerson state f =
    case gsCurrent state of
        CurrentPerson personId ->
            let updated =
                    maybe
                        (f (GedcomPerson personId Nothing Nothing Nothing Nothing))
                        f
                        (Map.lookup personId (gsPeople state))
             in state
                    { gsPeople = Map.insert personId updated (gsPeople state)
                    , gsPending = PendingNone
                    }
        _ ->
            state

updateCurrentFamily :: GedcomState -> (GedcomFamily -> GedcomFamily) -> GedcomState
updateCurrentFamily state f =
    case gsCurrent state of
        CurrentFamily familyId ->
            let updated =
                    maybe
                        (f (GedcomFamily familyId Nothing Nothing []))
                        f
                        (Map.lookup familyId (gsFamilies state))
             in state
                    { gsFamilies = Map.insert familyId updated (gsFamilies state)
                    , gsPending = PendingNone
                    }
        _ ->
            state

updatePendingDate :: GedcomState -> Text -> GedcomState
updatePendingDate state dateValue =
    case (gsCurrent state, gsPending state) of
        (CurrentPerson _, PendingBirth) ->
            updateCurrentPerson state (\person -> person{gpBirth = Just (T.strip dateValue)})
        (CurrentPerson _, PendingDeath) ->
            updateCurrentPerson state (\person -> person{gpDeath = Just (T.strip dateValue)})
        _ ->
            state

renderPerson :: GedcomPerson -> [Text]
renderPerson person =
    [ "entity " <> personIdentifier person <> " : person {"
    ]
        ++ maybeField "name" (gpName person)
        ++ maybeField "sex" (gpSex person)
        ++ maybeField "birth_date" (gpBirth person)
        ++ maybeField "death_date" (gpDeath person)
        ++ [ "    appears_on: gedcom_import @ 1900-01-01..2100-12-31,"
           , "}"
           , ""
           ]

renderRelationships :: Map Text GedcomPerson -> Map Text GedcomFamily -> [Text]
renderRelationships people families =
    concatMap renderFamily (sortOn gfId (Map.elems families))
  where
    renderFamily family =
        spouseRelationship family ++ parentRelationships family

    spouseRelationship family =
        case (gfHusband family >>= resolvePerson, gfWife family >>= resolvePerson) of
            (Just husbandIdent, Just wifeIdent) ->
                ["rel " <> husbandIdent <> " -[\"spouse\"]-> " <> wifeIdent <> ";", ""]
            _ ->
                []

    parentRelationships family =
        concatMap (renderParentLinks family) (gfChildren family)

    renderParentLinks family childId =
        case resolvePerson childId of
            Nothing -> []
            Just childIdent ->
                mapMaybe (\parentIdent -> fmap (\resolved -> "rel " <> resolved <> " -[\"parent_of\"]-> " <> childIdent <> ";") (resolvePerson parentIdent))
                    (parents family)
                    ++ ["" | not (null (parents family))]

    parents family = maybeToList (gfHusband family) ++ maybeToList (gfWife family)

    resolvePerson personId =
        personIdentifier <$> Map.lookup personId people

maybeField :: Text -> Maybe Text -> [Text]
maybeField fieldName maybeValue =
    case maybeValue of
        Nothing -> []
        Just value ->
            [ "    " <> fieldName <> ": \"" <> escapeString value <> "\","
            ]

personIdentifier :: GedcomPerson -> Text
personIdentifier person =
    sanitizeIdentifier (maybe (gpId person) id (gpName person)) (gpId person)

cleanName :: Text -> Text
cleanName = T.replace "/" "" . T.strip

normalizeRecordId :: Text -> Text
normalizeRecordId = T.dropAround (== '@')

sanitizeIdentifier :: Text -> Text -> Text
sanitizeIdentifier raw fallback
    | T.null normalized = normalizeRecordId fallback
    | otherwise = normalized
  where
    normalized =
        T.dropAround (== '_') $
            T.map
                (\charValue -> if isAllowed charValue then charValue else '_')
                (T.strip raw)

    isAllowed charValue =
        ('0' <= charValue && charValue <= '9')
            || ('A' <= charValue && charValue <= 'Z')
            || ('a' <= charValue && charValue <= 'z')
            || charValue == '_'

escapeString :: Text -> Text
escapeString =
    T.replace "\\" "\\\\"
        . T.replace "\"" "\\\""

maybeToList :: Maybe a -> [a]
maybeToList maybeValue =
    case maybeValue of
        Just value -> [value]
        Nothing -> []
