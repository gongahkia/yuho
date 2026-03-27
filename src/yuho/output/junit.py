"""JUnit XML output for CI test result ingestion."""

import xml.etree.ElementTree as ET
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """A single test result."""

    name: str
    classname: str = "yuho"
    time_s: float = 0.0
    passed: bool = True
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None


def to_junit_xml(
    results: List[TestResult],
    suite_name: str = "yuho",
    suite_time: float = 0.0,
) -> str:
    """Convert test results to JUnit XML string."""
    failures = sum(1 for r in results if not r.passed)
    suite = ET.Element(
        "testsuite",
        {
            "name": suite_name,
            "tests": str(len(results)),
            "failures": str(failures),
            "errors": "0",
            "time": f"{suite_time:.3f}",
        },
    )
    for r in results:
        tc = ET.SubElement(
            suite,
            "testcase",
            {
                "name": r.name,
                "classname": r.classname,
                "time": f"{r.time_s:.3f}",
            },
        )
        if not r.passed and r.failure_message:
            fail = ET.SubElement(
                tc,
                "failure",
                {
                    "message": r.failure_message,
                    "type": r.failure_type or "AssertionError",
                },
            )
            fail.text = r.failure_message
    tree = ET.ElementTree(suite)
    import io

    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue().decode("utf-8")
