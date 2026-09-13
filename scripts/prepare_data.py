from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen


SOURCE_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)
EXPECTED_SHA256 = "0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE"
EXPECTED_BYTES = 3_964_977
EXPECTED_ROWS = 64_000
EXPECTED_HEADER = (
    "recency,history_segment,history,mens,womens,zip_code,newbie,channel,"
    "segment,visit,conversion,spend"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate(path: Path) -> None:
    if path.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError(f"file size mismatch: {path.stat().st_size}")
    actual_hash = sha256(path)
    if actual_hash != EXPECTED_SHA256:
        raise RuntimeError(f"SHA-256 mismatch: {actual_hash}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = handle.readline().rstrip("\r\n")
        rows = sum(1 for _ in handle)
    if header != EXPECTED_HEADER:
        raise RuntimeError("schema header does not match the frozen input")
    if rows != EXPECTED_ROWS:
        raise RuntimeError(f"row count mismatch: {rows}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    destination = root / "data" / "raw" / "hillstrom.csv"
    if destination.exists():
        validate(destination)
        print("Hillstrom data already exists and passed verification.")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        request = Request(SOURCE_URL, headers={"User-Agent": "hillstrom-reproducibility-check"})
        with urlopen(request, timeout=60) as response, tempfile.NamedTemporaryFile(
            prefix="hillstrom-", suffix=".csv", delete=False
        ) as output:
            temporary = Path(output.name)
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        validate(temporary)
        os.replace(temporary, destination)
        destination.chmod(0o444)
        print(f"Data ready: {destination}")
        print(f"SHA-256 verified: {EXPECTED_SHA256}")
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    main()
