"""Offline infrastructure regressions: python -m unittest discover -s tools -v."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import common
import setup
import validate


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="Server First tools ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "tools").mkdir()
        self.engine = b"fixture executable\n"
        self.metadata = b'[plugin]\nversion="9.7.1"\n'
        self.gut_files = {"plugin.cfg": self.metadata, "gut_cmdln.gd": b"extends SceneTree\n"}
        gut_tree = self.root / "fixture-gut"
        gut_tree.mkdir()
        for name, content in self.gut_files.items():
            (gut_tree / name).write_bytes(content)
        self.engine_pin = {
            "version": "fixture", "directory": "bin/engine", "executable": "godot",
            "files": {"godot": hashlib.sha256(self.engine).hexdigest()},
            "download_url": "https://invalid.test/godot.zip",
        }
        self.certificate = b"fixture CA bundle"
        self.pins = {
            "godot": self.engine_pin,
            "ca_bundle": {"path": "bin/certs/ca-bundle.crt", "download_url": "https://invalid.test/ca-bundle.crt",
                          "sha256": hashlib.sha256(self.certificate).hexdigest()},
            "gut": {"version": "9.7.1", "directory": "addons/gut", "archive_member": "Gut/addons/gut/",
                    "content_sha256": common.content_hash(gut_tree), "download_url": "https://invalid.test/gut.zip"},
        }
        self.archives = {}
        for name, files in (("godot", {"godot": self.engine}),
                            ("gut", {"Gut/addons/gut/" + key: value for key, value in self.gut_files.items()})):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as bundle:
                for member, content in files.items():
                    bundle.writestr(member, content)
            data = stream.getvalue()
            self.archives[name] = data
            pin = self.engine_pin if name == "godot" else self.pins[name]
            pin["archive_sha256"] = hashlib.sha256(data).hexdigest()
        self.write_pins()

    def write_pins(self):
        (self.root / "tools/versions.json").write_text(json.dumps(self.pins), encoding="utf-8")

    def cache_archives(self):
        cache = self.root / "bin/cache"
        cache.mkdir(parents=True, exist_ok=True)
        for name, data in self.archives.items():
            pin = self.engine_pin if name == "godot" else self.pins[name]
            (cache / f"{name}-{pin['archive_sha256']}.zip").write_bytes(data)
        certificate = self.root / self.pins["ca_bundle"]["path"]
        certificate.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_bytes(self.certificate)

    def install(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network must not be used")):
            setup.install(self.root)

    def test_clean_download_and_offline_repeat_with_no_cache(self):
        def download(request, timeout):
            if request.full_url.endswith(".crt"):
                return io.BytesIO(self.certificate)
            name = "godot" if "godot" in request.full_url else "gut"
            return io.BytesIO(self.archives[name])
        with patch("urllib.request.urlopen", side_effect=download) as request:
            setup.install(self.root)
        self.assertEqual(request.call_count, 3)
        for path in (self.root / "bin/cache").iterdir():
            path.unlink()
        self.install()
        self.assertEqual((self.root / "bin/engine/godot").read_bytes(), self.engine)
        self.assertEqual(len(list((self.root / "addons/gut").iterdir())), 2)

    def test_corrupted_download_is_not_published(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b"corrupt")):
            with self.assertRaisesRegex(RuntimeError, "Checksum mismatch"):
                setup.install(self.root)
        self.assertFalse((self.root / "bin/engine").exists())
        self.assertEqual(list((self.root / "bin/cache").iterdir()), [])

    def test_corrupted_cache_is_rejected(self):
        self.cache_archives()
        next((self.root / "bin/cache").glob("godot-*.zip")).write_bytes(b"corrupt")
        with self.assertRaisesRegex(RuntimeError, "Checksum mismatch"):
            self.install()

    def test_mismatched_existing_dependencies_are_not_overwritten(self):
        self.cache_archives()
        self.install()
        engine = self.root / "bin/engine/godot"
        engine.write_bytes(b"unexpected")
        with self.assertRaisesRegex(RuntimeError, "Godot installation mismatch"):
            self.install()
        self.assertEqual(engine.read_bytes(), b"unexpected")
        engine.write_bytes(self.engine)
        metadata = self.root / "addons/gut/plugin.cfg"
        metadata.write_text('[plugin]\nversion="wrong"\n', encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "GUT version/content mismatch"):
            self.install()
        self.assertIn("wrong", metadata.read_text())

    def test_modified_gut_source_is_rejected_but_generated_sidecars_are_allowed(self):
        self.cache_archives()
        self.install()
        gut = self.root / "addons/gut"
        (gut / "gut_cmdln.gd.uid").write_text("generated", encoding="utf-8")
        self.install()
        (gut / "gut_cmdln.gd").write_text("modified", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "GUT version/content mismatch"):
            self.install()

    def test_interrupted_extraction_can_be_retried(self):
        self.cache_archives()
        original = setup.extract_gut
        def interrupt(source, destination, prefix):
            (destination / "partial.gd").write_text("partial", encoding="utf-8")
            raise KeyboardInterrupt()
        with patch.object(setup, "extract_gut", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.install()
        self.assertFalse((self.root / "addons/gut").exists())
        self.assertFalse(list((self.root / "addons").glob("install-*")))
        with patch.object(setup, "extract_gut", original):
            self.install()

    def test_interrupted_download_is_not_cached(self):
        class Interrupted(io.BytesIO):
            def read(self, *args):
                raise OSError("connection interrupted")
        with patch("urllib.request.urlopen", return_value=Interrupted()):
            with self.assertRaisesRegex(OSError, "connection interrupted"):
                setup.install(self.root)
        self.assertEqual(list((self.root / "bin/cache").iterdir()), [])

    def test_archive_cannot_escape_staging(self):
        source = self.root / "unsafe.zip"
        with zipfile.ZipFile(source, "w") as bundle:
            bundle.writestr("Gut/addons/gut/../outside", "unexpected")
        with self.assertRaisesRegex(RuntimeError, "Unsafe archive member"):
            setup.extract_gut(source, self.root / "stage", "Gut/addons/gut/")
        self.assertFalse((self.root / "outside").exists())

    def test_runtime_environment_does_not_mutate_parent(self):
        before = os.environ.copy()
        environment = common.runtime_environment(self.root / "runtime")
        self.assertEqual(dict(os.environ), before)
        for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
            self.assertTrue(Path(environment[key]).is_dir())
            self.assertTrue(Path(environment[key]).is_relative_to(self.root))

    def test_windows_godot_environment_verifies_certificate(self):
        self.cache_archives()
        environment = common.godot_environment(self.root / "runtime", self.root, self.pins)
        settings = Path(environment["APPDATA"]) / "Godot/editor_settings-fixture.tres"
        self.assertIn("network/tls/editor_tls_certificates", settings.read_text())
        self.assertEqual(environment["GODOT_EDITOR_CUSTOM_FEATURES"], "serverfirst_tools")
        (self.root / self.pins["ca_bundle"]["path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(RuntimeError, "Checksum mismatch"):
            common.godot_environment(self.root / "runtime", self.root, self.pins)

    def test_companion_binary_is_required(self):
        self.cache_archives()
        self.install()
        self.engine_pin["files"]["console"] = hashlib.sha256(b"console").hexdigest()
        self.write_pins()
        with self.assertRaisesRegex(RuntimeError, "Godot installation mismatch"):
            self.install()
        (self.root / "bin/engine/console").write_bytes(b"console")
        self.install()

    def report(self, body=None, tests=2):
        if body is None:
            body = "".join(
                f'<testcase classname="{validate.SMOKE_CLASS}" name="{name}" status="pass" assertions="1"/>'
                for name in sorted(validate.EXPECTED_SMOKE_TESTS)
            )
        path = self.root / "gut.xml"
        path.write_text(f'<testsuites tests="{tests}" failures="0"><testsuite>{body}</testsuite></testsuites>', encoding="utf-8")
        return path

    def test_complete_smoke_report_passes(self):
        self.assertEqual(validate.check_report(self.report()), 2)

    def test_missing_empty_zero_failed_skipped_and_incomplete_reports_fail(self):
        with self.assertRaisesRegex(RuntimeError, "did not create"):
            validate.check_report(self.root / "missing.xml")
        path = self.root / "empty.xml"
        path.touch()
        with self.assertRaisesRegex(RuntimeError, "invalid/empty"):
            validate.check_report(path)
        for body, count in (("", 0), ('<testcase><failure/></testcase>', 1),
                            ('<testcase><skipped/></testcase>', 1),
                            ('<testcase status="pass" assertions="1" name="unrelated"/>', 1)):
            with self.subTest(body=body), self.assertRaises(RuntimeError):
                validate.check_report(self.report(body, count))

    def run_python(self, code, timeout=5):
        return validate.run_process(
            [sys.executable, "-c", code], self.root, "fixture",
            os.environ.copy(), self.root, timeout=timeout,
        )

    def test_process_failures_and_zero_exit_diagnostics_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "exited with 3"):
            self.run_python("raise SystemExit(3)")
        for diagnostic in ("SCRIPT ERROR: parse failed", "ERROR: engine failed", "USER ERROR: failed"):
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(RuntimeError, "engine/script error"):
                self.run_python(f"print({diagnostic!r})")

    def test_timeout_preserves_logs(self):
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            self.run_python("import time; print('started', flush=True); time.sleep(20)", timeout=0.3)
        self.assertIn("started", (self.root / "fixture.stdout.log").read_text())

    def test_unsupported_host_and_python_are_rejected(self):
        with patch("platform.system", return_value="Other"), self.assertRaisesRegex(RuntimeError, "Windows x64"):
            common.check_host()
        with patch("platform.system", return_value="Windows"), patch("platform.machine", return_value="ARM64"):
            with self.assertRaisesRegex(RuntimeError, "Windows x64"):
                common.check_host()
        with patch("sys.version_info", (3, 8)), self.assertRaisesRegex(RuntimeError, "Python 3.10"):
            common.check_host()

if __name__ == "__main__":
    unittest.main()
