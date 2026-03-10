"""
Verification report generator.

Produces a LaTeX document summarizing the structural completeness
of statutes: element coverage, penalty ranges, exception guards,
and cross-references.
"""

from typing import List

from yuho.ast import nodes


def generate_verification_report(ast: nodes.ModuleNode) -> str:
    """Generate a LaTeX verification report for all statutes in the module."""
    lines: List[str] = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage[margin=1in]{geometry}")
    lines.append(r"\usepackage{booktabs,longtable,xcolor}")
    lines.append(r"\definecolor{pass}{RGB}{0,128,0}")
    lines.append(r"\definecolor{warn}{RGB}{200,150,0}")
    lines.append(r"\definecolor{fail}{RGB}{200,0,0}")
    lines.append(r"\newcommand{\pass}{\textcolor{pass}{\textbf{PASS}}}")
    lines.append(r"\newcommand{\warn}{\textcolor{warn}{\textbf{WARN}}}")
    lines.append(r"\newcommand{\fail}{\textcolor{fail}{\textbf{FAIL}}}")
    lines.append(r"\begin{document}")
    lines.append(r"\title{Yuho Verification Report}")
    lines.append(r"\maketitle")

    if not ast.statutes:
        lines.append(r"\section*{No statutes found}")
        lines.append(r"\end{document}")
        return "\n".join(lines)

    for statute in ast.statutes:
        title = statute.title.value if statute.title else "Untitled"
        lines.append(rf"\section{{Section {statute.section_number}: {_escape(title)}}}")
        checks = _check_statute(statute)
        lines.append(r"\begin{longtable}{lll}")
        lines.append(r"\toprule")
        lines.append(r"Check & Status & Details \\")
        lines.append(r"\midrule")
        for check_name, status, detail in checks:
            status_cmd = {True: r"\pass", False: r"\fail"}.get(status, r"\warn")
            lines.append(rf"{_escape(check_name)} & {status_cmd} & {_escape(detail)} \\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{longtable}")

    lines.append(r"\end{document}")
    return "\n".join(lines)


def _check_statute(statute: nodes.StatuteNode) -> list:
    """Run structural checks on a statute and return (name, pass, detail) tuples."""
    checks = []
    # title
    checks.append(("Has title", statute.title is not None, statute.title.value if statute.title else "missing"))
    # elements
    elem_count = _count_elements(statute.elements)
    checks.append(("Has elements", elem_count > 0, f"{elem_count} element(s)"))
    # actus reus
    ar = _count_by_type(statute.elements, "actus_reus")
    checks.append(("Actus reus present", ar > 0, f"{ar} actus reus"))
    # mens rea
    mr = _count_by_type(statute.elements, "mens_rea")
    checks.append(("Mens rea present", mr > 0, f"{mr} mens rea"))
    # penalty
    checks.append(("Has penalty", statute.penalty is not None, "present" if statute.penalty else "missing"))
    # definitions
    checks.append(("Has definitions", len(statute.definitions) > 0, f"{len(statute.definitions)} definition(s)"))
    # illustrations
    checks.append(("Has illustrations", len(statute.illustrations) > 0, f"{len(statute.illustrations)} illustration(s)"))
    # exceptions
    exc_count = len(statute.exceptions)
    if exc_count > 0:
        guarded = sum(1 for e in statute.exceptions if e.guard)
        checks.append(("Exception guards", guarded == exc_count, f"{guarded}/{exc_count} guarded"))
    # jurisdiction
    checks.append(("Jurisdiction set", statute.jurisdiction is not None, statute.jurisdiction or "not set"))
    # doc-comment
    checks.append(("Doc-comment", statute.doc_comment is not None, "present" if statute.doc_comment else "missing"))
    return checks


def _count_elements(elements) -> int:
    count = 0
    for e in elements:
        if isinstance(e, nodes.ElementGroupNode):
            count += _count_elements(e.members)
        else:
            count += 1
    return count


def _count_by_type(elements, etype: str) -> int:
    count = 0
    for e in elements:
        if isinstance(e, nodes.ElementGroupNode):
            count += _count_by_type(e.members, etype)
        elif isinstance(e, nodes.ElementNode) and e.element_type == etype:
            count += 1
    return count


def _escape(text: str) -> str:
    """Escape LaTeX special characters."""
    for char in ["&", "%", "$", "#", "_", "{", "}"]:
        text = text.replace(char, f"\\{char}")
    return text
