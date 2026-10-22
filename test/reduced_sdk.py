"""Exact-boundary regressions using all actual candidate members; never clearance."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import io
import json
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reduced", ROOT / "scripts/reduced_sdk.py")
sdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdk)


def main():
    inventory = sdk.load_inventory()
    contents = sdk.source_files(ROOT, inventory)
    prefix = inventory["package_root"] + "/"
    with tempfile.TemporaryDirectory(prefix="yuho-exact-sdk-") as tmp:
        tmp = Path(tmp)
        def archive(name, change=None, extra=None):
            path = tmp / (name + ".tar.gz")
            with tarfile.open(path, "w:gz") as tar:
                for relative, data in contents.items():
                    key = relative
                    if change is not None:
                        transformed = change(relative, data)
                        if transformed is None:
                            continue
                        key, data = transformed
                    item = tarfile.TarInfo(prefix + key)
                    item.size = len(data)
                    tar.addfile(item, io.BytesIO(data))
                if extra is not None:
                    item, data = extra
                    tar.addfile(item, io.BytesIO(data) if data is not None else None)
            return path
        assert sdk.checked_archive(archive("positive"), inventory) == contents
        cases = []
        for label, path in [("dataset", "library/_index/sso_acts.json"),
                            ("asset", "assets/logo/unlisted.png"), ("root-extra", "unapproved.txt")]:
            item = tarfile.TarInfo(prefix + path);item.size = 1
            cases.append((label, archive(label, extra=(item, b"x"))))
        cases.append(("missing", archive("missing", lambda p,b: None if p=="LICENSE" else (p,b))))
        # Remove one listed member and substitute a dataset: count stays identical.
        cases.append(("same-count", archive("same-count", lambda p,b: ("library/_index/sso_acts.json",b) if p=="CHANGELOG.md" else (p,b))))
        for label, data in [("changed",b"unexpected bytes"),
                            ("statutory-substitution",(ROOT/"library/penal_code/s161_public_servant_taking_gratification_other/illustrations.yh").read_bytes())]:
            cases.append((label, archive(label, lambda p,b: (p,data) if p=="CHANGELOG.md" else (p,b))))
        for number, name in enumerate([prefix+"LICENSE", prefix+"./LICENSE", prefix+"../escape", "/absolute", prefix+"src//ambiguous", prefix+"src\\ambiguous", prefix+"license"]):
            item = tarfile.TarInfo(name);item.size=1
            cases.append(("path-"+str(number), archive("path-"+str(number),extra=(item,b"x"))))
        for label, kind, target in [("symlink",tarfile.SYMTYPE,"/etc/passwd"),
                                     ("hardlink",tarfile.LNKTYPE,prefix+"LICENSE"),
                                     ("fifo",tarfile.FIFOTYPE,"")]:
            item=tarfile.TarInfo(prefix+"unlisted");item.type=kind;item.linkname=target
            cases.append((label,archive(label,extra=(item,None))))
        directory=tarfile.TarInfo(prefix+"research");directory.type=tarfile.DIRTYPE
        cases.append(("empty-unlisted-directory",archive("empty-unlisted-directory",extra=(directory,None))))
        for label, path in cases:
            try: sdk.checked_archive(path, inventory)
            except ValueError: pass
            else: raise AssertionError("unsafe/mismatched archive admitted: "+label)
        # Changing both membership and its manifest is not an implicit approval.
        changed=copy.deepcopy(inventory)
        changed["files"][0]["path"]="unapproved.txt"
        policy=tmp/"changed-inventory.json";policy.write_text(json.dumps(changed))
        try:sdk.load_inventory(policy)
        except ValueError:pass
        else:raise AssertionError("unreviewed inventory update accepted")
        stage=tmp/"stage";sdk.stage(ROOT,stage,inventory)
        (stage/"extra").write_text("unexpected")
        try:sdk.verify_stage(stage,inventory)
        except ValueError:pass
        else:raise AssertionError("stage extra admitted")
        (stage/"extra").unlink()
        (stage/"CHANGELOG.md").write_bytes(b"unreviewed replacement")
        try:sdk.verify_stage(stage,inventory)
        except ValueError:pass
        else:raise AssertionError("included file changed without inventory review")
        # Exercise the pre-staging source-digest guard, not only archive checking.
        source=tmp/"source-input"
        for r in inventory['files']:
            p=source/r['source'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(contents[r['path']])
        (source/"CHANGELOG.md").write_bytes(b"unreviewed source revision")
        try:sdk.source_files(source,inventory)
        except ValueError:pass
        else:raise AssertionError("unreviewed source change admitted")
        first=sdk.build(ROOT,tmp/"cabal-a",inventory)
        second=sdk.build(ROOT,tmp/"cabal-b",inventory)
        assert first.read_bytes()==second.read_bytes(),"Cabal archive generation is not repeatable"
        assert sdk.checked_archive(first,inventory)==contents
        print("Reduced SDK exact boundary:",len(contents),"reviewed members;",len(cases),"negative archives plus manifest/stage drift rejected")


if __name__ == "__main__":main()
