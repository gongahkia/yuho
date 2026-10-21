-- | Experimental diagram-first SDK. See docs/authoring-sdk.md.
module Yuho.Authoring
  ( module Yuho.Authoring.Temporal
  , module Yuho.Authoring.Types, module Yuho.Authoring.Codec
  , module Yuho.Authoring.Compile, module Yuho.Authoring.Report
  , module Yuho.Authoring.Projection, module Yuho.Authoring.Projection.Encode
  , module Yuho.Authoring.Projection.Inspect, module Yuho.Authoring.Projection.Views
  , module Yuho.Authoring.Projection.ViewEncode
  , module Yuho.Authoring.Edit
  , module Yuho.Authoring.Source
  , module Yuho.Authoring.Presumption
  , module Yuho.Authoring.Typed
  , module Yuho.Authoring.Definitions
  , module Yuho.Authoring.Interaction
  , validateDocument, validateAnalysis
  , SuppliedStatus(..), UnresolvedReason(..)
  ) where

import Yuho.Authoring.Temporal
import Yuho.Authoring.Types
import Yuho.Authoring.Edit
import Yuho.Authoring.Source
import Yuho.Authoring.Presumption
import Yuho.Authoring.Typed
import Yuho.Authoring.Definitions
import Yuho.Authoring.Interaction
import Yuho.Authoring.Codec
import Yuho.Authoring.Compile
import Yuho.Authoring.Report hiding (applicationReportFromResult)
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Encode
import Yuho.Authoring.Projection.Inspect
import Yuho.Authoring.Projection.Views
import Yuho.Authoring.Projection.ViewEncode
import Data.Text (Text)
import Yuho.Authoring.Validate (validateDocument, validateBindings)
import Yuho.SuppliedProofStatus.Types (SuppliedStatus(..), UnresolvedReason(..))

-- | Document and binding diagnostics remain available for drafts. A ready
-- analysis also passes compilation's unchanged kernel decoder/validator.
validateAnalysis :: AuthoringDocument -> Text -> ValidationReport
validateAnalysis doc key =
  let report = validateBindings doc key in
  if not (analysisReady report) then report else case compileAnalysis doc key of
    Left diagnostics -> report { analysisReady = False, validationDiagnostics = diagnostics }
    Right _ -> report

