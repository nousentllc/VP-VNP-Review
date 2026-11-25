"""Rebuild the Edition 11 LuaLaTeX report in isolation, without replacing the release PDF."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


REPORT = Path(__file__).resolve().parents[1] / "report"
MASTER = "VP_VNP_Research_Review"
EPOCH = "1795636800"
DIAGNOSTICS = re.compile(
    r"^(?:!|(?:LaTeX(?: Font)?|Package [\w.-]+|Class [\w.-]+) Warning:|"
    r"Missing character:|Overfull \\[hv]box|warning\s+\(pdf backend\)|"
    r"PDF(?:TeX)? warning|.*destination with the same identifier)",
    re.IGNORECASE | re.MULTILINE,
)


def copy_sources(directory):
    # Bind the exact copied bytes without embedding the absolute checkout path.
    inputs = sorted([*REPORT.glob("*.tex"), REPORT / "nous-black.png"])
    digest = hashlib.sha256()
    for source in inputs:
        data = source.read_bytes()
        (directory / source.name).write_bytes(data)
        digest.update(source.name.encode("utf-8") + b"\x00" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def aux_state(directory):
    return {suffix: path.read_bytes() for suffix in (".aux", ".out", ".toc")
            if (path := directory / (MASTER + suffix)).is_file()}


def build(directory, engine):
    source_digest = copy_sources(directory)
    env = os.environ.copy()
    for variable in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR", "TEXMFCACHE"):
        # Relative paths also work with LuaTeX's restricted filesystem mode.
        location = directory / variable
        location.mkdir()
        env[variable] = "./" + variable
    env.update(SOURCE_DATE_EPOCH=EPOCH, FORCE_SOURCE_DATE="1", TZ="UTC")
    env["PATH"] = str(engine.parent) + os.pathsep + env.get("PATH", "")
    command = [str(engine), "-no-shell-escape", "-interaction=nonstopmode",
               "-halt-on-error", "-file-line-error", MASTER + ".tex"]
    previous = None
    for number in range(1, 6):
        result = subprocess.run(command, cwd=directory, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, errors="replace")
        if result.returncode:
            raise RuntimeError(f"LuaLaTeX failed on pass {number}:\n{result.stdout[-4000:]}")
        state = aux_state(directory)
        if not state:
            raise RuntimeError("LuaLaTeX did not produce the report's auxiliary files.")
        if previous == state:
            log = (directory / (MASTER + ".log")).read_text(errors="replace")
            # The original project uses only a PNG; the optional EPS converter
            # advertises that it is disabled when shell execution is disabled.
            diagnostics = [line for line in log.splitlines() if DIAGNOSTICS.search(line)
                           and line != "Package epstopdf Warning: Shell escape feature is not enabled."]
            if diagnostics:
                raise RuntimeError("Final typesetting diagnostics:\n" + "\n".join(diagnostics))
            pdf = directory / (MASTER + ".pdf")
            pages = re.search(r"Output written on .*?\((\d+) pages?,", log, re.DOTALL)
            if not pdf.is_file() or not pages:
                raise RuntimeError("Missing PDF or page-count confirmation in the final log.")
            return pdf, int(pages[1]), number, source_digest
        previous = state
    raise RuntimeError("Report references or bookmarks failed to stabilize in five passes.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lualatex", default="lualatex", help="LuaLaTeX executable or command name")
    parser.add_argument("--output", type=Path, required=True, help="Destination for the rebuilt PDF")
    args = parser.parse_args()
    executable = shutil.which(args.lualatex)
    if not executable:
        parser.error(f"LuaLaTeX executable unavailable: {args.lualatex}")
    # Preserve the format-selecting executable name even when lualatex is a symlink.
    engine = Path(executable).absolute()
    destination = args.output.expanduser().resolve()
    release = REPORT / (MASTER + ".pdf")
    if destination == release or (destination.exists() and release.exists()
                                  and destination.samefile(release)):
        parser.error("Select an output distinct from the checked-in release PDF.")
    if destination.suffix.lower() != ".pdf":
        parser.error("Select a destination ending in .pdf.")
    with tempfile.TemporaryDirectory(prefix="vpvnp-report-") as scratch:
        pdf, pages, passes, source_digest = build(Path(scratch), engine)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Cross-filesystem safe; the previous destination survives any build or copy failure.
        with tempfile.TemporaryDirectory(dir=destination.parent) as stage:
            staged = Path(stage) / "rebuilt.pdf"
            shutil.copyfile(pdf, staged)
            digest = hashlib.sha256(staged.read_bytes()).hexdigest()
            os.replace(staged, destination)
    version = subprocess.check_output([str(engine), "--version"], text=True).splitlines()[0]
    print(version)
    print(f"Source set SHA-256 {source_digest}")
    print(f"{pages} pages; {passes} LuaLaTeX passes; SOURCE_DATE_EPOCH={EPOCH}")
    print(f"SHA-256 {digest}  {destination}")


if __name__ == "__main__":
    main()
