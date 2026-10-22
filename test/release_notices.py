"""Reject omitted acknowledgements/evidence and missing or substituted notices."""

import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("notices", ROOT / "scripts/verify_release_notices.py")
notices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notices)


def main():
    files = {p: (ROOT / p).read_bytes() for p in notices.REQUIRED}
    assert not notices.check_notices(files)
    for phrase in [b"copyright of the Singapore Government", b"permission of AGC",
                   b"https://sso.agc.gov.sg/", b"responsible for ensuring the accuracy",
                   b"not associated or affiliated", b"do not endorse",
                   b"acquisition and accuracy review\nremain outstanding"]:
        assert phrase in files["NOTICE"], phrase
        altered = {**files, "NOTICE": files["NOTICE"].replace(phrase, b"REMOVED")}
        assert notices.check_notices(altered), phrase
    owner = "release/owner-apache-authorisation.json"
    altered = json.loads(files[owner])
    altered["answer"] = "Unapproved licence"
    assert notices.check_notices({**files, owner: json.dumps(altered).encode()})
    altered["answer"] = notices.ANSWER
    altered["approval_timestamp"] = "invented"
    assert notices.check_notices({**files, owner: json.dumps(altered).encode()})
    with tempfile.TemporaryDirectory(prefix="yuho-notice-tests-") as tmp:
        for name, contents, valid in [
                ("valid", files, True),
                ("omitted", {k:v for k,v in files.items() if k != "NOTICE"}, False),
                ("substituted", {**files, "LICENSE": b"wrong"}, False)]:
            archive = Path(tmp) / (name + ".tar.gz")
            with tarfile.open(archive, "w:gz") as tar:
                for path, data in contents.items():
                    info = tarfile.TarInfo("package/" + path)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            assert (not notices.check_archive(archive, files)) == valid
    print("Release notices: seven acknowledgement omissions, altered approval/date and two archive substitutions rejected")


if __name__ == "__main__":
    main()
