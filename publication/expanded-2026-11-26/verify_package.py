"""Verify the extracted publication ZIP against its complete payload manifest."""

import hashlib
import pathlib
import sys


def main():
    root = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2]
    manifest = root / "PACKAGE_SHA256SUMS"
    checked = set()
    for line in manifest.read_text().splitlines():
        digest, relative = line.split("  ", 1)
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or relative in checked:
            raise ValueError("Unsafe or duplicate manifest path")
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError("Payload digest differs: " + relative)
        checked.add(relative)
    print(f"Verified {len(checked)} payload files against PACKAGE_SHA256SUMS.")
    print("The manifest excludes itself; verify the outer ZIP hash in the repository delivery receipt.")


if __name__ == "__main__":
    main()
