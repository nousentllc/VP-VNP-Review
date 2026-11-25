"""Portable directory entry point for replay of the frozen rainflow scoring program."""
import argparse
from pathlib import Path
from revalue import run

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    target=a.out/"results.json"
    if target.exists():raise FileExistsError(target)
    run(a.source.resolve(),target)
