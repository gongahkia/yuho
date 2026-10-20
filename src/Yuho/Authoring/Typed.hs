-- | Experimental ground typed authoring; separate from proof-profile documents.
module Yuho.Authoring.Typed
  ( module Yuho.Authoring.Typed.Types, module Yuho.Authoring.Typed.Run
  , module Yuho.Authoring.Typed.Projection, validateTypedDocument ) where
import Yuho.Authoring.Typed.Types
import Yuho.Authoring.Typed.Run
import Yuho.Authoring.Typed.Projection
import Yuho.Authoring.Typed.Validate (validateTypedDocument)
