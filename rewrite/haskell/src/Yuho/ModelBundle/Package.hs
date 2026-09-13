{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Package (validatePackage) where

import Control.Exception (Exception, catch, throwIO)
import Crypto.Hash (Context, Digest, SHA256, hashFinalize, hashInit, hashUpdate)
import qualified Data.ByteString as BS
import Data.Foldable (traverse_)
import Data.List (sort)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Directory (listDirectory)
import System.FilePath ((</>))
import System.IO (Handle, IOMode(ReadMode), withBinaryFile)
import System.Posix.Files (FileStatus, fileSize, getSymbolicLinkStatus, isDirectory, isRegularFile)
import Yuho.Core.Source (validateSpan)
import Yuho.Core.Types (Source(..))
import Yuho.ModelBundle.Json
import Yuho.ModelBundle.Review (classifyReviews, decodeReview)
import Yuho.ModelBundle.Types
import Yuho.ModelBundle.Validate (decodeCore, scopeDigest, validateCore)
import Yuho.Protocol.Json (encodeJson)

newtype BundleException = BundleException Failure deriving (Show)
instance Exception BundleException

validatePackage :: FilePath -> Maybe Text -> IO (Either Failure Validation)
validatePackage root policy = (Right <$> validate root policy) `catch` handle
  where handle (BundleException failure) = pure (Left failure)

validate :: FilePath -> Maybe Text -> IO Validation
validate root policy = do
  requireDirectory "/" root
  requireEntries "/" root ["model-bundle.json", "artifacts"] ["reviews"]
  requireDirectory "/artifacts" (root </> "artifacts")
  requireEntries "/artifacts" (root </> "artifacts") ["sha256"] []
  requireDirectory "/artifacts/sha256" (root </> "artifacts" </> "sha256")
  manifestBytes <- readBounded "/model-bundle.json" 1048576 (root </> "model-bundle.json")
  manifest <- expect (parseCanonical "/model-bundle.json" manifestBytes)
  core <- expect (decodeCore manifest)
  let artifactDir = root </> "artifacts" </> "sha256"
      expected = sort (map (Text.unpack . artifactDigest) (coreArtifacts core))
  names <- sort <$> listDirectory artifactDir
  traverse_ (\name -> if isDigestName name then pure ()
    else reject "MBPKG001" ("/artifacts/sha256/" <> Text.pack name) "invalid artifact filename") names
  if names /= expected then reject "MBPKG001" "/artifacts/sha256" "artifact inventory mismatch" else pure ()
  traverse_ (validateArtifact artifactDir) (coreArtifacts core)
  modelBytes <- readBounded "/executable_model" 1048576
    (artifactDir </> Text.unpack (coreModelDigest core))
  model <- expect (parseCanonical "/executable_model" modelBytes)
  expect (validateCore core model)
  traverse_ (validateMappings artifactDir core) (map artifactDigest
    (filter ((== "source_text") . artifactRole) (coreArtifacts core)))
  let bundle = digestDomain "yuho.model-bundle/v1" (encodeJson (coreRaw core))
      scope = scopeDigest core
  reviewFiles <- listDirectoryIfPresent root
  if length reviewFiles > 64 then reject "MBRES001" "/reviews" "review count exceeds 64" else pure ()
  reviews <- traverse (\name -> do
    if safeReviewName name then pure ()
      else reject "MBPKG001" ("/reviews/" <> Text.pack name) "invalid review filename"
    bytes <- readBounded ("/reviews/" <> Text.pack name) 1048576 (root </> "reviews" </> name)
    value <- expect (parseCanonical ("/reviews/" <> Text.pack name) bytes)
    expect (decodeReview (Text.pack name) value)) (sort reviewFiles)
  if Set.size (Set.fromList (map reviewId reviews)) == length reviews then pure ()
    else reject "MBINV001" "/reviews" "duplicate review ID"
  expect (classifyReviews core bundle scope policy reviews)

validateArtifact :: FilePath -> Artifact -> IO ()
validateArtifact directory artifact = do
  let path = "/artifacts/sha256/" <> artifactDigest artifact
      file = directory </> Text.unpack (artifactDigest artifact)
  status <- requireRegular path file
  if toInteger (fileSize status) /= artifactLength artifact
    then reject "MBINV001" path "artifact byte length differs from declaration" else pure ()
  if toInteger (fileSize status) > 33554432
    then reject "MBRES001" path "artifact exceeds 32 MiB" else pure ()
  actual <- hashFile file
  if actual == artifactDigest artifact then pure ()
    else reject "MBINV001" path "artifact SHA-256 mismatch"

hashFile :: FilePath -> IO Text
hashFile path = withBinaryFile path ReadMode (go hashInit)
  where
    go :: Context SHA256 -> Handle -> IO Text
    go context handle = do
      chunk <- BS.hGetSome handle 65536
      if BS.null chunk then pure (Text.pack (show (hashFinalize context :: Digest SHA256)))
        else go (hashUpdate context chunk) handle

validateMappings :: FilePath -> Core -> Text -> IO ()
validateMappings directory core digest = do
  let path = "/artifacts/sha256/" <> digest
      file = directory </> Text.unpack digest
  bytes <- BS.readFile file
  case Encoding.decodeUtf8' bytes of
    Left _ -> reject "MBINV001" path "span-bearing artifact is not UTF-8"
    Right decoded -> do
      let source = Source (Text.pack file) decoded bytes digest
      traverse_ (\mapping -> if validateSpan source (mappingSpan mapping) then pure ()
        else reject "MBINV001" "/semantic_mappings" "invalid UTF-8 byte/display span")
        [m | m <- coreMappings core, mappingArtifact m == digest]

readBounded :: Text -> Integer -> FilePath -> IO BS.ByteString
readBounded path limit file = do
  status <- requireRegular path file
  if toInteger (fileSize status) > limit then reject "MBRES001" path "file size limit" else pure ()
  bytes <- BS.readFile file
  if toInteger (BS.length bytes) > limit then reject "MBRES001" path "file grew beyond limit" else pure bytes

requireRegular :: Text -> FilePath -> IO FileStatus
requireRegular path file = do
  status <- getSymbolicLinkStatus file
  if isRegularFile status then pure status
    else reject "MBPKG001" path "expected regular file, no symlinks or special objects"

requireDirectory :: Text -> FilePath -> IO ()
requireDirectory path file = do
  status <- getSymbolicLinkStatus file
  if isDirectory status then pure ()
    else reject "MBPKG001" path "expected directory, no symlinks"

requireEntries :: Text -> FilePath -> [FilePath] -> [FilePath] -> IO ()
requireEntries path file required allowed = do
  entries <- listDirectory file
  if all (`elem` entries) required && all (`elem` (required ++ allowed)) entries
    then pure () else reject "MBPKG001" path "unexpected or missing package entry"

listDirectoryIfPresent :: FilePath -> IO [FilePath]
listDirectoryIfPresent root = do
  entries <- listDirectory root
  if "reviews" `elem` entries then do
    requireDirectory "/reviews" (root </> "reviews")
    listDirectory (root </> "reviews")
  else pure []

safeReviewName :: FilePath -> Bool
safeReviewName name = case Text.stripSuffix ".json" (Text.pack name) of
  Just identifier -> safeId identifier
  Nothing -> False

isDigestName :: FilePath -> Bool
isDigestName name = length name == 64 && all (\c -> c >= '0' && c <= '9' || c >= 'a' && c <= 'f') name

expect :: Either Failure a -> IO a
expect = either (throwIO . BundleException) pure

reject :: Text -> Text -> Text -> IO a
reject code path message = throwIO (BundleException (Failure code path message))
