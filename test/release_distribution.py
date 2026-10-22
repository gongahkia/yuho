"""Reject substituted historical sources before any baseline compilation."""

from pathlib import Path
import importlib.util
import io
import os
import tarfile
import tempfile

import prior_bytes


def extraction_checks(source_root, scratch):
    spec = importlib.util.spec_from_file_location("extract_bundle", source_root / "scripts/extract_reproducibility_bundle.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    def archive(name, extra):
        path = scratch / (name + ".tar")
        with tarfile.open(path, "w") as tar:
            data = b"synthetic package marker\n"
            marker = tarfile.TarInfo("candidate/marker.txt")
            marker.size = len(data)
            tar.addfile(marker, io.BytesIO(data))
            for relative, target in helper.NEGATIVE_LINKS.items():
                link = tarfile.TarInfo("candidate/" + relative)
                link.type = tarfile.SYMTYPE
                link.linkname = target
                tar.addfile(link)
            if extra is not None:
                tar.addfile(extra)
        return path

    unpacked = helper.extract_bundle(archive("valid", None), scratch / "valid")
    for relative, target in helper.NEGATIVE_LINKS.items():
        assert os.readlink(unpacked / relative) == target
    invalid = []
    for name, kind, target in [("candidate/unexpected", tarfile.SYMTYPE, "/etc/passwd"),
                               ("candidate/hardlink", tarfile.LNKTYPE, "candidate/marker.txt"),
                               ("candidate/../outside", tarfile.REGTYPE, ""),
                               ("candidate/marker.txt", tarfile.REGTYPE, "")]:
        item = tarfile.TarInfo(name)
        item.type = kind
        item.linkname = target
        invalid.append(item)
    for number, item in enumerate(invalid):
        try:
            helper.extract_bundle(archive("invalid-" + str(number), item), scratch / ("bad-" + str(number)))
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe bundle entry accepted: " + item.name)


def main():
    original = prior_bytes.baseline_archive()
    previous_root = prior_bytes.ROOT
    with tempfile.TemporaryDirectory(prefix="yuho-release-baseline-") as directory:
        root = Path(directory)
        archive = root / "reproducibility/prior-kernel.tar"
        archive.parent.mkdir()
        prior_bytes.ROOT = root
        try:
            archive.write_bytes(original)
            assert prior_bytes.baseline_archive() == original
            for changed in [b"", original + b"\n", b"unexpected" + original,
                            bytes([original[0] ^ 1]) + original[1:]]:
                archive.write_bytes(changed)
                try:
                    prior_bytes.baseline_archive()
                except SystemExit as error:
                    assert "SHA-256 mismatch" in str(error), error
                else:
                    raise AssertionError("substituted historical kernel source accepted")
        finally:
            prior_bytes.ROOT = previous_root
        extraction_checks(previous_root, root)
    print("release distribution: pinned source and two original symlinks preserved; four source substitutions and four unsafe extraction cases rejected")


if __name__ == "__main__":
    main()
