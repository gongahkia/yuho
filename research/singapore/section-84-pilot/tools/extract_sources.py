#!/usr/bin/env python3
"""Offline, source-specific extraction from three pinned browser-saved SSO pages."""

from __future__ import annotations

import argparse
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile


TRANSFORM = "yuho.sg-legislation-html-extraction/v1"
MAX_HTML = 8 * 1024 * 1024
MAX_ASSET_BYTES = 20 * 1024 * 1024
MAX_ASSET_FILES = 100
MAX_TEXT = 2 * 1024 * 1024
MAX_JSON = 2 * 1024 * 1024
ACTS = (
    ("pc", "Penal Code 1871", "PC1871", "S04", ("84",), "penal-code-1871-section-84.txt"),
    ("ea", "Evidence Act 1893", "EA1893", "S05", ("107",), "evidence-act-1893-section-107.txt"),
    ("cpc", "Criminal Procedure Code 2010", "CPC2010", "S06",
     tuple(map(str, range(246, 257))) + ("256A", "256B", "256C"),
     "criminal-procedure-code-2010-uom.txt"),
)


class IntakeError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def safe_name(name: str) -> str:
    if name in ("", ".", "..") or "/" in name or "\\" in name or Path(name).is_absolute():
        raise IntakeError(f"unsafe relative name: {name!r}")
    return name


