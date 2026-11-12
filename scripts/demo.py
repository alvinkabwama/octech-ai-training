"""Two-minute mini-EDRMS demo: upload, OCR, file and route three samples, then show the audit.

Start the server first (``make run``), then: ``python scripts/demo.py``
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT / "mini_edrms" / "samples"
DEMO_SAMPLES = ("finance_01", "hr_01", "legal_01")
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def _labels() -> dict[str, dict[str, str]]:
    with (SAMPLES_DIR / "labels.csv").open(newline="", encoding="utf-8") as handle:
        return {row["file"]: row for row in csv.DictReader(handle)}


def _check(response: httpx.Response) -> dict[str, Any]:
    response.raise_for_status()
    body: dict[str, Any] = response.json()
    return body


def process_sample(client: httpx.Client, stem: str, label: dict[str, str]) -> None:
    """Upload one sample PNG, OCR it, file it and route it, printing each step."""
    png = SAMPLES_DIR / f"{stem}.png"
    doc = _check(
        client.post("/documents", files={"file": (png.name, png.read_bytes(), "image/png")})
    )
    doc_id = doc["id"]
    print(f"[{doc_id}] uploaded {png.name}")

    text = _check(client.post(f"/documents/{doc_id}/ocr"))["text"]
    print(f"[{doc_id}] ocr: {text.splitlines()[0] if text else ''!r}...")

    reason = "Demo: expected label from labels.csv"
    _check(
        client.put(
            f"/documents/{doc_id}/category",
            json={"category": label["category"], "reason": reason},
        )
    )
    print(f"[{doc_id}] filed under {label['category']}")

    _check(
        client.post(
            f"/documents/{doc_id}/route",
            json={"department": label["department"], "reason": reason},
        )
    )
    print(f"[{doc_id}] routed to {label['department']}")


def run(client: httpx.Client) -> list[dict[str, Any]]:
    """Run the demo against ``client`` and return the audit rows it printed."""
    labels = _labels()
    for stem in DEMO_SAMPLES:
        process_sample(client, stem, labels[stem])

    response = client.get("/audit")
    response.raise_for_status()
    rows: list[dict[str, Any]] = response.json()
    print("\nAudit log (newest first):")
    for row in rows:
        print(
            f"  {row['ts'][:19]}  doc={row['doc_id']}  {row['action']:<6} {row['actor']:<5} "
            f"{row['detail']}"
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args(argv)

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        try:
            client.get("/health").raise_for_status()
        except httpx.HTTPError as exc:
            print(
                f"Cannot reach the mini-EDRMS at {args.base_url} ({exc}).\n"
                "Start it first with `make run`.",
                file=sys.stderr,
            )
            return 1
        run(client)
    return 0


if __name__ == "__main__":
    sys.exit(main())
