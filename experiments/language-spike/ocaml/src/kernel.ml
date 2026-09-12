open Json

let ( let* ) = Result.bind

type span = {
  start : int;
  end_ : int;
  start_line : int;
  start_col : int;
  end_line : int;
  end_col : int;
}

type kind = Leaf | All | Any | Unsupported of string

type requirement = {
  kind : kind;
  id : string;
  path : string list;
  span : span;
  members : requirement list;
  pointer : string;
}

type provision = {
  id : string;
  path : string list;
  span : span;
  requirements : requirement list;
  children : provision list;
  definitions : bool;
  pointer : string;
}

type diagnostic = {
  code : string;
  stage : string;
  severity : string;
  path : string;
  span : span option;
  parameters : (string * string) list;
}

type input =
  | Evaluate of provision * (string * bool) list * int
  | Validate of bool * diagnostic list

type trace = {
  branch : string;
  id : string;
  kind : string;
  path : string list;
  span : span;
  value : bool;
  children : string list;
}

type branch = {
  id : string;
  path : string list;
  value : bool;
  trace_ids : string list;
}

let protocol = "yuho.kernel-protocol/v1"
let result_schema = "yuho.kernel-result/v1"
let fragment = "ClosedBooleanBranches-v1"

let get_string = function Str value -> Ok value | _ -> Error "expected string"
let get_bool = function Bool value -> Ok value | _ -> Error "expected Boolean"
let get_int = function Num value -> Ok value | _ -> Error "expected integer"
let get_list = function Arr value -> Ok value | _ -> Error "expected array"
let get_object = function Obj value -> Ok value | _ -> Error "expected object"

let named decoder key value =
  let* item = field key value in
  decoder item

let rec collect = function
  | [] -> Ok []
  | result :: rest ->
      let* value = result in
      let* tail = collect rest in
      Ok (value :: tail)

let strings value =
  let* values = get_list value in
  collect (List.map get_string values)

let decode_span value =
  let* start = named get_int "start" value in
  let* end_ = named get_int "end" value in
  let* start_line = named get_int "start_line" value in
  let* start_col = named get_int "start_col" value in
  let* end_line = named get_int "end_line" value in
  let* end_col = named get_int "end_col" value in
  if start < 0 || end_ < start || start_line < 1 || end_line < start_line
     || start_col < 1 || end_col < 1
  then Error "invalid span"
  else Ok { start; end_; start_line; start_col; end_line; end_col }

let rec decode_requirement pointer value =
  let* kind_text = named get_string "kind" value in
  let* id = named get_string "id" value in
  let* path_value = field "path" value in
  let* path = strings path_value in
  let* span_value = field "span" value in
  let* span = decode_span span_value in
  let kind =
    match kind_text with
    | "leaf" -> Leaf
    | "all" -> All
    | "any" -> Any
    | other -> Unsupported other
  in
  let* members =
    match kind with
    | Leaf | Unsupported _ -> Ok []
    | All | Any ->
        let* member_value = field "members" value in
        let* values = get_list member_value in
        values
        |> List.mapi (fun index child ->
             decode_requirement (pointer ^ "/members/" ^ string_of_int index) child)
        |> collect
  in
  Ok { kind; id; path; span; members; pointer }

let rec decode_provision pointer value =
  let* id = named get_string "id" value in
  let* path_value = field "path" value in
  let* path = strings path_value in
  let* span_value = field "span" value in
  let* span = decode_span span_value in
  let* definitions = named get_bool "definitions" value in
  let* req_value = field "requirements" value in
  let* req_values = get_list req_value in
  let* requirements =
    req_values
    |> List.mapi (fun index child ->
         decode_requirement (pointer ^ "/requirements/" ^ string_of_int index) child)
    |> collect
  in
  let* child_value = field "children" value in
  let* child_values = get_list child_value in
  let* children =
    child_values
    |> List.mapi (fun index child ->
         decode_provision (pointer ^ "/children/" ^ string_of_int index) child)
    |> collect
  in
  Ok { id; path; span; requirements; children; definitions; pointer }

let decode_diagnostic value =
  let* code = named get_string "code" value in
  let* stage = named get_string "stage" value in
  let* severity = named get_string "severity" value in
  let* path = named get_string "path" value in
  let* span_value = field "span" value in
  let* span =
    match span_value with Null -> Ok None | other ->
      let* decoded = decode_span other in
      Ok (Some decoded)
  in
  let* parameter_value = field "parameters" value in
  let* parameter_pairs = get_object parameter_value in
  let* parameters =
    parameter_pairs
    |> List.map (fun (key, item) ->
         let* text = get_string item in
         Ok (key, text))
    |> collect
  in
  if not (List.mem severity [ "error"; "warning"; "info" ])
  then Error "invalid diagnostic severity"
  else Ok { code; stage; severity; path; span; parameters }

