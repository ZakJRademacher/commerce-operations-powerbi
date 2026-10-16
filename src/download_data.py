"""Download the public Kaggle archive without embedding user credentials."""
import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
ROOT = Path(__file__).resolve().parents[1]


def download(destination):
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "olist.zip"
    if not archive.exists():
        pending = destination / "olist.download"
        urllib.request.urlretrieve(URL, pending)
        with zipfile.ZipFile(pending) as z:
            if z.testzip():
                raise ValueError("Archive integrity check failed")
        pending.replace(archive)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if "/" not in item.filename and "\\" not in item.filename and ".." not in item.filename and item.filename.endswith(".csv"):
                target = destination / item.filename
                if not target.exists():
                    target.write_bytes(z.read(item))
    return {"url": URL, "bytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "data/raw")
    args = parser.parse_args()
    print(json.dumps(download(args.destination), indent=2))
