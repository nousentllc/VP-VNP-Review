"""Whole-panel secondary replay with separate import allowance and unchanged scoring."""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ["full", "lp_start", "group_start", "permanent"]


def run(output):
    config = json.loads((HERE / "freeze.json").read_text())
    output.mkdir(parents=True, exist_ok=False)
    for j, path in enumerate(sorted((HERE / "inputs").glob("*.json"))):
        for k, hours in enumerate([12, 48]):
            offset = (j + k) % len(ARMS)
            for arm in ARMS[offset:] + ARMS[:offset]:
                destination = output / f"{path.stem}_{hours}_{arm}"
                destination.mkdir()
                command = [sys.executable, str(HERE / "uc_warm.py"), "worker",
                           str(path), str(hours), arm, str(destination),
                           str(config["candidate_share"]), str(config["effort"])]
                with (destination / "console.log").open("w") as stream:
                    child = subprocess.Popen(command, stdout=stream, stderr=stream)
                    launched = time.monotonic()
                    start = None
                    killed = False
                    record = destination / "record.json"
                    while child.poll() is None:
                        if start is None and record.exists():
                            start = json.loads(record.read_text())["start_monotonic"]
                        gate = launched + 180 if start is None else start + 45.25
                        if time.monotonic() > gate:
                            child.kill()
                            child.wait()
                            killed = True
                            break
                        time.sleep(.03)
                log = dict(exit=child.returncode, killed=killed,
                           total_wall_s=time.monotonic()-launched, import_limit_s=180)
                (destination / "supervisor.json").write_text(json.dumps(log))
                print(destination.name, flush=True)


if __name__ == "__main__":
    run(Path(sys.argv[1]))
