{-# LANGUAGE OverloadedStrings #-}

module Euclid.TUI.App
    ( runEuclidTui
    ) where

import Brick
import qualified Brick.Main as M
import Brick.Widgets.Border (borderWithLabel)
import Data.Char (digitToInt)
import Data.List (nub, sort)
import qualified Data.Map.Strict as Map
import Data.Maybe (fromMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Graphics.Vty as V
import Euclid.Core.Validation
import Euclid.Model.Types
import Euclid.Render.Layout

data Name = Root
    deriving (Eq, Ord, Show)

data Pane
    = PaneTimelines
    | PaneEntities
    | PaneRelationships
    | PaneDiagnostics
    deriving (Eq, Show, Enum, Bounded)

data Mode
    = ModeNormal
    | ModeSearch
    | ModeCommand
    deriving (Eq, Show)

data AppSnapshot = AppSnapshot
    { snapshotPane :: Pane
    , snapshotTimelineIndex :: Int
    , snapshotEntityIndex :: Int
    , snapshotRelationshipIndex :: Int
    , snapshotDiagnosticIndex :: Int
    , snapshotSearch :: Text
    , snapshotTypeFilter :: Maybe Text
    , snapshotNeighborhoodOnly :: Bool
    , snapshotCompareTimeline :: Maybe Text
    , snapshotScrubPoint :: Maybe Integer
    }

data AppState = AppState
    { appFilePath :: FilePath
    , appWorld :: World
    , appLayout :: Layout
    , appDiagnostics :: [Diagnostic]
    , appPane :: Pane
    , appMode :: Mode
    , appTimelineIndex :: Int
    , appEntityIndex :: Int
    , appRelationshipIndex :: Int
    , appDiagnosticIndex :: Int
    , appSearch :: Text
    , appTypeFilter :: Maybe Text
    , appNeighborhoodOnly :: Bool
    , appCompareTimeline :: Maybe Text
    , appBookmarks :: Map.Map Int Text
    , appUndoStack :: [AppSnapshot]
    , appRedoStack :: [AppSnapshot]
    , appShowHelp :: Bool
    , appCommandInput :: Text
    , appScrubPoint :: Maybe Integer
    , appSelectionTrail :: [Text]
    , appStatus :: Text
    }

runEuclidTui :: FilePath -> World -> IO ()
runEuclidTui filePath world = do
    let initialState =
            AppState
                { appFilePath = filePath
                , appWorld = world
                , appLayout = computeLayout world
                , appDiagnostics = validateWorld world
                , appPane = PaneEntities
                , appMode = ModeNormal
                , appTimelineIndex = 0
                , appEntityIndex = 0
                , appRelationshipIndex = 0
                , appDiagnosticIndex = 0
                , appSearch = ""
                , appTypeFilter = Nothing
                , appNeighborhoodOnly = False
                , appCompareTimeline = Nothing
                , appBookmarks = Map.empty
                , appUndoStack = []
                , appRedoStack = []
                , appShowHelp = False
                , appCommandInput = ""
                , appScrubPoint = Nothing
                , appSelectionTrail = []
                , appStatus = "Tab switches panes, / searches, : opens commands, [ and ] scrub time, q quits"
                }
    _ <- M.defaultMain appDefinition initialState
    pure ()

appDefinition :: App AppState e Name
appDefinition =
    App
        { appDraw = drawUi
        , appChooseCursor = neverShowCursor
        , appHandleEvent = handleEvent
        , appStartEvent = pure ()
        , appAttrMap = const attrMapDefinition
        }

drawUi :: AppState -> [Widget Name]
drawUi state =
    [ if appShowHelp state
        then baseWidget <=> drawHelp
        else baseWidget
    ]
  where
    baseWidget =
        vBox
            [ borderWithLabel (withAttr headingAttr (txt "Euclid TUI")) $
                hBox
                    [ hLimit 32 (drawPane "Timelines" (appPane state == PaneTimelines) timelineRows)
                    , hLimit 48 (drawPane "Entities" (appPane state == PaneEntities) entityRows)
                    , hLimit 36 (drawPane "Relationships" (appPane state == PaneRelationships) relationshipRows)
                    , drawPane "Inspector" (appPane state == PaneDiagnostics) inspectorRows
                    ]
            , drawStatus state
            ]
    timelineRows =
        selectableRows
            (appPane state == PaneTimelines)
            (appTimelineIndex state)
            [ layoutTimelineName timeline <> " [" <> T.pack (show (layoutTimelineKind timeline)) <> "]"
            | timeline <- layoutTimelines (appLayout state)
            ]
    entityRows =
        selectableRows
            (appPane state == PaneEntities)
            (appEntityIndex state)
            [ layoutEntityName entity <> " : " <> layoutEntityType entity
            | entity <- visibleEntities state
            ]
    relationshipRows =
        selectableRows
            (appPane state == PaneRelationships)
            (appRelationshipIndex state)
            [ renderRelationship relationship
            | relationship <- visibleRelationships state
            ]
    inspectorRows = map txtWrap (inspectorText state)

drawPane :: Text -> Bool -> [Widget Name] -> Widget Name
drawPane labelValue active rows =
    borderWithLabel (withAttr headingAttr (txt labelValue)) $
        padAll 1 $
            vBox bodyRows
  where
    bodyRows =
        ( if null rows
            then [withAttr mutedAttr (txt "(empty)")]
            else rows
        )
            ++ [ padTop (Pad 1) $
                    if active
                        then withAttr statusAttr (txt "active")
                        else emptyWidget
               ]

drawStatus :: AppState -> Widget Name
drawStatus state =
    withAttr statusAttr $
        padAll 1 $
            txt $
                "file: "
                    <> T.pack (appFilePath state)
                    <> " | mode: "
                    <> T.pack (show (appMode state))
                    <> " | search: "
                    <> appSearch state
                    <> " | type: "
                    <> fromMaybe "all" (appTypeFilter state)
                    <> " | scrub: "
                    <> maybe "off" (T.pack . show) (appScrubPoint state)
                    <> " | "
                    <> appStatus state

selectableRows :: Bool -> Int -> [Text] -> [Widget Name]
selectableRows active selectedIndex values =
    zipWith renderRow [0 ..] values
  where
    renderRow rowIndex value
        | active && rowIndex == selectedIndex = withAttr selectedAttr (padRight Max (txt value))
        | otherwise = padRight Max (txt value)

inspectorText :: AppState -> [Text]
inspectorText state =
    timelineDetails
        ++ [""]
        ++ entityDetails
        ++ [""]
        ++ relationshipDetails
        ++ [""]
        ++ compareDetails
        ++ [""]
        ++ diagnosticDetails
        ++ [""]
        ++ trailDetails
  where
    timelineDetails =
        case safeIndex (appTimelineIndex state) (layoutTimelines (appLayout state)) of
            Nothing -> ["Timeline: none"]
            Just timeline ->
                [ "Timeline"
                , "  name: " <> layoutTimelineName timeline
                , "  kind: " <> T.pack (show (layoutTimelineKind timeline))
                , "  start: " <> T.pack (show (layoutTimelineStart timeline))
                , "  end: " <> T.pack (show (layoutTimelineEnd timeline))
                , "  scrub visible: " <> if timelineVisibleAtScrub state timeline then "yes" else "no"
                ]
    entityDetails =
        case safeIndex (appEntityIndex state) (visibleEntities state) of
            Nothing -> ["Entity: none"]
            Just entity ->
                let fieldLines =
                        case Map.lookup (layoutEntityName entity) (worldEntities (appWorld state)) of
                            Nothing -> []
                            Just sourceEntity ->
                                [ "  " <> keyValue <> ": " <> T.pack (show value)
                                | (keyValue, value) <- Map.toList (entityFields sourceEntity)
                                ]
                 in [ "Entity"
                    , "  name: " <> layoutEntityName entity
                    , "  type: " <> layoutEntityType entity
                    , "  timeline: " <> layoutEntityTimeline entity
                    ]
                        ++ fieldLines
    relationshipDetails =
        case safeIndex (appRelationshipIndex state) (visibleRelationships state) of
            Nothing -> ["Relationship: none"]
            Just relationship ->
                [ "Relationship"
                , "  " <> renderRelationship relationship
                ]
    compareDetails =
        case compareSummary state of
            [] -> ["Compare: disabled"]
            linesValue -> "Compare" : map ("  " <>) linesValue
    diagnosticDetails =
        case safeIndex (appDiagnosticIndex state) (appDiagnostics state) of
            Nothing -> ["Diagnostics", "  none"]
            Just diagnostic ->
                [ "Diagnostic"
                , "  " <> renderDiagnostic diagnostic
                ]
    trailDetails =
        case appSelectionTrail state of
            [] -> ["Trail", "  (empty)"]
            entries -> "Trail" : map ("  " <>) entries

handleEvent :: BrickEvent Name e -> EventM Name AppState ()
handleEvent (VtyEvent eventValue) = do
    state <- get
    case appMode state of
        ModeSearch ->
            case eventValue of
                V.EvKey V.KEsc [] -> put (exitSearch state)
                V.EvKey V.KBS [] -> put (searchBackspace state)
                V.EvKey V.KEnter [] -> put (exitSearch state)
                V.EvKey (V.KChar charValue) [] -> put (searchAppend charValue state)
                _ -> pure ()
        ModeCommand ->
            case eventValue of
                V.EvKey V.KEsc [] -> put (exitCommandPalette state)
                V.EvKey V.KBS [] -> put (commandBackspace state)
                V.EvKey V.KEnter [] -> put (runCommandPalette state)
                V.EvKey (V.KChar charValue) [] -> put (commandAppend charValue state)
                _ -> pure ()
        ModeNormal ->
            case eventValue of
                V.EvKey (V.KChar 'q') [] -> M.halt
                V.EvKey (V.KChar '\t') [] -> put (advancePane state)
                V.EvKey V.KUp [] -> put (moveSelection (-1) state)
                V.EvKey (V.KChar 'k') [] -> put (moveSelection (-1) state)
                V.EvKey V.KDown [] -> put (moveSelection 1 state)
                V.EvKey (V.KChar 'j') [] -> put (moveSelection 1 state)
                V.EvKey V.KEnter [] -> put (followSelection state)
                V.EvKey (V.KChar '/') [] ->
                    put (recordHistory state){appMode = ModeSearch, appStatus = "Search mode"}
                V.EvKey (V.KChar ':') [] ->
                    put (recordHistory state){appMode = ModeCommand, appCommandInput = "", appStatus = "Command palette"}
                V.EvKey (V.KChar 't') [] -> put (cycleTypeFilter state)
                V.EvKey (V.KChar 'n') [] -> put (toggleNeighborhood state)
                V.EvKey (V.KChar 's') [] -> put (jumpRelationshipEndpoint True state)
                V.EvKey (V.KChar 'g') [] -> put (jumpRelationshipEndpoint False state)
                V.EvKey (V.KChar '?') [] -> put state{appShowHelp = not (appShowHelp state)}
                V.EvKey (V.KChar 'c') [] -> put (cycleCompareTimeline state)
                V.EvKey (V.KChar 'b') [] -> put (saveBookmark state)
                V.EvKey (V.KChar '[') [] -> put (stepScrubber (-1) state)
                V.EvKey (V.KChar ']') [] -> put (stepScrubber 1 state)
                V.EvKey (V.KChar '{') [] -> put (scrubToTimelineBoundary False state)
                V.EvKey (V.KChar '}') [] -> put (scrubToTimelineBoundary True state)
                V.EvKey (V.KChar 'u') [] -> put (undoState state)
                V.EvKey (V.KChar 'y') [] -> put (redoState state)
                V.EvKey (V.KChar keyValue) []
                    | keyValue >= '1' && keyValue <= '9' ->
                        put (loadBookmark (digitToInt keyValue) state)
                _ -> pure ()
handleEvent _ = pure ()

advancePane :: AppState -> AppState
advancePane state =
    noteCurrentSelection $
        (recordHistory state)
        { appPane =
            case appPane state of
                PaneTimelines -> PaneEntities
                PaneEntities -> PaneRelationships
                PaneRelationships -> PaneDiagnostics
                PaneDiagnostics -> PaneTimelines
        , appStatus = "Switched pane"
        }

moveSelection :: Int -> AppState -> AppState
moveSelection delta state =
    let state' = recordHistory state
     in noteCurrentSelection $
            case appPane state of
                PaneTimelines ->
                    state'
                        { appTimelineIndex =
                            boundedMove delta (appTimelineIndex state) (layoutTimelines (appLayout state))
                        }
                PaneEntities ->
                    state'
                        { appEntityIndex =
                            boundedMove delta (appEntityIndex state) (visibleEntities state)
                        }
                PaneRelationships ->
                    state'
                        { appRelationshipIndex =
                            boundedMove delta (appRelationshipIndex state) (visibleRelationships state)
                        }
                PaneDiagnostics ->
                    state'
                        { appDiagnosticIndex =
                            boundedMove delta (appDiagnosticIndex state) (appDiagnostics state)
                        }

boundedMove :: Int -> Int -> [a] -> Int
boundedMove delta currentIndex values
    | null values = 0
    | otherwise = max 0 (min (length values - 1) (currentIndex + delta))

visibleEntities :: AppState -> [LayoutEntity]
visibleEntities state =
    filter entityVisible (layoutEntities (appLayout state))
  where
    searchValue = T.toLower (appSearch state)
    entityVisible entity =
        searchMatches entity && typeMatches entity && scrubMatches entity
    searchMatches entity =
        T.null searchValue
            || searchValue `T.isInfixOf` T.toLower (layoutEntityName entity)
            || searchValue `T.isInfixOf` T.toLower (layoutEntityType entity)
    typeMatches entity =
        maybe True (== layoutEntityType entity) (appTypeFilter state)
    scrubMatches entity =
        maybe True
            (\scrubPoint -> layoutEntityStart entity <= scrubPoint && scrubPoint <= layoutEntityEnd entity)
            (appScrubPoint state)

visibleRelationships :: AppState -> [LayoutRelationship]
visibleRelationships state
    | appNeighborhoodOnly state =
        case safeIndex (appEntityIndex state) (visibleEntities state) of
            Nothing -> []
            Just entity ->
                filter
                    (\relationship -> layoutRelSource relationship == layoutEntityName entity || layoutRelTarget relationship == layoutEntityName entity)
                    allRelationships
    | otherwise = allRelationships
  where
    allRelationships = filter relationshipVisibleAtScrub (layoutRelationships (appLayout state))
    relationshipVisibleAtScrub relationship =
        maybe True
            (\scrubPoint -> any (entityVisibleAt scrubPoint) relatedEntities)
            (appScrubPoint state)
      where
        relatedEntities =
            filter
                (\entity -> layoutEntityName entity == layoutRelSource relationship || layoutEntityName entity == layoutRelTarget relationship)
                (layoutEntities (appLayout state))
        entityVisibleAt scrubPoint entity = layoutEntityStart entity <= scrubPoint && scrubPoint <= layoutEntityEnd entity

renderRelationship :: LayoutRelationship -> Text
renderRelationship relationship =
    layoutRelSource relationship
        <> " "
        <> maybe "-->" (\labelValue -> "-[" <> labelValue <> "]->") (layoutRelLabel relationship)
        <> " "
        <> layoutRelTarget relationship

cycleTypeFilter :: AppState -> AppState
cycleTypeFilter state =
    let options = Nothing : map Just (sort (nub [layoutEntityType entity | entity <- layoutEntities (appLayout state)]))
        currentIndex = fromMaybe 0 (lookupIndex (appTypeFilter state) options)
        nextIndex = (currentIndex + 1) `mod` length options
        nextFilter = fromMaybe Nothing (safeIndex nextIndex options)
     in (recordHistory state)
            { appTypeFilter = nextFilter
            , appEntityIndex = 0
            , appStatus = "Cycled type filter"
            }

toggleNeighborhood :: AppState -> AppState
toggleNeighborhood state =
    (recordHistory state)
        { appNeighborhoodOnly = not (appNeighborhoodOnly state)
        , appRelationshipIndex = 0
        , appStatus = "Toggled relationship neighborhood mode"
        }

exitSearch :: AppState -> AppState
exitSearch state =
    state
        { appMode = ModeNormal
        , appStatus = "Exited search mode"
        }

exitCommandPalette :: AppState -> AppState
exitCommandPalette state =
    state
        { appMode = ModeNormal
        , appCommandInput = ""
        , appStatus = "Exited command palette"
        }

searchBackspace :: AppState -> AppState
searchBackspace state =
    case appMode state of
        ModeNormal -> state
        ModeSearch ->
            (recordHistory state)
                { appSearch =
                    if T.null (appSearch state)
                        then ""
                        else T.init (appSearch state)
                , appEntityIndex = 0
                }
        ModeCommand -> state

searchAppend :: Char -> AppState -> AppState
searchAppend charValue state =
    case appMode state of
        ModeNormal -> state
        ModeSearch ->
            (recordHistory state)
                { appSearch = appSearch state <> T.singleton charValue
                , appEntityIndex = 0
                , appStatus = "Filtering entities"
                }
        ModeCommand -> state

commandBackspace :: AppState -> AppState
commandBackspace state =
    case appMode state of
        ModeCommand ->
            state
                { appCommandInput =
                    if T.null (appCommandInput state)
                        then ""
                        else T.init (appCommandInput state)
                }
        _ -> state

commandAppend :: Char -> AppState -> AppState
commandAppend charValue state =
    case appMode state of
        ModeCommand ->
            state
                { appCommandInput = appCommandInput state <> T.singleton charValue
                , appStatus = "Command palette"
                }
        _ -> state

runCommandPalette :: AppState -> AppState
runCommandPalette state =
    let commandName = T.toLower (T.strip (appCommandInput state))
        baseState = (recordHistory state){appMode = ModeNormal, appCommandInput = ""}
     in case commandName of
            "help" -> baseState{appShowHelp = not (appShowHelp state), appStatus = "Toggled help panel"}
            "compare" -> cycleCompareTimeline baseState
            "bookmark" -> saveBookmark baseState
            "clear-search" -> baseState{appSearch = "", appStatus = "Cleared search"}
            "clear-filters" ->
                baseState
                    { appSearch = ""
                    , appTypeFilter = Nothing
                    , appNeighborhoodOnly = False
                    , appScrubPoint = Nothing
                    , appStatus = "Cleared active filters"
                    }
            "clear-scrub" -> baseState{appScrubPoint = Nothing, appStatus = "Cleared scrubber"}
            "follow" -> followSelection baseState
            "rel-source" -> jumpRelationshipEndpoint True baseState
            "rel-target" -> jumpRelationshipEndpoint False baseState
            "scrub-center" ->
                baseState
                    { appScrubPoint = Just ((layoutMinTime (appLayout state) + layoutMaxTime (appLayout state)) `div` 2)
                    , appStatus = "Moved scrubber to timeline center"
                    }
            "timeline-next" -> moveTimelineSelection 1 baseState
            "timeline-prev" -> moveTimelineSelection (-1) baseState
            _ -> baseState{appStatus = "Unknown command: " <> commandName}

recordHistory :: AppState -> AppState
recordHistory state =
    state
        { appUndoStack = snapshotState state : appUndoStack state
        , appRedoStack = []
        }

snapshotState :: AppState -> AppSnapshot
snapshotState state =
    AppSnapshot
        { snapshotPane = appPane state
        , snapshotTimelineIndex = appTimelineIndex state
        , snapshotEntityIndex = appEntityIndex state
        , snapshotRelationshipIndex = appRelationshipIndex state
        , snapshotDiagnosticIndex = appDiagnosticIndex state
        , snapshotSearch = appSearch state
        , snapshotTypeFilter = appTypeFilter state
        , snapshotNeighborhoodOnly = appNeighborhoodOnly state
        , snapshotCompareTimeline = appCompareTimeline state
        , snapshotScrubPoint = appScrubPoint state
        }

restoreSnapshot :: AppSnapshot -> AppState -> AppState
restoreSnapshot snapshot state =
    state
        { appPane = snapshotPane snapshot
        , appTimelineIndex = snapshotTimelineIndex snapshot
        , appEntityIndex = snapshotEntityIndex snapshot
        , appRelationshipIndex = snapshotRelationshipIndex snapshot
        , appDiagnosticIndex = snapshotDiagnosticIndex snapshot
        , appSearch = snapshotSearch snapshot
        , appTypeFilter = snapshotTypeFilter snapshot
        , appNeighborhoodOnly = snapshotNeighborhoodOnly snapshot
        , appCompareTimeline = snapshotCompareTimeline snapshot
        , appScrubPoint = snapshotScrubPoint snapshot
        }

undoState :: AppState -> AppState
undoState state =
    case appUndoStack state of
        [] -> state{appStatus = "Nothing to undo"}
        snapshot : rest ->
            (restoreSnapshot snapshot state)
                { appUndoStack = rest
                , appRedoStack = snapshotState state : appRedoStack state
                , appStatus = "Undid the last view change"
                }

redoState :: AppState -> AppState
redoState state =
    case appRedoStack state of
        [] -> state{appStatus = "Nothing to redo"}
        snapshot : rest ->
            (restoreSnapshot snapshot state)
                { appRedoStack = rest
                , appUndoStack = snapshotState state : appUndoStack state
                , appStatus = "Redid the last view change"
                }

saveBookmark :: AppState -> AppState
saveBookmark state =
    case safeIndex (appEntityIndex state) (visibleEntities state) of
        Nothing -> state{appStatus = "No visible entity to bookmark"}
        Just entity ->
            let nextSlot =
                    case [slot | slot <- [1 .. 9], Map.notMember slot (appBookmarks state)] of
                        slot : _ -> slot
                        [] -> 1
             in state
                    { appBookmarks = Map.insert nextSlot (layoutEntityName entity) (appBookmarks state)
                    , appStatus = "Saved bookmark " <> T.pack (show nextSlot) <> " for " <> layoutEntityName entity
                    }

loadBookmark :: Int -> AppState -> AppState
loadBookmark slot state =
    case Map.lookup slot (appBookmarks state) of
        Nothing -> state{appStatus = "No bookmark in slot " <> T.pack (show slot)}
        Just entityNameValue ->
            case lookupIndexBy (\entity -> layoutEntityName entity == entityNameValue) (visibleEntities state) of
                Nothing -> state{appStatus = "Bookmarked entity is not visible under current filters"}
                Just indexValue ->
                    noteCurrentSelection $
                        (recordHistory state)
                            { appPane = PaneEntities
                            , appEntityIndex = indexValue
                            , appStatus = "Loaded bookmark " <> T.pack (show slot)
                            }

cycleCompareTimeline :: AppState -> AppState
cycleCompareTimeline state =
    case layoutTimelines (appLayout state) of
        [] -> state{appStatus = "No timelines available for comparison"}
        timelinesValue ->
            let names = map layoutTimelineName timelinesValue
                nextName =
                    case appCompareTimeline state of
                        Nothing ->
                            case names of
                                firstName : _ -> Just firstName
                                [] -> Nothing
                        Just current ->
                            safeIndex 0 (drop 1 (dropWhile (/= current) names) ++ names)
             in (recordHistory state)
                    { appCompareTimeline = nextName
                    , appStatus = "Updated timeline comparison target"
                    }

moveTimelineSelection :: Int -> AppState -> AppState
moveTimelineSelection delta state =
    noteCurrentSelection $
        (recordHistory state)
            { appPane = PaneTimelines
            , appTimelineIndex = boundedMove delta (appTimelineIndex state) (layoutTimelines (appLayout state))
            , appStatus = "Moved timeline selection"
            }

stepScrubber :: Integer -> AppState -> AppState
stepScrubber delta state =
    let nextPoint =
            case appScrubPoint state of
                Nothing -> Just (layoutMinTime (appLayout state))
                Just current ->
                    Just (max (layoutMinTime (appLayout state)) (min (layoutMaxTime (appLayout state)) (current + delta)))
     in (recordHistory state)
            { appScrubPoint = nextPoint
            , appRelationshipIndex = 0
            , appEntityIndex = 0
            , appStatus = "Moved scrubber"
            }

scrubToTimelineBoundary :: Bool -> AppState -> AppState
scrubToTimelineBoundary useEnd state =
    case safeIndex (appTimelineIndex state) (layoutTimelines (appLayout state)) of
        Nothing -> state{appStatus = "No timeline selected for scrubber jump"}
        Just timeline ->
            (recordHistory state)
                { appScrubPoint =
                    Just $
                        if useEnd
                            then layoutTimelineEnd timeline
                            else layoutTimelineStart timeline
                , appStatus =
                    if useEnd
                        then "Scrubber moved to selected timeline end"
                        else "Scrubber moved to selected timeline start"
                }

timelineVisibleAtScrub :: AppState -> LayoutTimeline -> Bool
timelineVisibleAtScrub state timeline =
    maybe True
        (\scrubPoint -> layoutTimelineStart timeline <= scrubPoint && scrubPoint <= layoutTimelineEnd timeline)
        (appScrubPoint state)

compareSummary :: AppState -> [Text]
compareSummary state =
    case (safeIndex (appTimelineIndex state) (layoutTimelines (appLayout state)), appCompareTimeline state) of
        (Just currentTimeline, Just compareName) ->
            let currentEntities =
                    sort
                        [ layoutEntityName entity
                        | entity <- layoutEntities (appLayout state)
                        , layoutEntityTimeline entity == layoutTimelineName currentTimeline
                        ]
                compareEntities =
                    sort
                        [ layoutEntityName entity
                        | entity <- layoutEntities (appLayout state)
                        , layoutEntityTimeline entity == compareName
                        ]
                onlyCurrent = filter (`notElem` compareEntities) currentEntities
                onlyCompare = filter (`notElem` currentEntities) compareEntities
             in [ "current: " <> layoutTimelineName currentTimeline
                , "against: " <> compareName
                , "only current: " <> renderList onlyCurrent
                , "only compare: " <> renderList onlyCompare
                ]
        _ -> []

followSelection :: AppState -> AppState
followSelection state =
    case appPane state of
        PaneTimelines ->
            case safeIndex (appTimelineIndex state) (layoutTimelines (appLayout state)) of
                Nothing -> state{appStatus = "No timeline selected to follow"}
                Just timeline ->
                    case [layoutEntityName entity | entity <- layoutEntities (appLayout state), layoutEntityTimeline entity == layoutTimelineName timeline] of
                        entityNameValue : _ ->
                            focusEntityByName entityNameValue state
                        [] ->
                            state{appStatus = "Selected timeline has no entities to follow"}
        PaneEntities ->
            case safeIndex (appEntityIndex state) (visibleEntities state) of
                Nothing -> state{appStatus = "No entity selected to explore"}
                Just entity ->
                    noteCurrentSelection $
                        (recordHistory state)
                            { appPane = PaneRelationships
                            , appNeighborhoodOnly = True
                            , appRelationshipIndex = 0
                            , appStatus = "Showing neighborhood relationships for " <> layoutEntityName entity
                            }
        PaneRelationships ->
            jumpRelationshipEndpoint True state
        PaneDiagnostics ->
            followDiagnostic state

jumpRelationshipEndpoint :: Bool -> AppState -> AppState
jumpRelationshipEndpoint useSource state =
    case safeIndex (appRelationshipIndex state) (visibleRelationships state) of
        Nothing -> state{appStatus = "No relationship selected"}
        Just relationship ->
            focusEntityByName
                (if useSource then layoutRelSource relationship else layoutRelTarget relationship)
                state

followDiagnostic :: AppState -> AppState
followDiagnostic state =
    case safeIndex (appDiagnosticIndex state) (appDiagnostics state) of
        Nothing -> state{appStatus = "No diagnostic selected"}
        Just diagnostic ->
            case diagnosticRelationshipPair diagnostic of
                Just (sourceName, targetName) ->
                    focusRelationshipBy
                        (\relationship -> layoutRelSource relationship == sourceName && layoutRelTarget relationship == targetName)
                        ("Focused relationship " <> sourceName <> " -> " <> targetName)
                        state
                Nothing ->
                    case diagnosticEntityTarget diagnostic of
                        Just entityNameValue ->
                            focusEntityByName entityNameValue state
                        Nothing ->
                            case diagnosticTimelineTarget diagnostic of
                                Just timelineNameValue ->
                                    focusTimelineByName timelineNameValue state
                                Nothing ->
                                    case diagnosticRelationshipSourceTarget diagnostic of
                                        Just sourceName ->
                                            focusRelationshipBy
                                                (\relationship -> layoutRelSource relationship == sourceName)
                                                ("Focused relationship source " <> sourceName)
                                                state
                                        Nothing ->
                                            case diagnosticRelationshipDestinationTarget diagnostic of
                                                Just targetName ->
                                                    focusRelationshipBy
                                                        (\relationship -> layoutRelTarget relationship == targetName)
                                                        ("Focused relationship target " <> targetName)
                                                        state
                                                Nothing ->
                                                    state
                                                        { appStatus =
                                                            maybe
                                                                "No navigation target for selected diagnostic"
                                                                renderDiagnosticLocation
                                                                (diagnosticSpan diagnostic)
                                                        }

diagnosticEntityTarget :: Diagnostic -> Maybe Text
diagnosticEntityTarget diagnostic =
    takeTargetName =<< T.stripPrefix "entity " (diagnosticMessage diagnostic)

diagnosticTimelineTarget :: Diagnostic -> Maybe Text
diagnosticTimelineTarget diagnostic =
    takeTargetName =<< T.stripPrefix "timeline " (diagnosticMessage diagnostic)

diagnosticRelationshipPair :: Diagnostic -> Maybe (Text, Text)
diagnosticRelationshipPair diagnostic = do
    targetText <- T.stripPrefix "relationship temporal scope has start after end: " (diagnosticMessage diagnostic)
    case T.splitOn " -> " targetText of
        [sourceName, targetName] -> Just (sourceName, targetName)
        _ -> Nothing

diagnosticRelationshipSourceTarget :: Diagnostic -> Maybe Text
diagnosticRelationshipSourceTarget diagnostic =
    T.stripPrefix "relationship source not found: " (diagnosticMessage diagnostic)

diagnosticRelationshipDestinationTarget :: Diagnostic -> Maybe Text
diagnosticRelationshipDestinationTarget diagnostic =
    T.stripPrefix "relationship target not found: " (diagnosticMessage diagnostic)

takeTargetName :: Text -> Maybe Text
takeTargetName targetText =
    case T.words targetText of
        targetName : _ -> Just targetName
        [] -> Nothing

renderDiagnosticLocation :: SourceSpan -> Text
renderDiagnosticLocation sourceSpan =
    "Diagnostic at "
        <> T.pack (spanFile sourceSpan)
        <> ":"
        <> T.pack (show (spanStartLine sourceSpan))
        <> ":"
        <> T.pack (show (spanStartColumn sourceSpan))

focusEntityByName :: Text -> AppState -> AppState
focusEntityByName entityNameValue state =
    case lookupIndexBy (\entity -> layoutEntityName entity == entityNameValue) (visibleEntities baseState) of
        Nothing ->
            baseState{appStatus = "Unable to focus entity " <> entityNameValue}
        Just indexValue ->
            noteCurrentSelection $
                baseState
                    { appPane = PaneEntities
                    , appEntityIndex = indexValue
                    , appStatus = "Focused entity " <> entityNameValue
                    }
  where
    baseState =
        (recordHistory state)
            { appSearch = ""
            , appTypeFilter = Nothing
            , appNeighborhoodOnly = False
            , appScrubPoint = Nothing
            }

focusTimelineByName :: Text -> AppState -> AppState
focusTimelineByName timelineNameValue state =
    case lookupIndexBy (\timeline -> layoutTimelineName timeline == timelineNameValue) (layoutTimelines (appLayout baseState)) of
        Nothing ->
            baseState{appStatus = "Unable to focus timeline " <> timelineNameValue}
        Just indexValue ->
            noteCurrentSelection $
                baseState
                    { appPane = PaneTimelines
                    , appTimelineIndex = indexValue
                    , appStatus = "Focused timeline " <> timelineNameValue
                    }
  where
    baseState =
        (recordHistory state)
            { appNeighborhoodOnly = False
            , appScrubPoint = Nothing
            }

focusRelationshipBy :: (LayoutRelationship -> Bool) -> Text -> AppState -> AppState
focusRelationshipBy predicate successMessage state =
    case lookupIndexBy predicate (visibleRelationships baseState) of
        Nothing ->
            baseState{appStatus = "Unable to focus relationship for selected diagnostic"}
        Just indexValue ->
            noteCurrentSelection $
                baseState
                    { appPane = PaneRelationships
                    , appRelationshipIndex = indexValue
                    , appStatus = successMessage
                    }
  where
    baseState =
        (recordHistory state)
            { appSearch = ""
            , appTypeFilter = Nothing
            , appNeighborhoodOnly = False
            , appScrubPoint = Nothing
            }

noteCurrentSelection :: AppState -> AppState
noteCurrentSelection state =
    case selectionLabel state of
        Nothing -> state
        Just labelValue ->
            state
                { appSelectionTrail =
                    take 8 (labelValue : filter (/= labelValue) (appSelectionTrail state))
                }

selectionLabel :: AppState -> Maybe Text
selectionLabel state =
    case appPane state of
        PaneTimelines ->
            ("timeline " <>) . layoutTimelineName <$> safeIndex (appTimelineIndex state) (layoutTimelines (appLayout state))
        PaneEntities ->
            ("entity " <>) . layoutEntityName <$> safeIndex (appEntityIndex state) (visibleEntities state)
        PaneRelationships ->
            ("relationship " <>) . renderRelationship <$> safeIndex (appRelationshipIndex state) (visibleRelationships state)
        PaneDiagnostics ->
            ("diagnostic " <>) . renderDiagnostic <$> safeIndex (appDiagnosticIndex state) (appDiagnostics state)

renderList :: [Text] -> Text
renderList [] = "(none)"
renderList values = T.intercalate ", " values

lookupIndexBy :: (a -> Bool) -> [a] -> Maybe Int
lookupIndexBy predicate = go 0
  where
    go _ [] = Nothing
    go indexValue (entry : rest)
        | predicate entry = Just indexValue
        | otherwise = go (indexValue + 1) rest

drawHelp :: Widget Name
drawHelp =
    borderWithLabel (withAttr headingAttr (txt "Help")) $
        padAll 1 $
            vBox
                [ txt "Tab: cycle panes"
                , txt "j/k or arrows: move selection"
                , txt "Enter: follow the current selection"
                , txt "/: search entities"
                , txt ":: command palette"
                , txt "t: cycle type filter"
                , txt "n: toggle neighborhood relationships"
                , txt "s/g: jump from a selected relationship to its source or target entity"
                , txt "c: cycle comparison timeline"
                , txt "[ ]: step scrubber"
                , txt "{ }: jump scrubber to selected timeline bounds"
                , txt "b: save current entity bookmark"
                , txt "1-9: jump to bookmark"
                , txt "u/y: undo or redo"
                , txt "?: toggle this help"
                , txt "q: quit"
                ]

safeIndex :: Int -> [a] -> Maybe a
safeIndex indexValue values
    | indexValue < 0 = Nothing
    | otherwise =
        case drop indexValue values of
            [] -> Nothing
            value : _ -> Just value

lookupIndex :: Eq a => a -> [a] -> Maybe Int
lookupIndex value = go 0
  where
    go _ [] = Nothing
    go currentIndex (entry : rest)
        | entry == value = Just currentIndex
        | otherwise = go (currentIndex + 1) rest

selectedAttr :: AttrName
selectedAttr = attrName "selected"

headingAttr :: AttrName
headingAttr = attrName "heading"

statusAttr :: AttrName
statusAttr = attrName "status"

mutedAttr :: AttrName
mutedAttr = attrName "muted"

attrMapDefinition :: AttrMap
attrMapDefinition =
    attrMap
        V.defAttr
        [ (selectedAttr, V.black `on` V.yellow)
        , (headingAttr, fg V.cyan)
        , (statusAttr, fg V.green)
        , (mutedAttr, fg V.brightBlack)
        ]
