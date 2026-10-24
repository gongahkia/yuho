{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE CPP #-}
{-# LANGUAGE ForeignFunctionInterface #-}
module Yuho.Surface.Publication (publishExport) where
import Control.Exception (bracketOnError, try)
import Control.Monad (when)
import qualified Data.ByteString as BS
import System.Directory (makeAbsolute, removeDirectoryRecursive)
import System.FilePath ((</>), takeDirectory, takeFileName, splitDirectories)
import System.Posix.Files (getSymbolicLinkStatus, isDirectory)
import System.Posix.Temp (mkdtemp)
import System.IO.Error (isDoesNotExistError)
#if defined(linux_HOST_OS)
import Foreign.C.String (CString, withCString)
import Foreign.C.Types (CInt(..), CUInt(..))
import Foreign.C.Error (throwErrnoIfMinus1_)
#endif

-- Linux renameat2(RENAME_NOREPLACE) publishes the completed directory in one
-- filesystem operation and refuses *any* existing destination, including an empty
-- directory or a dangling link. There is deliberately no check-then-rename fallback.
-- This is atomic visibility/no-clobber, not a power-loss durability guarantee.
publishExport :: FilePath -> [(FilePath,BS.ByteString)] -> IO ()
publishExport out files = do
  when (null out || takeFileName out `elem` ["", ".", ".."]
        || ".." `elem` splitDirectories out)
    (ioError (userError "output must name a new directory without parent traversal"))
  destination <- makeAbsolute out
  let parent = takeDirectory destination
  checkParents parent
  existing <- try (getSymbolicLinkStatus destination)
  case existing of
    Right _ -> ioError (userError "output destination already exists; use a new directory")
    Left issue | isDoesNotExistError issue -> pure ()
               | otherwise -> ioError issue
  bracketOnError (mkdtemp (parent </> ".yuho-compose-")) removeDirectoryRecursive $ \staging -> do
    mapM_ (\(name,bytes) -> BS.writeFile (staging </> name) bytes) files
    publishNoReplace staging destination
  where
    checkParents path = do
      stat <- getSymbolicLinkStatus path
      when (not (isDirectory stat))
        (ioError (userError "output parent and ancestors must be real directories, not links"))
      let parent = takeDirectory path
      when (parent /= path) (checkParents parent)

publishNoReplace :: FilePath -> FilePath -> IO ()
#if defined(linux_HOST_OS)
publishNoReplace source destination = withCString source $ \src ->
  withCString destination $ \dst ->
    throwErrnoIfMinus1_ "renameat2(RENAME_NOREPLACE)" (renameNoReplace (-100) src (-100) dst 1)

foreign import ccall unsafe "renameat2"
  renameNoReplace :: CInt -> CString -> CInt -> CString -> CUInt -> IO CInt
#else
publishNoReplace _ _ = ioError (userError
  "atomic no-replace directory publication is unsupported on this platform; no output published")
#endif
