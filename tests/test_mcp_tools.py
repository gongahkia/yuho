"""MCP server tool unit tests.

Skipped automatically if the ``mcp`` (model-context-protocol) package
isn't installed (it's an optional dep under ``yuho[mcp]``). When the
package is present, we drive each tool function via the
``FastMCP.call_tool`` API without going through the wire protocol.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

mcp_pkg = pytest.importorskip("mcp", reason="mcp not installed (yuho[mcp])")

from yuho.mcp.server import create_server, YuhoMCPServer  # noqa: E402


@pytest.fixture(scope="module")
def server() -> YuhoMCPServer:
    return create_server()


def _run(coro):
    """Run a coroutine to completion in a clean event loop."""
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _call(server: YuhoMCPServer, name: str, args: dict):
    """Invoke a tool by name and return its dict payload, unwrapping the
    FastMCP envelope. FastMCP wraps the tool's return value in
    ``{"result": <value>}`` and additionally returns a content_list /
    structured_dict tuple.
    """
    result = _run(server.server.call_tool(name, args))
    payload = None
    # FastMCP returns (content_list, structured_dict). We want the structured dict.
    if isinstance(result, tuple) and len(result) >= 2 and isinstance(result[1], dict):
        payload = result[1]
    elif isinstance(result, dict):
        payload = result
    elif isinstance(result, list) and result and hasattr(result[0], "text"):
        try:
            payload = json.loads(result[0].text)
        except Exception:
            payload = {"raw": result[0].text}
    else:
        payload = {"raw": result}

    # FastMCP wraps the tool's actual return value under "result".
    if isinstance(payload, dict) and set(payload.keys()) == {"result"}:
        return payload["result"]
    return payload


# ---------------------------------------------------------------------------
# Tool inventory
# ---------------------------------------------------------------------------


class TestToolInventory:
    def test_at_least_26_tools_registered(self, server):
        tools = _run(server.server.list_tools())
        assert len(tools) >= 26, f"expected ≥ 26 tools, got {len(tools)}"

    def test_research_tools_registered(self, server):
        tools = _run(server.server.list_tools())
        names = {t.name for t in tools}
        # The four research tools added in v5.1.
        for required in (
            "yuho_section_references",
            "yuho_simulate_fact_pattern",
            "yuho_verify_grounded",
            "yuho_benchmark_task",
        ):
            assert required in names, f"missing research tool: {required}"


# ---------------------------------------------------------------------------
# Core language ops
# ---------------------------------------------------------------------------


class TestCoreOps:
    def test_yuho_check_on_valid_source(self, server):
        src = Path("library/penal_code/s415_cheating/statute.yh").read_text()
        result = _call(server, "yuho_check", {"file_content": src})
        assert result.get("valid") is True, result

    def test_yuho_check_on_broken_source(self, server):
        bad = 'statute 999 "broken" effective 1872-01-01 {\n  elements { actu_reus x = "y"; }\n}\n'
        result = _call(server, "yuho_check", {"file_content": bad})
        assert result.get("valid") is False
        # parse_errors or similar should surface
        assert any(k in result for k in ("parse_errors", "errors", "diagnostics"))

    def test_yuho_transpile_english(self, server):
        src = Path("library/penal_code/s415_cheating/statute.yh").read_text()
        result = _call(server, "yuho_transpile", {"file_content": src, "target": "english"})
        assert "Cheating" in (result.get("output") or result.get("result") or "")


# ---------------------------------------------------------------------------
# Library / corpus tools
# ---------------------------------------------------------------------------


class TestLibraryTools:
    def test_section_pair(self, server):
        result = _call(server, "yuho_section_pair", {"section": "415"})
        assert "raw" in result or "canonical" in result or "text" in str(result).lower()

    def test_coverage_status(self, server):
        result = _call(server, "yuho_coverage_status", {})
        # Some shape with totals.
        assert isinstance(result, dict)

    def test_library_list(self, server):
        result = _call(server, "yuho_library_list", {"limit": 5})
        # Should produce a list-shaped response.
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# G10 reference graph
# ---------------------------------------------------------------------------


class TestSectionReferences:
    def test_outgoing_from_s300(self, server):
        result = _call(server, "yuho_section_references", {"section": "300", "direction": "out"})
        outgoing = result.get("outgoing") or []
        # s300 should have at least one outgoing edge (subsumes s299 per the live graph).
        assert len(outgoing) >= 1, result

    def test_unknown_section(self, server):
        result = _call(server, "yuho_section_references", {"section": "99999"})
        # Either error or empty edges — both are acceptable shapes.
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Verify-grounded
# ---------------------------------------------------------------------------


class TestVerifyGrounded:
    def test_grounded_answer(self, server):
        answer = {
            "claims": [
                {
                    "text": "s415 requires deception",
                    "citations": [
                        {
                            "section": "415",
                            "kind": "raw",
                            "span": "deceiving any person",
                        }
                    ],
                }
            ]
        }
        result = _call(server, "yuho_verify_grounded", {"answer": answer})
        assert result.get("n_grounded") == 1, result

    def test_orphan_claim(self, server):
        answer = {"claims": [{"text": "made-up claim", "citations": []}]}
        result = _call(server, "yuho_verify_grounded", {"answer": answer})
        assert result.get("n_orphans", 0) == 1


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


class TestBenchmark:
    def test_unknown_task_type(self, server):
        result = _call(server, "yuho_benchmark_task", {"task_type": "bogus", "n": 1})
        # Standard error envelope: {ok: false, error_code: "invalid_argument", ...}
        assert result.get("ok") is False
        assert result.get("error_code") == "invalid_argument"
        assert "valid_types" in result

    def test_known_task_type(self, server):
        # Skip if benchmarks aren't built.
        if not Path("benchmarks/tasks/citation_grounding.jsonl").exists():
            pytest.skip("benchmarks not built")
        result = _call(server, "yuho_benchmark_task", {"task_type": "citation_grounding", "n": 2})
        assert result.get("n_returned") == 2


# ---------------------------------------------------------------------------
# Resource sanity
# ---------------------------------------------------------------------------


class TestExplorerAndRecommender:
    """End-to-end MCP wiring tests for the two analytical surfaces.

    These exercise the full FastMCP path (rate-limit lookup, dispatch,
    return-value envelope) — not just the underlying core function — so
    a regression in the tool decorator stack would show up here.
    """

    def test_explore_counterexamples_present_and_callable(self, server):
        tools = _run(server.server.list_tools())
        names = {t.name for t in tools}
        assert "yuho_explore_counterexamples" in names

    def test_explore_counterexamples_round_trip(self, server):
        src = Path("library/penal_code/s415_cheating/statute.yh").read_text()
        try:
            import z3  # noqa: F401
        except Exception:
            pytest.skip("z3 not installed; explorer requires it")
        result = _call(server, "yuho_explore_counterexamples",
                       {"file_content": src, "section": "415",
                        "max_satisfying": 2})
        assert result.get("ok") is True, result
        rep = result["report"]
        assert rep["section"] == "415"
        assert rep["available"] is True
        assert rep["summary"]["conviction_reachable"] is True

    def test_explore_counterexamples_unknown_section_envelope(self, server):
        # Wiring regression check: a parsed module that lacks the requested
        # section should round-trip as ok=True / report.available=False.
        # If the input doesn't even parse, ok=False with mcp_error envelope.
        src = Path("library/penal_code/s415_cheating/statute.yh").read_text()
        result = _call(server, "yuho_explore_counterexamples",
                       {"file_content": src, "section": "9999"})
        assert result.get("ok") is True
        assert result["report"]["available"] is False
        assert "not found" in (result["report"]["reason"] or "").lower()

    def test_recommend_charges_present_and_callable(self, server):
        tools = _run(server.server.list_tools())
        names = {t.name for t in tools}
        assert "yuho_recommend_charges" in names

    def test_recommend_charges_returns_disclaimer(self, server):
        if not Path("library/penal_code/_corpus/sections").exists():
            pytest.skip("corpus not built")
        facts = {
            "name": "A intentionally deceives B",
            "acts": [
                {"actor": "A", "description": "deceives B about a worthless article"},
                {"actor": "A", "description": "induces B to deliver property"},
            ],
            "mental_states": {"A": {"intent": "to defraud"}},
        }
        result = _call(server, "yuho_recommend_charges",
                       {"facts": facts, "top_k": 3})
        assert result.get("ok") is True, result
        rec = result["recommendation"]
        # Disclaimer fields are load-bearing — clients rely on them.
        assert rec["not_legal_advice"] is True
        assert "disclaimer" in rec and rec["disclaimer"]
        assert isinstance(rec["candidates"], list)

    def test_recommend_charges_rate_limit_override_registered(self, server):
        # The two new tools should be in the per-tool override map,
        # otherwise they fall back to the global limit and may be too aggressive.
        overrides = server.rate_limiter.config.per_tool_overrides
        assert "yuho_explore_counterexamples" in overrides
        assert "yuho_recommend_charges" in overrides


class TestResources:
    def test_resources_listed(self, server):
        resources = _run(server.server.list_resources())
        names = {str(r.uri) for r in resources}
        # At least these primary entry points should be present.
        for required in (
            "yuho://library/index",
            "yuho://coverage",
            "yuho://gaps",
        ):
            assert any(n.startswith(required) for n in names), (
                f"missing resource: {required}, found: {sorted(names)[:5]}..."
            )
