"""Build Allure HTML report and archive raw results after each run.

History lives in allure-history/ because --clean-alluredir wipes results.
"""

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

REPORT_NAME = "AItomationKart"


def write_environment(results_dir, values):
    """Write environment.properties for the Environment panel."""
    results_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in values.items()]
    (results_dir / "environment.properties").write_text(
        "\n".join(lines), encoding="utf-8")


def write_executor(results_dir, counter_file):
    """Assign run number and write executor.json for trend labels.

    No reportUrl: Allure history links break with single-file reports.
    """
    order = 1
    if counter_file.exists():
        order = int(counter_file.read_text(encoding="utf-8").strip()) + 1
    counter_file.parent.mkdir(parents=True, exist_ok=True)
    counter_file.write_text(str(order), encoding="utf-8")

    moment = datetime.now()
    (results_dir / "executor.json").write_text(json.dumps({
        "name": "Local run",
        "type": "local",
        "buildOrder": order,
        "buildName": f"Run {order} - {moment:%d %b %Y, %H:%M:%S}",
        "reportName": REPORT_NAME,
    }), encoding="utf-8")
    return order, moment


def run_stem(order, moment):
    """Archive filename: zero-padded order, no colons (Windows)."""
    return f"run-{order:03d}_{moment:%Y-%m-%d_%H-%M-%S}"


def archive_results(results_dir, runs_dir, order, moment):
    """Zip this run's raw results for later replay."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    base = runs_dir / run_stem(order, moment)
    # make_archive appends .zip itself.
    return Path(shutil.make_archive(str(base), "zip", root_dir=results_dir))


def summarise(runs_dir):
    """Return archived run count and total size in MB."""
    files = list(runs_dir.glob("run-*.zip"))
    total = sum(path.stat().st_size for path in files)
    return len(files), total / (1024 * 1024)


def build(results_dir, report_dir, history_dir, single_file):
    """Build report; return HTML path or None. Never raises."""
    allure = shutil.which("allure")
    if not allure:
        print(f"\n[report] allure is not on PATH, so no HTML was built.\n"
              f"[report] Raw results are in {results_dir}")
        return None

    # Copy saved history into results before generate.
    if history_dir.exists():
        shutil.copytree(history_dir, results_dir / "history",
                        dirs_exist_ok=True)

    try:
        _generate(allure, results_dir, report_dir)

        # Save history from this run for the next one.
        produced = report_dir / "history"
        if produced.exists():
            shutil.copytree(produced, history_dir, dirs_exist_ok=True)

        # Single-file mode writes to a temp dir; copy index.html out.
        with tempfile.TemporaryDirectory() as staging:
            _generate(allure, results_dir, Path(staging), single=True)
            shutil.copyfile(Path(staging) / "index.html", single_file)
    except (subprocess.CalledProcessError, OSError) as error:
        print(f"\n[report] could not build the HTML report: {error}")
        return None

    return single_file


def _generate(allure, results_dir, output_dir, single=False):
    command = [allure, "generate", str(results_dir),
               "-o", str(output_dir), "--clean"]
    if single:
        command.append("--single-file")
    subprocess.run(command, check=True, capture_output=True)
