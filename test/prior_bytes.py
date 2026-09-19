"""Compare all six prior protocol families with their committed baseline bytes."""

import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9dd40b628bfb18e50f10050f3e9300e7f5bfc7c1"
FAMILIES = [
    ("frozen", ROOT / "test/kernel-fixtures/frozen/requests"),
    ("H", ROOT / "test/fixtures/requests"),
    ("E", ROOT / "test/exception-fixtures/requests"),
    ("T", ROOT / "test/typed-fixtures/requests"),
    ("GP", ROOT / "test/penalty-fixtures/requests"),
    ("PT", ROOT / "test/term-fixtures/requests"),
    ("PS", ROOT / "test/proof-fixtures/requests"),
]
GHC = (os.environ.get("YUHO_GHC") or shutil.which("ghc-9.8.4")
       or str(Path.home() / ".ghcup/bin/ghc-9.8.4"))


def request_bytes(path):
    raw = path.read_bytes()
    if path.suffix == ".json":
        raw = (json.dumps(json.loads(raw), sort_keys=True, ensure_ascii=False,
                          separators=(",", ":")) + "\n").encode()
    return raw.rstrip(b"\r\n") + b"\n"


def binary(workspace):
    return subprocess.check_output(["cabal", "list-bin", "exe:yuho-kernel",
                                    f"--with-compiler={GHC}"],
                                   cwd=workspace, text=True).strip()


def responses(executable, requests):
    completed = subprocess.run([executable], input=b"".join(requests),
                               capture_output=True, check=True, timeout=120)
    assert not completed.stderr, completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(requests)
    return lines


def main():
    version = subprocess.check_output([GHC, "--numeric-version"], text=True).strip()
    if version != "9.8.4":
        raise SystemExit(f"prior-byte comparison requires GHC 9.8.4, found {version}")
    archive = subprocess.run(["git", "archive", BASELINE, "rewrite/haskell"],
                             cwd=ROOT, capture_output=True, check=True).stdout
    with tempfile.TemporaryDirectory(prefix="yuho-six-variant-baseline-") as folder:
        target = Path(folder)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(target, filter="data")
        workspace = target / "rewrite/haskell"
        subprocess.run(["cabal", "v2-build", "exe:yuho-kernel", "--offline", "--jobs=1",
                        f"--with-compiler={GHC}"],
                       cwd=workspace, check=True, capture_output=True)
        original = binary(workspace)
        current = binary(ROOT)
        total = 0
        for label, directory in FAMILIES:
            paths = sorted(path for path in directory.iterdir()
                           if path.suffix in (".json", ".txt"))
            requests = [request_bytes(path) for path in paths]
            old = responses(original, requests)
            new = responses(current, requests)
            differences = [path.name for path, before, after in zip(paths, old, new,
                strict=True) if before != after]
            assert not differences, (label, differences)
            print(f"{label}: {len(paths)} exact baseline response bytes")
            total += len(paths)
        print(f"all {total} earlier request responses are byte-identical to {BASELINE}")


if __name__ == "__main__":
    main()
