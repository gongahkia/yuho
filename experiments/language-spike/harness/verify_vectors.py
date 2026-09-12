"""Read back candidate proof vectors and check all identifiers and trace edges."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for language in ("HASKELL", "OCAML"):
    vectors = json.loads((ROOT / f"results/{language}-PROOF-VECTORS.json").read_bytes())
    assert [item["case"] for item in vectors] == [f"B{index:02d}" for index in range(1, 8)]
    for vector in vectors:
        expected = json.loads((ROOT / f"fixtures/expected/{vector['case']}.json").read_bytes())
        assert vector["branches"] == expected["branches"]
        assert vector["trace"] == expected["trace"]
        by_branch = {}
        for edge in vector["trace"]:
            by_branch.setdefault(edge["branch"], {})[edge["id"]] = edge
            assert edge["path"] and edge["span"]["start"] <= edge["span"]["end"]
        for edge in vector["trace"]:
            assert all(child in by_branch[edge["branch"]] for child in edge["children"])
        for branch in vector["branches"]:
            assert branch["path"]
            assert branch["trace_ids"] == [edge["id"] for edge in vector["trace"]
                                            if edge["branch"] == branch["id"]]
    print(f"{language}: seven proof vectors decode with IDs, paths and trace edges intact")
