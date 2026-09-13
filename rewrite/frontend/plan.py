"""Bounded synthetic YuhoSurface-v0.4 fragment plans and typed kernel bridges."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
import resource
import subprocess
import tempfile

from . import bundle, core, modules


LANGUAGE = "YuhoSurface-v0.4"
PLAN_SCHEMA = "yuho.execution-plan/v0.1"
TRACE_SCHEMA = "yuho.execution-trace/v0.1"
MAX_STEPS = 4
MAX_EDGES = 3
MAX_OUTPUTS = 4
MAX_REQUEST_BYTES = 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_REQUEST_BYTES = 4 * 1024 * 1024
MAX_TOTAL_RESPONSE_BYTES = 8 * 1024 * 1024
VARIANTS = {
    "SuppliedProofStatus-v1",
    "GuardedPenaltySelection-v1",
    "PenaltyTerms-v1",
}
OUTPUT_TYPES = {
    "SuppliedProofStatus-v1": {"root-status": "status"},
    "GuardedPenaltySelection-v1": {"selected-penalties": "penalty-set"},
    "PenaltyTerms-v1": {"selected-terms": "term-set"},
}
GATES = {
    ("status", "is"): {"satisfied"},
    ("penalty-set", "contains"): {"pen:basic", "pen:enhanced"},
}
MODEL_ID = re.compile(r"[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+")
STEP_ID = re.compile(r"[a-z][a-z0-9_]*")


@dataclass(frozen=True)
class Gate:
    target: core.Token
    operation: core.Token
    value: core.Token


@dataclass(frozen=True)
class Step:
    identifier: core.Token
    variant: core.Token
    module: core.Token
    version: core.Token
    gate: Gate | None


@dataclass(frozen=True)
class PlanSource:
    path: str
    source: bytes
    identifier: core.Token
    version: core.Token
    steps: tuple[Step, ...]
    outputs: tuple[core.Token, ...]
    limitations: tuple[core.Token, ...]


@dataclass(frozen=True)
class FragmentModel:
    path: str
    source: bytes
    identifier: core.Token
    version: core.Token
    variant: core.Token
    request_id: core.Token
    policy_date: core.Token
    inputs: tuple[tuple[core.Token, core.Token], ...]
    requirements: tuple[tuple[str, tuple[core.Token, ...]], ...]
    penalties: tuple[tuple[core.Token, core.Token | None], ...]
    term: tuple[core.Token, core.Token, core.Token] | None
    limitations: tuple[core.Token, ...]


@dataclass(frozen=True)
class Scenario:
    path: str
    source: bytes
    identifier: core.Token
    plan: core.Token
    proof: tuple[core.Assignment, ...]
    booleans: tuple[tuple[core.Token, tuple[core.Assignment, ...]], ...]


def fail(code: str, path: str, token: core.Token, message: str) -> None:
    raise core.FrontendError(code, path, token, message)


def _parser(source: bytes, path: str) -> core.Parser:
    if len(source) > core.MAX_SOURCE_BYTES:
        fail("SFE067", path, core.Token("error", "", 1, 1), "source limit exceeded")
    try:
        text = source.decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail("SFE001", path, core.Token("error", "", 1, 1), "strict UTF-8 required")
    return core.Parser(core.lex(text, path), path)


def _header(p: core.Parser, kind: str) -> tuple[core.Token, core.Token]:
    p.take("language", "SFE052")
    p.take(LANGUAGE, "SFE052")
    p.take(";")
    p.take(kind, "SFE052")
    identifier = p.word()
    p.take("version")
    version = p.word()
    p.take(";")
    p.take("{")
    p.take("jurisdiction")
    p.take("Fictional", "SFE056")
    p.take(";")
    p.take("purpose")
    p.take("compiler_fixture", "SFE056")
    p.take(";")
    if not MODEL_ID.fullmatch(identifier.text) or not modules.SEMVER.fullmatch(
        version.text
    ):
        fail("SFE052", p.path, identifier, "canonical ID and exact version required")
    return identifier, version


def _end(p: core.Parser) -> tuple[core.Token, ...]:
    p.take("limitations")
    p.take("{")
    limitations = []
    while p.tokens[p.index].text != "}":
        limitations.append(p.take("string"))
        p.take(";")
    p.take("}")
    p.take("}")
    p.take("eof")
    if not limitations or not any("fictional" in x.text.lower() for x in limitations):
        fail("SFE056", p.path, p.tokens[0], "fictional limitation required")
    return tuple(limitations)


def parse_plan(source: bytes, path: str) -> PlanSource:
    p = _parser(source, path)
    duplicate = [
        token
        for token in p.tokens
        if token.kind == "word" and token.text == "execution-plan"
    ]
    if len(duplicate) > 1:
        fail("SFE053", path, duplicate[1], "duplicate plan declaration")
    identifier, version = _header(p, "execution-plan")
    steps = []
    while p.tokens[p.index].text == "step":
        p.take("step")
        sid = p.word()
        p.take("uses")
        variant = p.word()
        p.take("module")
        module = p.word()
        p.take("version")
        module_version = p.word()
        gate = None
        if p.tokens[p.index].text == "when":
            p.take("when")
            gate = Gate(p.word(), p.word(), p.word())
        p.take(";")
        steps.append(Step(sid, variant, module, module_version, gate))
        if len(steps) > MAX_STEPS:
            fail("SFE067", path, sid, "step limit exceeded")
    p.take("outputs")
    p.take("{")
    outputs = []
    while p.tokens[p.index].text != "}":
        p.take("output")
        outputs.append(p.word())
        p.take(";")
        if len(outputs) > MAX_OUTPUTS:
            fail("SFE067", path, outputs[-1], "output limit exceeded")
    p.take("}")
    limitations = _end(p)
    result = PlanSource(
        path, source, identifier, version, tuple(steps), tuple(outputs), limitations
    )
    return replace(result, steps=check_plan(result))


def check_plan(plan: PlanSource) -> tuple[Step, ...]:
    if not plan.steps:
        fail("SFE052", plan.path, plan.identifier, "plan needs steps")
    index: dict[str, Step] = {}
    edges = 0
    for step in plan.steps:
        sid = step.identifier.text
        if not STEP_ID.fullmatch(sid) or sid in index:
            fail("SFE053", plan.path, step.identifier, "duplicate or invalid step ID")
        if step.variant.text not in VARIANTS:
            fail("SFE056", plan.path, step.variant, "unsupported fragment")
        if not MODEL_ID.fullmatch(step.module.text) or not modules.SEMVER.fullmatch(
            step.version.text
        ):
            fail("SFE052", plan.path, step.module, "invalid exact module reference")
        index[sid] = step
    dependencies = {}
    for step in plan.steps:
        if step.gate:
            edges += 1
            name = step.gate.target.text.split("::")
            if len(name) != 2 or name[0] not in index:
                fail("SFE054", plan.path, step.gate.target, "unknown dependency")
            typ = OUTPUT_TYPES[index[name[0]].variant.text].get(name[1])
            if typ is None:
                fail(
                    "SFE058",
                    plan.path,
                    step.gate.target,
                    "unregistered technical output",
                )
            if step.gate.value.text not in GATES.get(
                (typ, step.gate.operation.text), set()
            ):
                fail(
                    "SFE059", plan.path, step.gate.operation, "incompatible typed gate"
                )
            dependencies[step.identifier.text] = name[0]
        elif step.identifier.text != "assessment":
            fail(
                "SFE062", plan.path, step.identifier, "downstream step requires a gate"
            )
    ready = sorted(set(index) - set(dependencies))
    ordered = []
    remaining = dict(dependencies)
    while ready:
        name = ready.pop(0)
        ordered.append(index[name])
        ready.extend(sorted(key for key, parent in remaining.items() if parent == name))
        ready.sort()
        remaining = {key: parent for key, parent in remaining.items() if parent != name}
    if remaining:
        fail(
            "SFE055",
            plan.path,
            index[sorted(remaining)[0]].identifier,
            "dependency cycle",
        )
    if edges > MAX_EDGES:
        fail("SFE067", plan.path, plan.identifier, "dependency edge limit exceeded")
    expected = {
        "assessment::root-status",
        "choice::selected-penalties",
        "basic_terms::selected-terms",
        "enhanced_terms::selected-terms",
    }
    if set(x.text for x in plan.outputs) != expected or len(plan.outputs) != 4:
        fail("SFE063", plan.path, plan.identifier, "four registered outputs required")
    if set(index) != {"assessment", "choice", "basic_terms", "enhanced_terms"}:
        fail("SFE056", plan.path, plan.identifier, "bounded step roles required")
    expected_variants = {
        "assessment": "SuppliedProofStatus-v1",
        "choice": "GuardedPenaltySelection-v1",
        "basic_terms": "PenaltyTerms-v1",
        "enhanced_terms": "PenaltyTerms-v1",
    }
    if any(step.variant.text != expected_variants[sid] for sid, step in index.items()):
        fail("SFE056", plan.path, plan.identifier, "step role and variant mismatch")
    expected_gates = {
        "choice": ("assessment::root-status", "is", "satisfied"),
        "basic_terms": ("choice::selected-penalties", "contains", "pen:basic"),
        "enhanced_terms": ("choice::selected-penalties", "contains", "pen:enhanced"),
    }
    if any(
        step.gate is None
        or (step.gate.target.text, step.gate.operation.text, step.gate.value.text)
        != expected_gates[sid]
        for sid, step in index.items()
        if sid != "assessment"
    ):
        fail("SFE059", plan.path, plan.identifier, "unsafe gate topology")
    return tuple(ordered)


def parse_fragment(source: bytes, path: str) -> FragmentModel:
    p = _parser(source, path)
    identifier, version = _header(p, "fragment-model")
    p.take("variant")
    variant = p.word()
    p.take(";")
    if variant.text not in {"GuardedPenaltySelection-v1", "PenaltyTerms-v1"}:
        fail("SFE056", path, variant, "unsupported authored fragment")
    p.take("request")
    request_id = p.word()
    p.take(";")
    p.take("policy")
    policy_date = p.word()
    p.take(";")
    inputs = []
    while p.tokens[p.index].text == "input":
        p.take("input")
        inputs.append((p.word(), p.take("string")))
        p.take(";")
    requirements = []
    while p.tokens[p.index].text in {"require", "require_any"}:
        kind = p.word()
        if kind.text == "require":
            refs = (p.word(),)
        else:
            refs = (p.word(), p.word())
        p.take(";")
        requirements.append((kind.text, refs))
    penalties = []
    while p.tokens[p.index].text == "candidate":
        p.take("candidate")
        item = p.word()
        p.take("when")
        guard = p.word()
        p.take(";")
        penalties.append((item, guard))
    term = None
    if p.tokens[p.index].text == "term":
        p.take("term")
        term = (p.word(), p.word(), p.word())
        p.take(";")
    limitations = _end(p)
    result = FragmentModel(
        path,
        source,
        identifier,
        version,
        variant,
        request_id,
        policy_date,
        tuple(inputs),
        tuple(requirements),
        tuple(penalties),
        term,
        limitations,
    )
    check_fragment(result)
    return result


def check_fragment(model: FragmentModel) -> None:
    ids = [x.text for x, _ in model.inputs]
    if len(ids) != len(set(ids)) or not ids or any(not x.startswith("f:") for x in ids):
        fail("SFE053", model.path, model.identifier, "duplicate or invalid input ID")
    if len(model.penalties) not in {1, 2} or len(
        set(x.text for x, _ in model.penalties)
    ) != len(model.penalties):
        fail(
            "SFE053",
            model.path,
            model.identifier,
            "candidate declaration IDs must be unique",
        )
    if model.variant.text == "PenaltyTerms-v1" and (
        len(model.penalties) != 1 or model.term is None
    ):
        fail("SFE056", model.path, model.identifier, "one candidate and term required")
    if model.variant.text == "GuardedPenaltySelection-v1" and model.term is not None:
        fail("SFE056", model.path, model.term[0], "terms require PenaltyTerms-v1")
    if not model.requirements:
        fail("SFE063", model.path, model.identifier, "root requirements required")
    mentioned = [x.text for _, refs in model.requirements for x in refs]
    if set(mentioned) != set(ids):
        fail(
            "SFE059", model.path, model.identifier, "every input must be a requirement"
        )
    for _, refs in model.requirements:
        for ref in refs:
            if ref.text not in ids:
                fail("SFE058", model.path, ref, "unknown Boolean input")
    for item, guard in model.penalties:
        if item.text not in {"pen:basic", "pen:enhanced"} or guard.text not in ids:
            fail("SFE059", model.path, item, "candidate or guard is not registered")
    if model.term and (
        model.term[0].text not in {"term:basic", "term:enhanced"}
        or model.term[1].text != "days"
        or not model.term[2].text.isascii()
        or not model.term[2].text.isdecimal()
        or not 1 <= int(model.term[2].text) <= 100
    ):
        fail("SFE056", model.path, model.identifier, "unsupported fictional term")
    if model.policy_date.text != "2026-09-13":
        fail(
            "SFE056",
            model.path,
            model.policy_date,
            "fixed synthetic policy date required",
        )


def parse_scenario(source: bytes, path: str) -> Scenario:
    p = _parser(source, path)
    p.take("scenario")
    identifier = p.word()
    p.take("for")
    plan = p.word()
    p.take("{")
    p.take("proof_assignments")
    p.take("{")
    proof = p.assignments()
    p.take("}")
    booleans = []
    while p.tokens[p.index].text == "bool_assignments":
        p.take("bool_assignments")
        step = p.word()
        p.take("{")
        assignments = p.assignments()
        p.take("}")
        booleans.append((step, assignments))
    p.take("}")
    p.take("eof")
    if len(set(x.text for x, _ in booleans)) != len(booleans):
        fail("SFE053", path, identifier, "duplicate step assignments")
    return Scenario(path, source, identifier, plan, proof, tuple(booleans))


def _model_path(root: Path, identifier: str, *, proof: bool = False) -> Path:
    if not MODEL_ID.fullmatch(identifier):
        raise ValueError("invalid module ID")
    if proof:
        return root / "proof" / "composition.yh"
    return root / "fragments" / (identifier + ".yh")


def _load_fragment(root: Path, step: Step) -> FragmentModel:
    path = _model_path(root, step.module.text)
    try:
        data = core._regular_source(path).encode("utf-8")
    except OSError:
        fail("SFE057", str(path), step.module, "required fragment module missing")
    model = parse_fragment(data, str(path))
    if (
        model.identifier.text != step.module.text
        or model.version.text != step.version.text
    ):
        fail("SFE057", str(path), model.identifier, "exact model ID/version mismatch")
    if model.variant.text != step.variant.text:
        fail("SFE056", str(path), model.variant, "step variant differs from model")
    return model


def check_modules(plan: PlanSource, root: Path) -> None:
    if any(path.is_symlink() for path in (root, *root.parents)) or any(
        path.is_symlink() or not path.is_dir()
        for path in (root, root / "proof", root / "fragments")
    ):
        fail("SFE066", plan.path, plan.identifier, "unsafe or missing module root")
    source_step = plan.steps[0]
    source_path = _model_path(root, source_step.module.text, proof=True)
    resolved = modules.resolve(source_path, root / "proof")
    if (
        resolved.root.identifier.text != source_step.module.text
        or resolved.root.version.text != source_step.version.text
        or resolved.model.variant.text != source_step.variant.text
    ):
        fail(
            "SFE057",
            str(source_path),
            source_step.module,
            "exact proof model ID, version or variant mismatch",
        )
    for step in plan.steps[1:]:
        _load_fragment(root, step)


def lower_fragment(
    model: FragmentModel, assignments: tuple[core.Assignment, ...]
) -> bytes:
    values: dict[str, bool] = {}
    for item in assignments:
        if (
            item.identifier.text in values
            or item.status.text not in {"true", "false"}
            or item.reason
        ):
            fail(
                "SFE059",
                model.path,
                item.identifier,
                "invalid or duplicate Boolean assignment",
            )
        values[item.identifier.text] = item.status.text == "true"
    if set(values) != {x.text for x, _ in model.inputs}:
        fail(
            "SFE059",
            model.path,
            model.identifier,
            "missing or unexpected Boolean assignment",
        )
    source = ("\n".join(q.text for _, q in model.inputs) + "\n").encode("utf-8")
    positions = {}
    offset = 0
    for token, quote in model.inputs:
        encoded = quote.text.encode("utf-8")
        positions[token.text] = core.span(source, offset, offset + len(encoded))
        offset += len(encoded) + 1
    whole = core.span(source, 0, len(source))
    leaves = {
        name: {
            "id": name,
            "kind": "leaf",
            "path": ["candidate"],
            "span": positions[name],
        }
        for name in values
    }
    requirements = []
    for index, (kind, refs) in enumerate(model.requirements):
        if kind == "require":
            requirements.append(leaves[refs[0].text])
        else:
            requirements.append(
                {
                    "id": f"g:candidate-{index}",
                    "kind": "any",
                    "path": ["candidate"],
                    "span": whole,
                    "members": [leaves[x.text] for x in refs],
                }
            )
    declarations = []
    for item, guard in model.penalties:
        row = {
            "penalty_id": item.text,
            "source_id": "src:fictional-plan",
            "span": whole,
            "guard": {"kind": "leaf_true", "leaf_id": guard.text},
        }
        if model.term:
            row["term"] = {
                "term_id": model.term[0].text,
                "kind": "term_imprisonment",
                "span": whole,
                "unit": model.term[1].text,
                "minimum": {"kind": "not_stated"},
                "maximum": {"kind": "specified", "value": int(model.term[2].text)},
            }
        declarations.append(row)
    request = {
        "protocol": "yuho.kernel-protocol/v1",
        "input_schema": "yuho.kernel-input/v1",
        "operation": "evaluate",
        "fragment": model.variant.text,
        "request_id": model.request_id.text,
        "root_rule": "r:fictional-candidate",
        "policy": {"reference_date": model.policy_date.text, "max_nodes": 1024},
        "sources": [
            {
                "id": "src:fictional-plan",
                "path": "fictional/plan-source.txt",
                "text": source.decode("utf-8"),
                "sha256": core.sha(source),
            }
        ],
        "registry": [
            {
                "id": "r:fictional-candidate",
                "source_id": "src:fictional-plan",
                "exceptions": [],
                "program": {
                    "id": "p:fictional-candidate",
                    "path": ["candidate"],
                    "span": whole,
                    "definitions": False,
                    "children": [],
                    "requirements": requirements,
                    "penalties": declarations,
                },
            }
        ],
        "facts": {
            key: {"type": "bool", "value": value} for key, value in values.items()
        },
    }
    data = core.canonical(request)
    if len(data) > MAX_REQUEST_BYTES:
        fail("SFE067", model.path, model.identifier, "request byte limit exceeded")
    return data


def _lock(plan: PlanSource, files: list[tuple[str, str, bytes]]) -> bytes:
    files = files + [(plan.identifier.text, plan.version.text, plan.source)]
    return core.canonical(
        {
            "schema": "yuho.execution-module-lock/v0.1",
            "plan_id": plan.identifier.text,
            "plan_version": plan.version.text,
            "language": LANGUAGE,
            "modules": [
                {
                    "id": identifier,
                    "version": version,
                    "byte_length": len(data),
                    "sha256": core.sha(data),
                }
                for identifier, version, data in sorted(files)
            ],
        }
    )


def verify_compiled(
    plan_bytes: bytes, requests: dict[str, bytes], digests: dict[str, str], path: str
) -> None:
    try:
        value = json.loads(plan_bytes)
        if plan_bytes != core.canonical(value) or value["schema"] != PLAN_SCHEMA:
            raise ValueError("noncanonical plan")
        if set(value) != {
            "schema",
            "plan_id",
            "version",
            "language",
            "scope",
            "steps",
            "outputs",
            "limits",
        }:
            raise ValueError("unknown or missing plan field")
        steps = value["steps"]
        if len(steps) != len(requests) or {x["id"] for x in steps} != set(requests):
            raise ValueError("step inventory mismatch")
        for step in steps:
            if set(step) != {
                "id",
                "variant",
                "module_id",
                "module_version",
                "request_sha256",
                "bundle_digest",
                "depends_on",
                "gate",
            }:
                raise ValueError("unknown or missing step field")
            sid = step["id"]
            if step["request_sha256"] != core.sha(requests[sid]):
                fail(
                    "SFE064",
                    path,
                    core.Token("error", sid, 1, 1),
                    "request hash differs from compiled plan",
                )
            if step["bundle_digest"] != digests[sid]:
                fail(
                    "SFE064",
                    path,
                    core.Token("error", sid, 1, 1),
                    "step bundle digest differs from compiled plan",
                )
    except (KeyError, TypeError, ValueError) as error:
        fail(
            "SFE064",
            path,
            core.Token("error", "", 1, 1),
            f"invalid compiled plan binding: {error}",
        )


def _prepare(plan: PlanSource, scenario: Scenario, root: Path):
    if scenario.plan.text != plan.identifier.text:
        fail("SFE059", scenario.path, scenario.plan, "scenario targets another plan")
    check_modules(plan, root)
    source_step = plan.steps[0]
    source_path = _model_path(root, source_step.module.text, proof=True)
    resolved = modules.resolve(source_path, root / "proof")
    if (
        resolved.root.identifier.text != source_step.module.text
        or resolved.root.version.text != source_step.version.text
    ):
        fail(
            "SFE057",
            str(source_path),
            resolved.root.identifier,
            "exact proof module version mismatch",
        )
    if resolved.model.variant.text != source_step.variant.text:
        fail(
            "SFE056", str(source_path), resolved.model.variant, "proof variant mismatch"
        )
    proof_scenario = core.Scenario(
        scenario.identifier, resolved.model.identifier, scenario.proof
    )
    proof = core.lower_synthetic(
        resolved.model, proof_scenario, resolved.root.path, scenario.path
    )
    entries = [
        (x.identifier.text, x.version.text, x.source_bytes) for x in resolved.ordered
    ]
    booleans = {x.text: value for x, value in scenario.booleans}
    if set(booleans) != {x.identifier.text for x in plan.steps[1:]}:
        fail(
            "SFE059",
            scenario.path,
            scenario.identifier,
            "Boolean assignment steps differ",
        )
    requests = {"assessment": proof}
    models = {"assessment": resolved.model}
    for step in plan.steps[1:]:
        model = _load_fragment(root, step)
        requests[step.identifier.text] = lower_fragment(
            model, booleans[step.identifier.text]
        )
        models[step.identifier.text] = model
        entries.append((model.identifier.text, model.version.text, model.source))
    if len({(a, b) for a, b, _ in entries}) != len(entries):
        fail("SFE053", plan.path, plan.identifier, "duplicate module identity")
    if sum(len(data) for data in requests.values()) > MAX_TOTAL_REQUEST_BYTES:
        fail("SFE067", plan.path, plan.identifier, "aggregate request limit exceeded")
    return requests, models, _lock(plan, entries)


def _run_kernel(
    executable: Path, request: bytes, plan: PlanSource
) -> tuple[bytes, dict]:
    if not executable.is_file() or executable.is_symlink():
        fail("SFE065", plan.path, plan.identifier, "kernel executable unavailable")
    with tempfile.TemporaryFile() as output:

        def cap() -> None:
            resource.setrlimit(
                resource.RLIMIT_FSIZE, (MAX_RESPONSE_BYTES + 1, MAX_RESPONSE_BYTES + 1)
            )

        try:
            completed = subprocess.run(
                [str(executable)],
                input=request + b"\n",
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
                preexec_fn=cap,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            fail(
                "SFE065",
                plan.path,
                plan.identifier,
                f"kernel execution failed: {type(error).__name__}",
            )
        if completed.returncode or output.tell() > MAX_RESPONSE_BYTES:
            fail(
                "SFE065",
                plan.path,
                plan.identifier,
                "kernel protocol or response limit failure",
            )
        output.seek(0)
        data = output.read()
    if data.count(b"\n") != 1 or not data.endswith(b"\n"):
        fail("SFE065", plan.path, plan.identifier, "expected one kernel JSON line")

    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant {value}")

    try:
        parsed = json.loads(
            data, object_pairs_hook=unique, parse_constant=invalid_constant
        )
    except (UnicodeDecodeError, ValueError):
        fail("SFE065", plan.path, plan.identifier, "invalid kernel JSON")
    input_value = json.loads(request)
    input_keys = (
        "input_schema",
        "fragment",
        "sources",
        "registry",
        "root_rule",
        "facts",
        "policy",
    )
    input_digest = core.sha(
        core.canonical({key: input_value[key] for key in input_keys})
    )
    if (
        not isinstance(parsed, dict)
        or data != core.canonical(parsed) + b"\n"
        or parsed.get("status") == "rejected"
        or parsed.get("diagnostics")
        or parsed.get("protocol") != "yuho.kernel-protocol/v1"
        or parsed.get("result_schema") != "yuho.kernel-result/v1"
        or parsed.get("request_id") != input_value["request_id"]
        or parsed.get("root_rule") != input_value["root_rule"]
        or parsed.get("input_digest") != input_digest
        or parsed.get("fragment") != input_value["fragment"]
    ):
        fail("SFE065", plan.path, plan.identifier, "kernel response contract failure")
    return data, parsed


def _registered(
    step: Step, response: dict, request: bytes, plan: PlanSource
) -> dict[str, object]:
    if step.variant.text == "SuppliedProofStatus-v1":
        status = response.get("status")
        rules = response.get("rules")
        if status not in {"satisfied", "not_satisfied", "unresolved"} or not isinstance(
            rules, list
        ):
            fail("SFE065", plan.path, step.identifier, "invalid proof status")
        roots = [
            rule
            for rule in rules
            if isinstance(rule, dict) and rule.get("id") == response.get("root_rule")
        ]
        if len(roots) != 1 or not isinstance(roots[0].get("branches"), list):
            fail("SFE065", plan.path, step.identifier, "root branch missing")
        branches = roots[0]["branches"]
        if len(branches) != 1 or branches[0].get("reason") not in {
            "satisfied",
            "requirements_not_satisfied",
            "defeated",
            "requirements_unresolved",
            "exception_unresolved",
        }:
            fail(
                "SFE065", plan.path, step.identifier, "unsupported proof branch reason"
            )
        reason = branches[0]["reason"]
        if (
            branches[0].get("status") != status
            or (status == "satisfied") != (reason == "satisfied")
            or (status == "unresolved")
            != (reason in {"requirements_unresolved", "exception_unresolved"})
        ):
            fail(
                "SFE065",
                plan.path,
                step.identifier,
                "proof status and branch reason disagree",
            )
        return {"root-status": status, "root-reason": reason}
    penalties = response.get("selected_penalties")
    if not isinstance(penalties, list) or any(
        not isinstance(row, dict)
        or row.get("penalty_id") not in {"pen:basic", "pen:enhanced"}
        for row in penalties
    ):
        fail("SFE065", plan.path, step.identifier, "invalid selected declaration")
    ids = [row["penalty_id"] for row in penalties]
    declared = json.loads(request)["registry"][0]["program"]["penalties"]
    declared_ids = {row["penalty_id"] for row in declared}
    if (
        not set(ids) <= declared_ids
        or response.get("status") not in {"true", "false", "unresolved"}
        or (response["status"] != "true" and ids)
    ):
        fail(
            "SFE065",
            plan.path,
            step.identifier,
            "selected ID or status disagrees with request",
        )
    if len(ids) != len(set(ids)):
        fail("SFE065", plan.path, step.identifier, "duplicate selected declaration")
    if step.variant.text == "GuardedPenaltySelection-v1":
        if len(ids) > 1:
            fail("SFE060", plan.path, step.identifier, "ambiguous candidate routing")
        return {"selected-penalties": ids, "selection-status": response["status"]}
    if len(ids) != 1:
        fail("SFE065", plan.path, step.identifier, "terms step selected no declaration")
    term = penalties[0].get("term")
    expected = next(row["term"] for row in declared if row["penalty_id"] == ids[0])
    if not isinstance(term, dict) or term != expected:
        fail(
            "SFE065",
            plan.path,
            step.identifier,
            "selected term does not match declaration",
        )
    return {"selected-terms": [{"penalty_id": ids[0], "term": term}]}


def execute(
    plan: PlanSource,
    scenario: Scenario,
    root: Path,
    kernel: Path,
    bundle_validator: Path,
    bundle_dir: Path,
) -> tuple[bytes, bytes, bytes, dict[str, str]]:
    requests, models, lock = _prepare(plan, scenario, root)
    # Every independent request is packaged and validated before the first kernel call.
    digests = {}
    for step in plan.steps:
        sid = step.identifier.text
        destination = bundle_dir / sid
        model = models[sid]
        if isinstance(model, core.SyntheticModel):
            digests[sid] = bundle.build(model, requests[sid], destination)
        else:
            digests[sid] = bundle.build_fragment(
                model.identifier.text,
                requests[sid],
                tuple(x.text for x in model.limitations),
                destination,
            )
        try:
            validation = subprocess.run(
                [str(bundle_validator), "validate", str(destination)],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            fail(
                "SFE064",
                plan.path,
                step.identifier,
                "bundle validator unavailable or timed out",
            )
        try:
            validated = json.loads(validation.stdout)
        except (UnicodeDecodeError, ValueError):
            fail(
                "SFE064",
                plan.path,
                step.identifier,
                "invalid bundle-validator response",
            )
        if (
            validation.returncode
            or validated.get("status") != "valid"
            or validated.get("bundle_digest") != digests[sid]
        ):
            fail(
                "SFE064",
                plan.path,
                step.identifier,
                "step ModelBundle validation failed",
            )
    plan_record = {
        "schema": PLAN_SCHEMA,
        "plan_id": plan.identifier.text,
        "version": plan.version.text,
        "language": LANGUAGE,
        "scope": {
            "jurisdiction": "Fictional",
            "authority": "none",
            "review": "none",
            "use": "compiler_fixture",
            "court_outcome": "excluded",
        },
        "steps": [
            {
                "id": x.identifier.text,
                "variant": x.variant.text,
                "module_id": x.module.text,
                "module_version": x.version.text,
                "request_sha256": core.sha(requests[x.identifier.text]),
                "bundle_digest": digests[x.identifier.text],
                "depends_on": []
                if x.gate is None
                else [x.gate.target.text.split("::")[0]],
                "gate": None
                if x.gate is None
                else {
                    "output": x.gate.target.text,
                    "operation": x.gate.operation.text,
                    "value": x.gate.value.text,
                },
            }
            for x in plan.steps
        ],
        "outputs": [x.text for x in plan.outputs],
        "limits": {
            "max_steps": MAX_STEPS,
            "max_edges": MAX_EDGES,
            "max_outputs": MAX_OUTPUTS,
            "max_request_bytes": MAX_REQUEST_BYTES,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "max_total_request_bytes": MAX_TOTAL_REQUEST_BYTES,
            "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        },
    }
    plan_bytes = core.canonical(plan_record)
    verify_compiled(plan_bytes, requests, digests, plan.path)
    registered: dict[str, dict] = {}
    skip_reasons: dict[str, str] = {}
    observations = []
    total_response = 0
    for step in plan.steps:
        sid = step.identifier.text
        gate = step.gate
        skip = None
        gate_result = (
            {"kind": "unconditional"}
            if gate is None
            else {
                "kind": "checked",
                "output": gate.target.text,
                "operation": gate.operation.text,
                "value": gate.value.text,
            }
        )
        if gate:
            upstream, output = gate.target.text.split("::")
            upstream_value = registered[upstream].get(output)
            if upstream in skip_reasons:
                skip = skip_reasons[upstream]
            elif gate.operation.text == "is":
                if upstream_value != gate.value.text:
                    reason = registered[upstream].get("root-reason")
                    skip = (
                        "upstream_unresolved"
                        if upstream_value == "unresolved"
                        else "upstream_defeated"
                        if reason == "defeated"
                        else "upstream_not_proved"
                    )
            elif not isinstance(upstream_value, list):
                skip = "candidate_not_selected"
            elif gate.value.text not in upstream_value:
                skip = (
                    "upstream_unresolved"
                    if registered[upstream].get("selection-status") == "unresolved"
                    else "candidate_not_selected"
                    if not upstream_value
                    else "alternate_candidate_selected"
                )
        if skip:
            registered[sid] = {}
            skip_reasons[sid] = skip
            observations.append(
                {
                    "id": sid,
                    "variant": step.variant.text,
                    "request_sha256": core.sha(requests[sid]),
                    "bundle_digest": digests[sid],
                    "state": "skipped",
                    "gate": {**gate_result, "matched": False},
                    "response_sha256": None,
                    "outputs": {},
                    "reason": skip,
                }
            )
            continue
        response_bytes, response = _run_kernel(kernel, requests[sid], plan)
        total_response += len(response_bytes)
        if total_response > MAX_TOTAL_RESPONSE_BYTES:
            fail(
                "SFE067",
                plan.path,
                step.identifier,
                "aggregate response limit exceeded",
            )
        output = _registered(step, response, requests[sid], plan)
        registered[sid] = output
        observations.append(
            {
                "id": sid,
                "variant": step.variant.text,
                "request_sha256": core.sha(requests[sid]),
                "bundle_digest": digests[sid],
                "state": "unresolved"
                if output.get("root-status") == "unresolved"
                else "completed",
                "gate": {**gate_result, "matched": True},
                "response_sha256": core.sha(response_bytes),
                "outputs": output,
                "reason": None,
            }
        )
    trace = core.canonical(
        {
            "schema": TRACE_SCHEMA,
            "plan_id": plan.identifier.text,
            "plan_sha256": core.sha(plan_bytes),
            "module_lock_sha256": core.sha(lock),
            "scenario_sha256": core.sha(scenario.source),
            "step_order": [x.identifier.text for x in plan.steps],
            "steps": observations,
            "outputs": {
                name.text: registered[name.text.split("::")[0]].get(
                    name.text.split("::")[1]
                )
                for name in plan.outputs
            },
            "scope": plan_record["scope"],
        }
    )
    return plan_bytes, lock, trace, digests
