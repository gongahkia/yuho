{-# LANGUAGE OverloadedStrings #-}
-- Public-only SDK construction; Python supplies independent expected tuples.
module Main (main) where
import qualified Yuho.Authoring as S
import qualified Yuho.Authoring.Dependency as D
import qualified Data.Aeson as A
import qualified Data.ByteString as B
import qualified Data.Map.Strict as M
import Data.Text (Text)
import qualified Data.Text.Encoding as U
import System.Environment (getArgs)
import System.FilePath ((</>))
import Control.Monad (forM_)
import System.Exit (exitFailure)

meta :: Text -> S.TypedMeta
meta i=S.TypedMeta i i Nothing []
term :: D.DataTerm
term=D.DataTerm (A.object ["kind" A..= ("life_imprisonment"::Text),"term_id" A..= ("term:fictional"::Text),"span" A..= A.object
  ["start" A..= (0::Int),"end" A..= (0::Int),"start_line" A..= (1::Int),"start_col" A..= (1::Int),"end_line" A..= (1::Int),"end_col" A..= (1::Int)]])
document :: Text -> Text -> Bool -> D.DependencyDocument
document ty actor sdk=D.DependencyDocument D.planFormat
  (D.DependencyPlan "generated-ownership-control" [D.SourceOrigin "origin" "urn:fictional:f04"] [scope] [component] [] [candidate]) sources Nothing
 where
  scope=D.PlanScope "occurrence" "project:actor" "project:event" Nothing Nothing [("project:actor","role:person"),("project:event","role:event")]
  local=S.Scope actor "local:context"
  tuple=S.GroundTuple "own" [actor,"event:one"]
  typed=S.TypedDocument S.typedAuthoringFormat "document" "law:fictional" "1"
    [S.TypedEntityType (meta ty),S.TypedEntityType (meta "event")]
    [S.TypedEntity (meta actor) ty,S.TypedEntity (meta "event:one") "event"]
    [S.TypedPredicate (meta "own") [S.TypedArgument "actor" ty,S.TypedArgument "event" "event"]]
    [S.TypedApplication (meta "application") tuple] []
    [S.TypedExpression (meta "q") (S.GroundApplication "application")]
    [S.TypedLink "body" "r" "q" "typed_body"] [S.TypedRule (meta "r") "p"] [S.TypedProposition (meta "p")]
    [S.TypedAssessment (meta "assessment") "application" tuple local S.TechnicalTrue "supplied" "fictional author" "synthetic_fixture" "assumption" []]
    [] [S.TypedAnalysis "analysis" "r" "p" local ["assessment"] []] [] [] [] [] ["Fictional ownership control only"]
  template=D.TechnicalTemplate "template" [ty,"event"] [(actor,ty),("event:one","event")]
    [("own",[ty,"event"])] [] [("q",D.TemplateAtom "own" [actor,"event:one"])] ["p"] [("r","p","q")]
    [("own",[actor,"event:one"],D.Satisfied,"supplied")] ["Fictional ownership control only"]
  component=D.PlanComponent "producer" (if sdk then "sdk-typed-v0.3" else "native-typed")
    (if sdk then "typed.json" else "") Nothing (if sdk then Just ("analysis","analysis") else Nothing)
    "occurrence" [(ty,"role:person"),("event","role:event")] [(actor,"project:actor"),("event:one","project:event")]
    "Exact local actor/context correspondence" (if sdk then Nothing else Just template) Nothing
  candidate=D.PlanCandidate "candidate" "occurrence" (D.ObservationPort "producer" "typed.expression.truth" "q")
    "yuho.condition-identity/v1" "unspecified" "Technical candidate only, no sentence" ["origin"] term Nothing
  sources=if sdk then M.singleton "typed.json" (U.decodeUtf8 (S.encodeTypedDocument typed)) else M.empty

main :: IO ()
main=do
 args<-getArgs
 case args of
  ["typed",input,output]->do
   bytes<-B.readFile input
   typed<-either (fail . show) pure (S.decodeTypedDocument bytes)
   compiled<-either (fail . show) pure (S.compileTypedAnalysis typed "analysis")
   result<-either (fail . show) pure (S.evaluateTypedAnalysis compiled)
   B.writeFile output (S.typedEvaluationResponse result)
   B.writeFile (output<>".request.json") (S.typedCompiledRequest compiled)
  [folder]->writeDocuments folder
  _->exitFailure

writeDocuments :: FilePath -> IO ()
writeDocuments folder=
 forM_ [("ordinary","person","actor"),("entity","person","dep_template_entity"),("type","dep_template_type","actor"),("both","dep_template_type","dep_template_entity")] $ \(label,ty,actor)->
  forM_ [("template",False),("typed",True)] $ \(profile,sdk)->
   B.writeFile (folder </> label<>"-"<>profile<>".json") (D.encodeDependencyDocument (document ty actor sdk))
