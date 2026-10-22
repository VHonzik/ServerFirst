"""Offline headless import and GUT validation. Does not infer sandbox permissions."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from common import ROOT, entrypoint, godot_environment, godot_path, verify_gut, versions


EXPECTED_SMOKE_TESTS = {"test_headless_runtime", "test_user_data_round_trip"}
SMOKE_CLASS = "test/unit/test_setup_smoke.gd"
ERROR = re.compile(r"^\s*(?:(?:SCRIPT |USER |FATAL )?ERROR|FATAL):", re.MULTILINE)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_process(command: list[str], directory: Path, name: str, environment: dict,
                root: Path, timeout: float = 120) -> str:
    stdout_path = directory / f"{name}.stdout.log"
    stderr_path = directory / f"{name}.stderr.log"
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            command, cwd=root, env=environment, stdout=stdout, stderr=stderr,
        )
        try:
            process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            # Godot is launched directly, without a console launcher child.
            process.kill()
            process.wait()
            if isinstance(error, KeyboardInterrupt):
                raise
            raise RuntimeError(f"{name} timed out after {timeout}s. See {directory}.") from error
    output = stdout_path.read_text(encoding="utf-8", errors="replace")
    errors = stderr_path.read_text(encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError(f"{name} exited with {process.returncode}. See {directory}.")
    plain = ANSI.sub("", output + "\n" + errors)
    diagnostic = ERROR.search(plain)
    if diagnostic:
        raise RuntimeError(f"{name} emitted an engine/script error. See {directory}.")
    return output


def check_report(path: Path) -> int:
    if not path.is_file():
        raise RuntimeError(f"GUT did not create its report: {path}")
    try:
        report = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise RuntimeError(f"GUT produced an invalid/empty report: {path}") from error
    cases = report.findall(".//testcase")
    if not cases or report.findall(".//failure") or report.findall(".//error") or report.findall(".//skipped"):
        raise RuntimeError(f"GUT failed, skipped tests or ran zero tests. See {path}.")
    for element in report.iter():
        for attribute in ("failures", "errors", "skipped"):
            if int(element.get(attribute, "0")):
                raise RuntimeError(f"GUT reported {attribute}. See {path}.")
    if int(report.get("tests", "0")) != len(cases):
        raise RuntimeError(f"GUT report test count is inconsistent. See {path}.")
    for case in cases:
        if case.get("status") != "pass" or int(case.get("assertions", "0")) < 1:
            raise RuntimeError(f"GUT test did not pass with assertions. See {path}.")
    smoke = {case.get("name") for case in cases if case.get("classname") == SMOKE_CLASS}
    if not EXPECTED_SMOKE_TESTS.issubset(smoke):
        raise RuntimeError(f"Expected setup smoke tests did not run. See {path}.")
    return len(cases)


def validate(root: Path = ROOT) -> None:
    pins = versions(root)
    engine = godot_path(root, pins)
    verify_gut(root / pins["gut"]["directory"], pins["gut"])
    report_root = root / "reports/validation"
    report_root.mkdir(parents=True, exist_ok=True)
    # Unique directories guarantee that previous successful reports cannot be reused.
    directory = Path(tempfile.mkdtemp(prefix="run-", dir=report_root))
    print(f"Validation logs: {directory}", flush=True)
    environment = godot_environment(directory / "runtime", root, pins)
    command = [str(engine), "--headless", "--path", str(root)]
    version = run_process(command + ["--version"], directory, "version", environment, root, timeout=15)
    if version.strip() != pins["godot"]["version"]:
        raise RuntimeError(f"Godot version does not match the pin. See {directory}.")
    run_process(command + ["--editor", "--import"], directory, "import", environment, root)
    report = directory / "gut.xml"
    run_process(command + [
        "--script", "res://addons/gut/gut_cmdln.gd", "-gconfig=",
        "-gdir=res://test/unit", "-ginclude_subdirs", "-gexit", "-gdisable_colors",
        "-gfailure_error_types=engine,gut,push_error", f"-gjunit_xml_file={report}",
    ], directory, "gut", environment, root)
    count = check_report(report)
    print(f"PASS: pinned Godot version, headless import, {count} GUT tests. Logs: {directory}")


if __name__ == "__main__":
    entrypoint(validate)