let decode_input root =
  let* schema = named get_string "input_schema" root in
  let* fragment_name = named get_string "fragment" root in
  if schema <> "yuho.kernel-input/v1" || fragment_name <> fragment
  then Error "unsupported input schema or fragment"
  else
    let* source = field "source" root in
    let* source_text = named get_string "text" source in
    let* source_hash = named get_string "sha256" source in
    let* _source_path = named get_string "path" source in
    if Sha256.sha256 source_text <> source_hash then Error "source SHA-256 mismatch"
    else
      let* policy = field "policy" root in
      let* _date = named get_string "reference_date" policy in
      let* max_nodes = named get_int "max_nodes" policy in
      if max_nodes < 1 || max_nodes > 1024 then Error "invalid max_nodes"
      else
        let* operation = named get_string "operation" root in
        match operation with
        | "evaluate" ->
            let* program_value = field "program" root in
            let* program = decode_provision "/program" program_value in
            let* fact_value = field "facts" root in
            let* fact_pairs = get_object fact_value in
            let* facts =
              fact_pairs
              |> List.map (fun (key, item) ->
                   let* value = get_bool item in
                   Ok (key, value))
              |> collect
            in
            Ok (Evaluate (program, facts, max_nodes))
        | "validate" ->
            let* parser_result = field "parser_result" root in
            let* accepted = named get_bool "accepted" parser_result in
            let* _source_version = named get_string "source_version" parser_result in
            let* diagnostic_value = field "diagnostics" parser_result in
            let* diagnostic_values = get_list diagnostic_value in
            let* diagnostics = collect (List.map decode_diagnostic diagnostic_values) in
            Ok (Validate (accepted, diagnostics))
        | _ -> Error "unsupported operation"

let span_json (value : span) =
  Obj [
    "start", Num value.start; "end", Num value.end_;
    "start_line", Num value.start_line; "start_col", Num value.start_col;
    "end_line", Num value.end_line; "end_col", Num value.end_col;
  ]

let diagnostic_json (value : diagnostic) =
  Obj [
    "code", Str value.code; "stage", Str value.stage;
    "severity", Str value.severity; "path", Str value.path;
    "span", (match value.span with None -> Null | Some location -> span_json location);
    "parameters", Obj (List.map (fun (key, text) -> key, Str text) value.parameters);
  ]

let make_diagnostic code stage path span parameters =
  { code; stage; severity = "error"; path; span; parameters }

type node = Provision_node of provision | Requirement_node of requirement

let rec requirement_nodes (value : requirement) =
  Requirement_node value :: List.concat_map requirement_nodes value.members

let rec all_nodes (value : provision) =
  Provision_node value
  :: (List.concat_map requirement_nodes value.requirements
      @ List.concat_map all_nodes value.children)

module Id_set = Set.Make (String)

let validate_program max_nodes facts root =
  let nodes = all_nodes root in
  if List.length nodes > max_nodes then
    Error (make_diagnostic "KINV004" "validate" "/program" (Some root.span) [])
  else
    let check_node seen = function
      | Provision_node item ->
          if Id_set.mem item.id seen then
            Error (make_diagnostic "KINV002" "validate"
                     (item.pointer ^ "/id") (Some item.span) [ "id", item.id ])
          else Ok (Id_set.add item.id seen)
      | Requirement_node item ->
          (match item.kind with
           | Unsupported name ->
               Error (make_diagnostic "KCAP001" "capability"
                        (item.pointer ^ "/kind") (Some item.span) [ "kind", name ])
           | _ when Id_set.mem item.id seen ->
               Error (make_diagnostic "KINV002" "validate"
                        (item.pointer ^ "/id") (Some item.span) [ "id", item.id ])
           | Leaf -> Ok (Id_set.add item.id seen)
           | All | Any when item.members = [] ->
               Error (make_diagnostic "KINV004" "validate"
                        (item.pointer ^ "/members") (Some item.span) [])
           | All | Any -> Ok (Id_set.add item.id seen))
    in
    let* _seen =
      List.fold_left
        (fun state node ->
          let* seen = state in
          check_node seen node)
        (Ok Id_set.empty) nodes
    in
    let leaves : requirement list =
      List.filter_map
        (function
          | Requirement_node ({ kind = Leaf; _ } as item) -> Some item
          | _ -> None)
        nodes
    in
    List.fold_left
      (fun state (item : requirement) ->
        let* () = state in
        if List.mem_assoc item.id facts then Ok ()
        else Error (make_diagnostic "KINV001" "validate"
                      ("/facts/" ^ item.id) (Some item.span) [ "id", item.id ]))
      (Ok ()) leaves

let rec leaf_branches (provision : provision) inherited =
  let direct = inherited @ provision.requirements in
  let descendants =
    List.concat_map (fun child -> leaf_branches child direct) provision.children
  in
  if descendants <> [] then descendants
  else if direct = [] then []
  else [ provision, direct ]

let kind_name = function
  | Leaf -> "leaf"
  | All -> "all"
  | Any -> "any"
  | Unsupported name -> name

