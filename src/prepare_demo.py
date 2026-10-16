"""Unpack the published demo snapshot with integrity and safe-path checks."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    archive = root / "sample-data.zip"
    expected = (root / "sample-data.sha256").read_text(encoding="utf-8").split()[0]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Sample archive checksum mismatch")
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            path = (root / info.filename).resolve()
            allowed = (root / "data/processed").resolve()
            if not path.is_relative_to(allowed) or info.is_dir():
                raise ValueError(f"Unexpected archive member: {info.filename}")
            content = z.read(info)
            if path.exists():
                if path.read_bytes() != content:
                    raise ValueError(f"Existing demo output differs: {path}. Use a fresh extraction folder.")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    print("Demo snapshot ready. Set Power BI DataRoot to:", root / "data/processed")


if __name__ == "__main__":
    prepare()