def bounded_regular(path: Path, limit: int) -> bytes:
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise IntakeError(f"expected regular file: {path.name}")
    if path.stat().st_size > limit:
        raise IntakeError(f"input size limit exceeded: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise IntakeError(f"input size limit exceeded: {path.name}")
    return data


def inventory(directory: Path) -> tuple[list[dict], str]:
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise IntakeError(f"expected companion directory: {directory.name}")
    entries = []
    total = 0
    for entry in sorted(directory.iterdir(), key=lambda p: p.name):
        safe_name(entry.name)
        data = bounded_regular(entry, MAX_ASSET_BYTES)
        total += len(data)
        if len(entries) >= MAX_ASSET_FILES or total > MAX_ASSET_BYTES:
            raise IntakeError("companion inventory limit exceeded")
        entries.append({"name": entry.name, "byte_length": len(data), "sha256": digest(data)})
    return entries, digest(canonical(entries))


class ProvisionParser(HTMLParser):
    """Read only top-level `div.prov1` nodes inside the saved active `div#legis`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.legis_depth = 0
        self.legis_count = 0
        self.section_depth = 0
        self.section_id = ""
        self.tokens: list[str] = []
        self.sections: dict[str, str] = {}
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        fields = dict(attrs)
        classes = set((fields.get("class") or "").split())
        if tag in ("script", "style"):
            self.ignored_depth += 1
            if self.section_depth:
                raise IntakeError("active content inside a provision")
            return
        if tag == "div" and fields.get("id") == "legis":
            if self.legis_depth or self.legis_count:
                raise IntakeError("ambiguous active legislation expression")
            self.legis_count += 1
            self.legis_depth = 1
            return
        if not self.legis_depth:
            return
        if tag == "div":
            self.legis_depth += 1
            if self.section_depth:
                self.section_depth += 1
            elif "prov1" in classes:
                self.section_depth = 1
                self.section_id = ""
                self.tokens = []
        if not self.section_depth:
            return
        if tag == "td" and "prov1Hdr" in classes:
            match = re.fullmatch(r"pr([0-9]+[A-Z]?)-", fields.get("id") or "")
            if match:
                self.section_id = match.group(1)
        if tag in ("tr", "br", "p") or (tag == "td" and (
                classes & {"prov1Hdr", "prov1Txt", "prov2Txt", "pTxt", "def", "p1tbl"}
                or any(re.fullmatch(r"p[0-9]+(?:No|Txt)", item) for item in classes))) or (
                tag == "div" and "amendNote" in classes):
            self.tokens.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self.ignored_depth = max(0, self.ignored_depth - 1)
            return
        if tag != "div" or not self.legis_depth:
            return
        if self.section_depth:
            self.section_depth -= 1
            if not self.section_depth:
                if self.section_id in self.sections:
                    raise IntakeError(f"duplicate provision ID: {self.section_id}")
                if self.section_id:
                    lines = [re.sub(r"\s+", " ", line).strip()
                             for line in "".join(self.tokens).split("\n")]
                    self.sections[self.section_id] = "\n".join(line for line in lines if line) + "\n"
        self.legis_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.section_depth and not self.ignored_depth:
            self.tokens.append(data)


def inspect_page(raw: bytes, title: str, act_code: str, required: tuple[str, ...]) -> tuple[dict, dict[str, str]]:
    try:
        page = raw.decode("utf-8", "strict")
    except UnicodeError as error:
        raise IntakeError("HTML is not valid UTF-8") from error
    if not re.search(r'<meta\s+http-equiv="Content-Type"\s+content="text/html; charset=UTF-8"', page, re.I):
        raise IntakeError("expected UTF-8 HTML declaration missing")
    expected_title = f"{title} - Singapore Statutes Online"
    if not re.search(r"<title>" + re.escape(expected_title) + r"</title>", page):
        raise IntakeError(f"wrong or error page for {title}")
    url_match = re.search(r"<!-- saved from url=\([0-9]+\)(https://sso\.agc\.gov\.sg/Act/[A-Z0-9]+) -->", page)
    if not url_match or url_match.group(1) != f"https://sso.agc.gov.sg/Act/{act_code}":
        raise IntakeError(f"missing or wrong saved source URL for {title}")
    status = re.search(r'<div class="doc-status">([^<]+)</div>', page)
    generated = re.search(r'<div class="generated-on">([^<]+)</div>', page)
    front = re.search(r'<div class="front">(.{0,1800})', page, re.S)
    if not status or not generated or not front:
        raise IntakeError(f"missing version or active expression metadata for {title}")
    if not re.fullmatch(r"Current version as at [0-9]{1,2} [A-Z][a-z]{2} [0-9]{4} ?", status.group(1)):
        raise IntakeError(f"ambiguous version label for {title}")
    if not re.fullmatch(r"HTML created on: [0-9]{1,2} [A-Z][a-z]{2} [0-9]{4}", generated.group(1)):
        raise IntakeError(f"ambiguous HTML generation label for {title}")
    front_text = unescape(re.sub(r"<[^>]*>", " ", front.group(1)))
    if title not in front_text or "2020 REVISED EDITION" not in front_text:
        raise IntakeError(f"wrong or incomplete active expression for {title}")
    parser = ProvisionParser()
    parser.feed(page)
    parser.close()
    if parser.legis_count != 1 or parser.legis_depth:
        raise IntakeError(f"incomplete or ambiguous active expression for {title}")
    for number in required:
        section = parser.sections.get(number)
        if not section:
            raise IntakeError(f"missing provision {number} in {title}")
        if f"{number}." not in section[:300]:
            raise IntakeError(f"provision {number} lacks matching numbered text")
    return {
        "source_url": url_match.group(1), "page_title": expected_title,
        "legislation_title": title, "observed_status": status.group(1).strip(),
        "observed_html_created_on": generated.group(1).removeprefix("HTML created on: "),
        "observed_edition": "2020 REVISED EDITION",
        "expression_selection": "single active div#legis; legislative history and navigation excluded",
    }, {key: parser.sections[key] for key in required}


def line_position(data: bytes, offset: int) -> tuple[int, int]:
    line = data.count(b"\n", 0, offset) + 1
    last = data.rfind(b"\n", 0, offset)
    return line, offset - last


ANCHORS = (
    ("P84-01", "pc", "Nothing is an offence", "direct_text", "post-1-March-2022 snapshot label"),
    ("P84-02", "pc", "at the time of doing it", "direct_text", "act-time text; no case finding"),
    ("P84-03", "pc", "by reason of unsoundness of mind", "direct_text", "causal wording only; interpretation unresolved"),
    ("P84-04", "pc", "incapable of knowing the nature of the act;", "direct_text", "no diagnosis or proof inference"),
    ("P84-05", "pc", "is wrong by the ordinary standards of reasonable and honest persons; and", "direct_text", "one of two listed limbs; construction requires review"),
    ("P84-05", "pc", "is wrong as contrary to law.", "direct_text", "second listed limb; construction requires review"),
    ("P84-07", "pc", "completely deprived of any power to control his actions.", "direct_text", "no proof or application inference"),
    ("P84-09", "ea", "the court is to presume the absence of such circumstances.", "direct_text", "burden/standard interpretation unresolved"),
    ("P84-11", "cpc", "Acquittal on ground of unsound mind", "context_only", "court procedure, never a kernel outcome"),
    ("P84-12", "cpc", "Procedure if accused is suspected to be incapable of making defence", "context_only", "fitness is distinct from act-time responsibility"),
    ("P84-13", "cpc", "Safe custody of person acquitted", "context_only", "procedure depends on proceeding date"),
)


REPRESENTABILITY = {
    "P84-01": ("representable_by_convention", ["AcyclicGuardedExceptions-v1"], "exception target only; no legal applicability decision"),
    "P84-02": ("representable_by_convention", ["SuppliedProofStatus-v1"], "externally classified act-time proposition"),
    "P84-03": ("requires_new_semantics", ["SuppliedProofStatus-v1"], "causation cannot be derived from separate Boolean leaves"),
    "P84-04": ("representable_by_convention", ["ClosedBooleanBranches-v1"], "source-order alternative only"),
    "P84-05": ("representable_by_convention", ["ClosedBooleanBranches-v1"], "two source-order wrongfulness clauses; legal construction unreviewed"),
    "P84-06": ("legally_unresolved", [], "earlier expression not in selected active provision"),
    "P84-07": ("representable_by_convention", ["ClosedBooleanBranches-v1"], "source-order alternative only"),
    "P84-08": ("requires_new_semantics", [], "no medical-evidence assessment"),
    "P84-09": ("requires_new_semantics", ["TypedBooleanFacts-v1"], "metadata agreement is not burden discharge or EA presumption"),
    "P84-10": ("representable_by_convention", ["SuppliedProofStatus-v1"], "prosecution burden not computed"),
    "P84-11": ("procedural_and_out_of_scope", [], "court acquittal is not kernel branch defeat"),
    "P84-12": ("procedural_and_out_of_scope", [], "fitness requires separate proceeding"),
    "P84-13": ("procedural_and_out_of_scope", [], "CPC order is not kernel result"),
    "P84-14": ("legally_unresolved", [], "intoxication boundary excluded"),
    "P84-15": ("procedural_and_out_of_scope", [], "diminished responsibility excluded"),
    "P84-16": ("legally_unresolved", [], "section 323 anchor unreviewed"),
    "P84-17": ("legally_unresolved", [], "historical case treatment unresolved"),
    "P84-18": ("procedural_and_out_of_scope", ["PenaltyTerms-v1"], "selected term is not imposed punishment"),
}

# ledger IDs describe research support, including non-statutory and unavailable sources.
PROPOSITION_SOURCES = {
    "P84-01": ["S04", "S05", "S16"], "P84-02": ["S02", "S09"],
    "P84-03": ["S01", "S02", "S09", "S18"], "P84-04": ["S09"],
    "P84-05": ["S02", "S03", "S09", "S11"], "P84-06": ["S01", "S02", "S16"],
    "P84-07": ["S01", "S09"], "P84-08": ["S09", "S17", "S18"],
    "P84-09": ["S05"], "P84-10": ["S05", "S10"],
    "P84-11": ["S16", "S19"], "P84-12": ["S12", "S13"],
    "P84-13": ["S06", "S12", "S14", "S15", "S16"],
    "P84-14": ["S02", "S17"], "P84-15": ["S09"],
    "P84-16": ["S04"], "P84-17": ["S01", "S02", "S16", "S17"],
    "P84-18": ["S16"],
}


def build_packet(input_dir: Path, inspection_timestamp: str) -> dict[str, bytes]:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", inspection_timestamp):
        raise IntakeError("inspection timestamp must be explicit UTC ISO text")
    if not stat.S_ISDIR(input_dir.lstat().st_mode):
        raise IntakeError("input directory is not a real directory")
    expected = {f"{title} - Singapore Statutes Online.html" for _, title, *_ in ACTS}
    expected |= {name.removesuffix(".html") + "_files" for name in expected}
    actual = {entry.name for entry in input_dir.iterdir()}
    if actual != expected:
        raise IntakeError(f"missing or unexpected top-level entries: {sorted(expected ^ actual)}")
    receipts = []
    artifacts = []
    outputs: dict[str, bytes] = {}
    source_data = {}
    for key, title, act_code, ledger_id, required, output_name in ACTS:
        name = f"{title} - Singapore Statutes Online.html"
        raw = bounded_regular(input_dir / name, MAX_HTML)
        companion = input_dir / (name.removesuffix(".html") + "_files")
        assets, asset_digest = inventory(companion)
        observed, sections = inspect_page(raw, title, act_code, required)
        extracted = "\n".join(sections[number].rstrip("\n") for number in required) + "\n"
        data = extracted.encode("utf-8")
        if len(data) > MAX_TEXT:
            raise IntakeError(f"extracted text size limit exceeded: {title}")
        rel = f"extracted/{output_name}"
        outputs[rel] = data
        source_data[key] = {"source_id": f"sg:{act_code}", "ledger_id": ledger_id,
                            "digest": digest(data), "bytes": data, "path": rel}
        receipts.append({
            "source_id": f"sg:{act_code}", "source_ledger_id": ledger_id, "original_filename": name,
            "acquisition_class": "browser_saved_complete_html", "byte_length": len(raw),
            "sha256": digest(raw), "detected_encoding": "utf-8", **observed,
            "inspection_timestamp": inspection_timestamp, "acquisition_timestamp": {"kind": "not_recorded"},
            "companion_directory": companion.name, "companion_files": len(assets),
            "companion_inventory_sha256": asset_digest, "relevant_provisions_present": list(required),
            "extraction_status": "extracted", "authority_status": "unverified_browser_snapshot",
            "redistribution_status": "not_redistributed_permission_unverified",
            "verification_limitations": ["browser capture and page labels are not authenticated",
                                       "point-in-time applicability and later changes require qualified review",
                                       "companion assets are inventory only, not legislative sources"],
        })
        artifacts.append({"source_id": f"sg:{act_code}", "source_input_sha256": digest(raw),
                          "extraction_transform": TRANSFORM, "extracted_filename": rel,
                          "extracted_byte_length": len(data), "extracted_sha256": digest(data),
                          "included_provisions": list(required), "encoding": "utf-8", "line_endings": "lf",
                          "excluded_content": ["navigation", "legislative history", "other provisions", "scripts", "styles", "companion assets"],
                          "warnings": ["observed current-version label is unverified",
                                       "HTML-to-text transformation does not establish source or extraction fidelity"]})
    mappings = []
    for proposition, key, phrase, support, note in ANCHORS:
        source = source_data[key]
        needle = phrase.encode("utf-8")
        data = source["bytes"]
        if data.count(needle) != 1:
            raise IntakeError(f"missing or ambiguous exact anchor for {proposition}: {phrase[:32]}")
        start = data.index(needle)
        end = start + len(needle)
        start_line, start_col = line_position(data, start)
        end_line, end_col = line_position(data, end)
        mappings.append({"proposition_id": proposition, "source_id": source["source_id"],
                         "extracted_artifact_sha256": source["digest"], "start": start, "end": end,
                         "start_line": start_line, "start_col": start_col,
                         "end_line": end_line, "end_col": end_col,
                         "support": support, "support_sha256": digest(needle),
                         "short_supporting_text": phrase if len(phrase) <= 80 else None,
                         "temporal_qualification": "snapshot label 13 Sep 2026; legal applicability unverified",
                         "unresolved_interpretation": note})
    direct_ids = {item["proposition_id"] for item in mappings}
    representation = []
    for proposition, (classification, fragments, note) in REPRESENTABILITY.items():
        representation.append({"proposition_id": proposition,
                               "source_ids": PROPOSITION_SOURCES[proposition],
                               "classification": classification, "existing_fragments": fragments,
                               "non_executable_structure": note, "missing_capability": note,
                               "legal_review_dependency": "exact source version, statutory meaning and scope require qualified review",
                               "directly_source_spanned": proposition in direct_ids,
                               "no_executable_claim": "no KernelInput request or factual assignment is generated"})
    scope = {"schema": "yuho.sg-section-84-intake-scope/v1", "packet_kind": "pre_bundle_source_and_representability_packet",
             "positive_scope": ["source intake", "section 84 statutory structure", "Evidence Act section 107 textual context",
                                "CPC sections 246-256C textual context", "exact extracted-text spans",
                                "representability against existing Yuho constructs"],
             "exclusions": ["person-specific unsoundness", "evidence assessment", "medical diagnosis", "section 84 success",
                            "anchor offence", "Penal Code section 323 execution", "fitness-to-plead determination",
                            "CPC court order", "conviction", "acquittal", "sentencing", "current-law certification",
                            "legal advice", "independent legal review", "authenticated source provenance"],
             "model_bundle_status": "blocked_no_executable_model_or_reviewed_source"}
    generated = {
        "SOURCE-RECEIPT.json": {"schema": "yuho.sg-section-84-source-receipt/v1", "sources": receipts},
        "EXTRACTION-MANIFEST.json": {"schema": "yuho.sg-section-84-extraction-manifest/v1", "transform": TRANSFORM,
                                     "transformations": ["strict UTF-8 decode", "HTML character-reference decode",
                                                         "select active div#legis and exact div.prov1 IDs",
                                                         "insert LF before provision and table/list rows",
                                                         "collapse whitespace within each structural line to one ASCII space",
                                                         "strip line-edge whitespace and empty lines", "no Unicode normalization"],
                                     "artifacts": artifacts},
        "STATUTORY-SPAN-MAP.json": {"schema": "yuho.sg-section-84-span-map/v1", "mappings": mappings},
        "REPRESENTABILITY-MAP.json": {"schema": "yuho.sg-section-84-representability/v1", "entries": representation},
        "MODEL-SCOPE.json": scope,
    }
    for name, value in generated.items():
        encoded = canonical(value)
        if len(encoded) > MAX_JSON:
            raise IntakeError(f"generated JSON size limit exceeded: {name}")
        outputs[name] = encoded
    return outputs


def verify_lock(outputs: dict[str, bytes], input_dir: Path, lock_path: Path) -> None:
    lock = json.loads(bounded_regular(lock_path, MAX_JSON).decode("utf-8", "strict"))
    if lock.get("transform") != TRANSFORM:
        raise IntakeError("source lock transform mismatch")
    receipts = json.loads(outputs["SOURCE-RECEIPT.json"])["sources"]
    sources = [{key: receipt[key] for key in ("source_id", "original_filename", "byte_length", "sha256")}
               for receipt in receipts]
    generated = [{"path": name, "sha256": digest(data), "byte_length": len(data)}
                 for name, data in sorted(outputs.items())]
    if lock.get("sources") != sources or lock.get("generated_artifacts") != generated:
        raise IntakeError("source lock mismatch: input or generated bytes differ")


def write_packet(output_dir: Path, outputs: dict[str, bytes]) -> None:
    parent = output_dir.parent
    if not parent.is_dir():
        raise IntakeError("output parent directory missing")
    if output_dir.exists() or output_dir.is_symlink():
        if not stat.S_ISDIR(output_dir.lstat().st_mode):
            raise IntakeError("output is not a real directory")
        found = {}
        for path in output_dir.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            rel = path.relative_to(output_dir).as_posix()
            found[rel] = bounded_regular(path, MAX_TEXT if rel.endswith(".txt") else MAX_JSON)
        if found:
            if found != outputs:
                raise IntakeError("non-empty output differs; refusing to overwrite")
            return
    temp = Path(tempfile.mkdtemp(prefix=".sg-s84-intake-", dir=parent))
    try:
        for name, data in outputs.items():
            target = temp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if output_dir.exists():
            output_dir.rmdir()
        os.replace(temp, output_dir)
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main() -> int:
    argument = argparse.ArgumentParser(description=__doc__)
    argument.add_argument("--input-dir", type=Path, required=True)
    argument.add_argument("--output-dir", type=Path, required=True)
    argument.add_argument("--inspection-timestamp", required=True)
    argument.add_argument("--verify-lock", type=Path)
    args = argument.parse_args()
    try:
        source_root = args.input_dir.resolve()
        output_root = args.output_dir.resolve()
        if source_root == output_root or output_root.is_relative_to(source_root) or source_root.is_relative_to(output_root):
            raise IntakeError("input and output directories must be separate")
        outputs = build_packet(args.input_dir, args.inspection_timestamp)
        if args.verify_lock:
            verify_lock(outputs, args.input_dir, args.verify_lock)
        write_packet(args.output_dir, outputs)
    except (IntakeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        argument.exit(1, f"intake rejected: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
