"""Recreate both November 24 inputs from the captured native page responses."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read_source():
    with gzip.open(HERE / "source_pages.json.gz", "rt") as stream:
        pages = json.load(stream)
    master = pages["manuscript"]
    blocks = master["blocks"]
    order = json.loads((ROOT / "manuscript/source_order.json").read_text())
    parts = []
    for index, expected in enumerate(order["blocks"]):
        heading, data = blocks[4 + 2 * index:6 + 2 * index]
        assert heading["markdown"] == f"## Source block {index + 1:02d} / 17"
        assert data["id"] == expected["id"] and data["hash"] == expected["page_block_hash"]
        part = re.fullmatch(r"\x60{3}latex\n([\s\S]*)\n\x60{3}", data["markdown"])[1]
        assert hashlib.sha256(part.encode()).hexdigest() == expected["source_sha256"]
        parts.append(part)
    assert len(parts) == 17
    return {"CRGC_Whitepaper_v0.4.tex": "\n".join(parts).encode(),
            "W05_Research_Protocol.md": ("\n\n".join(b["markdown"] for b in pages["protocol"]["blocks"]) + "\n").encode()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, help="optional new output directory")
    args = parser.parse_args()
    documents = read_source()
    if args.out:
        args.out.mkdir(parents=True, exist_ok=False)
    for name, data in documents.items():
        source = ROOT / "manuscript" / name if name.endswith(".tex") else HERE / name
        if source.read_bytes() != data:
            raise ValueError(f"Export discrepancy for {name}")
        if args.out:
            (args.out / name).write_bytes(data)
        print(hashlib.sha256(data).hexdigest(), name)


if __name__ == "__main__":
    main()