let rec evaluate_requirement facts branch_id (item : requirement) =
  let make_trace value children =
    {
      branch = branch_id; id = item.id; kind = kind_name item.kind;
      path = item.path; span = item.span; value; children;
    }
  in
  match item.kind with
  | Unsupported name ->
      Error (make_diagnostic "KCAP001" "capability"
               (item.pointer ^ "/kind") (Some item.span) [ "kind", name ])
  | Leaf ->
      (match List.assoc_opt item.id facts with
       | None ->
           Error (make_diagnostic "KINV001" "validate"
                    ("/facts/" ^ item.id) (Some item.span) [ "id", item.id ])
       | Some value -> Ok (value, [ make_trace value [] ]))
  | All | Any ->
      let* evaluated =
        collect (List.map (evaluate_requirement facts branch_id) item.members)
      in
      let values = List.map fst evaluated in
      let value = if item.kind = All then List.for_all Fun.id values else List.exists Fun.id values in
      let children = List.concat_map snd evaluated in
      Ok (value, make_trace value (List.map (fun (member : requirement) -> member.id) item.members) :: children)

let evaluate_branch facts ((provision : provision), requirements) =
  let* evaluated =
    collect (List.map (evaluate_requirement facts provision.id) requirements)
  in
  let value = List.for_all (fun (result, _) -> result) evaluated in
  let trace = List.concat_map snd evaluated in
  Ok ({ id = provision.id; path = provision.path; value;
        trace_ids = List.map (fun (item : trace) -> item.id) trace }, trace)

let bool_name value = if value then "true" else "false"

let branch_json (value : branch) =
  Obj [
    "id", Str value.id; "path", Arr (List.map (fun item -> Str item) value.path);
    "status", Str (bool_name value.value);
    "trace_ids", Arr (List.map (fun item -> Str item) value.trace_ids);
  ]

let trace_json (value : trace) =
  Obj [
    "branch", Str value.branch; "id", Str value.id;
    "kind", Str value.kind; "path", Arr (List.map (fun item -> Str item) value.path);
    "span", span_json value.span; "value", Str (bool_name value.value);
    "children", Arr (List.map (fun item -> Str item) value.children);
  ]

let inner_digest root =
  let operation = named get_string "operation" root in
  let keys =
    match operation with
    | Ok "validate" ->
        [ "input_schema"; "fragment"; "source"; "parser_result"; "policy" ]
    | _ ->
        [ "input_schema"; "fragment"; "source"; "program"; "facts"; "policy" ]
  in
  let pairs =
    keys
    |> List.map (fun key ->
         let* value = field key root in
         Ok (key, value))
    |> collect
  in
  match pairs with
  | Error _ -> Sha256.sha256 ""
  | Ok items -> Sha256.sha256 (Json.encode (Obj items))

let base_result request_id digest status kind branches traces diagnostics =
  Obj [
    "protocol", Str protocol;
    "request_id", Str request_id;
    "result_schema", Str result_schema;
    "fragment", Str fragment;
    "input_digest", Str digest;
    "status", Str status;
    "provision_kind", Str kind;
    "branches", Arr (List.map branch_json branches);
    "trace", Arr (List.map trace_json traces);
    "diagnostics", Arr (List.map diagnostic_json diagnostics);
  ]

let run root =
  let request_id =
    match named get_string "request_id" root with Ok value -> value | Error _ -> "?"
  in
  let digest = inner_digest root in
  let reject diagnostic =
    base_result request_id digest "rejected" "none" [] [] [ diagnostic ]
  in
  let received =
    match named get_string "protocol" root with Ok value -> value | Error _ -> ""
  in
  if received <> protocol then
    reject (make_diagnostic "KPROT001" "protocol" "/protocol" None
              [ "received", received ])
  else
    match decode_input root with
    | Error message ->
        reject (make_diagnostic "KDEC001" "decode" "/" None
                  [ "reason", message ])
    | Ok (Validate (accepted, diagnostics)) ->
        base_result request_id digest
          (if accepted then "true" else "rejected") "none" [] [] diagnostics
    | Ok (Evaluate (program, facts, max_nodes)) ->
        (match validate_program max_nodes facts program with
         | Error diagnostic -> reject diagnostic
         | Ok () ->
             (match collect (List.map (evaluate_branch facts) (leaf_branches program [])) with
              | Error diagnostic -> reject diagnostic
              | Ok evaluated ->
                  let branches = List.map fst evaluated in
                  let traces = List.concat_map snd evaluated in
                  let kind = if branches = [] then "definition_only" else "executable" in
                  base_result request_id digest
                    (bool_name (List.exists (fun (item : branch) -> item.value) branches))
                    kind branches traces []))

let decode_failure message =
  base_result "?" (Sha256.sha256 "") "rejected" "none" [] []
    [ make_diagnostic "KDEC001" "decode" "/" None [ "reason", message ] ]
