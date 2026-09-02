"""Turns a finished run into one HTML report plus a small archived record.

Allure's model: each run writes fresh results, and a `history` folder carried
over from the previous report is what produces the trend chart and each test's
record of earlier runs. Since --clean-alluredir wipes the results directory
every run, that history has to be stashed somewhere it survives - which is all
allure-history/ is for.

A single-file report embeds everything, history included, but emits no history
folder of its own. So a run generates twice: once normally, purely to harvest
the history folder, and once as a single file for you to actually open.

Only the newest report is kept as HTML. What gets archived per run is the raw
results instead, because a single-file report is around 3 MB of which 1.9 MB
is a byte-identical copy of Allure's viewer and only ~20 KB is the run's own
data. Zipped results are roughly a tenth of the size and lose nothing: any
archived run can be rendered again with tools/view_run.py.
"""

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

REPORT_NAME = "AItomationKart"


def write_environment(results_dir, values):
    """Fills the Environment panel, so a report says what it ran against."""
    results_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in values.items()]
    (results_dir / "environment.properties").write_text(
        "\n".join(lines), encoding="utf-8")


def write_executor(results_dir, counter_file):
    """Numbers and names this run, so the trend has a label per execution.

    No reportUrl here on purpose. Allure would render the History rows as
    links to it, but it treats the value as a folder and appends
    "/#testresult/<uid>" - which cannot address a test inside a single-file
    archive. It produced links that led nowhere, so it is left out.
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
    """A name that sorts chronologically and survives Windows.

    Zero-padded so run-010 does not sort before run-9, and colons are out
    because Windows will not have them in a filename.
    """
    return f"run-{order:03d}_{moment:%Y-%m-%d_%H-%M-%S}"


def archive_results(results_dir, runs_dir, order, moment):
    """Zips this run's raw results so it can be re-rendered later."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    base = runs_dir / run_stem(order, moment)
    # make_archive appends its own .zip, hence base without a suffix.
    return Path(shutil.make_archive(str(base), "zip", root_dir=results_dir))


def summarise(runs_dir):
    """How many runs are archived and what they weigh, in MB."""
    files = list(runs_dir.glob("run-*.zip"))
    total = sum(path.stat().st_size for path in files)
    return len(files), total / (1024 * 1024)


def build(results_dir, report_dir, history_dir, single_file):
    """Generates the report. Returns the HTML path, or None if it could not.

    Never raises: a reporting problem should not turn a green run red, so
    anything that goes wrong is printed and the raw results are left in place
    to render by hand.
    """
    allure = shutil.which("allure")
    if not allure:
        print(f"\n[report] allure is not on PATH, so no HTML was built.\n"
              f"[report] Raw results are in {results_dir}")
        return None

    # Feed previous runs back in before generating, or every report thinks
    # this was the first one.
    if history_dir.exists():
        shutil.copytree(history_dir, results_dir / "history",
                        dirs_exist_ok=True)

    try:
        _generate(allure, results_dir, report_dir)

        # Harvest the history this run produced for the next one to use.
        produced = report_dir / "history"
        if produced.exists():
            shutil.copytree(produced, history_dir, dirs_exist_ok=True)

        # Single-file mode writes index.html into whatever directory it is
        # given, so it goes somewhere temporary and gets renamed.
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
