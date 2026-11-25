"""Export the ordered literal LaTeX payloads from the supplied private Page snapshot."""
import hashlib
import json
import re
from pathlib import Path

def export(root):
    page = json.loads((root / "source_page.json").read_bytes())
    blocks = page["blocks"]
    parts, order = [], []
    for n in range(1, 27):
        heading, block = blocks[3 + 2*(n-1):5 + 2*(n-1)]
        assert heading["markdown"] == f"### LaTeX part {n:02d} of 26"
        match = re.fullmatch(r"```latex\n(.*)\n```", block["markdown"], re.DOTALL)
        assert match is not None
        part = match.group(1)
        parts.append(part)
        order.append({"order": n, "block": block["id"], "page_block_hash": block["hash"],
                      "payload_sha256": hashlib.sha256(part.encode()).hexdigest()})
    assert len(blocks) == 55
    source = "\n".join(parts).encode()
    (root / "CRGC_Whitepaper_v0.6.tex").write_bytes(source)
    inventory = {"page": page["page_id"], "assembly": "Literal fenced payloads joined by one LF.",
                 "bytes": len(source), "physical_lines": len(source.splitlines()),
                 "sha256": hashlib.sha256(source).hexdigest(), "parts": order}
    (root / "source_order.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(inventory["sha256"], inventory["physical_lines"], len(order))

if __name__ == "__main__":
    export(Path(__file__).resolve().parent)
