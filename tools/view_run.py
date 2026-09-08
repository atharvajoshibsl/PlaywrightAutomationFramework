"""Rebuild and open an archived Allure run.

    py tools/view_run.py        # list archives
    py tools/view_run.py 7      # rebuild run 7
"""

import shutil
import subprocess
import sys
import tempfile
import webbrowser
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "reports" / "runs"
REBUILT = ROOT / "reports" / "rebuilt"


def archives():
    return sorted(RUNS.glob("run-*.zip"))


def show_list():
    found = archives()
    if not found:
        print(f"No archived runs in {RUNS}. Run the suite first.")
        return
    print(f"{len(found)} archived run(s) in {RUNS}:\n")
    for path in found:
        size = path.stat().st_size / 1024
        print(f"  {path.stem}  ({size:.0f} KB)")
    print("\nRebuild one with: py tools/view_run.py <run number>")


def find(number):
    """Matches on the run number, so the timestamp need not be typed."""
    prefix = f"run-{int(number):03d}_"
    for path in archives():
        if path.name.startswith(prefix):
            return path
    return None


def rebuild(archive):
    allure = shutil.which("allure")
    if not allure:
        print("allure is not on PATH, so the report cannot be rebuilt.")
        return None

    REBUILT.mkdir(parents=True, exist_ok=True)
    report = REBUILT / f"{archive.stem}.html"

    with tempfile.TemporaryDirectory() as work:
        results = Path(work) / "results"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(results)

        staging = Path(work) / "report"
        subprocess.run([allure, "generate", str(results),
                        "-o", str(staging), "--clean", "--single-file"],
                       check=True, capture_output=True)
        shutil.copyfile(staging / "index.html", report)

    return report


def main():
    if len(sys.argv) < 2:
        show_list()
        return 0

    archive = find(sys.argv[1])
    if not archive:
        print(f"No archive for run {sys.argv[1]}.\n")
        show_list()
        return 1

    report = rebuild(archive)
    if not report:
        return 1

    print(f"Rebuilt {archive.stem} -> {report}")
    webbrowser.open(report.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
