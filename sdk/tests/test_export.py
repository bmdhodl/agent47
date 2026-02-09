"""Tests for export module: load_trace, export_json, export_csv, export_jsonl."""
import csv
import json
import os
import tempfile
import unittest

from agentguard.export import export_csv, export_json, export_jsonl, load_trace


class TestLoadTrace(unittest.TestCase):
    def _write_jsonl(self, lines):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for line in lines:
            f.write(line + "\n")
        f.close()
        return f.name

    def test_load_valid_events(self):
        path = self._write_jsonl([
            '{"kind": "span", "name": "test"}',
            '{"kind": "event", "name": "step"}',
        ])
        try:
            events = load_trace(path)
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["kind"], "span")
        finally:
            os.unlink(path)

    def test_skip_malformed_lines(self):
        path = self._write_jsonl([
            '{"kind": "span"}',
            'this is not json',
            '{"kind": "event"}',
        ])
        try:
            events = load_trace(path)
            self.assertEqual(len(events), 2)
        finally:
            os.unlink(path)

    def test_skip_empty_lines(self):
        path = self._write_jsonl([
            '{"kind": "span"}',
            '',
            '   ',
            '{"kind": "event"}',
        ])
        try:
            events = load_trace(path)
            self.assertEqual(len(events), 2)
        finally:
            os.unlink(path)

    def test_empty_file(self):
        path = self._write_jsonl([])
        try:
            events = load_trace(path)
            self.assertEqual(events, [])
        finally:
            os.unlink(path)


class TestExportJson(unittest.TestCase):
    def test_export_json(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.write('{"kind": "span", "name": "test"}\n')
        input_f.write('{"kind": "event", "name": "step"}\n')
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        output_f.close()

        try:
            count = export_json(input_f.name, output_f.name)
            self.assertEqual(count, 2)

            with open(output_f.name, "r") as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)

    def test_export_json_empty(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        output_f.close()

        try:
            count = export_json(input_f.name, output_f.name)
            self.assertEqual(count, 0)

            with open(output_f.name, "r") as f:
                data = json.load(f)
            self.assertEqual(data, [])
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)


class TestExportCsv(unittest.TestCase):
    def test_export_csv(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.write(json.dumps({"service": "test", "kind": "span", "phase": "start", "name": "run"}) + "\n")
        input_f.write(json.dumps({"service": "test", "kind": "event", "phase": "emit", "name": "step"}) + "\n")
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        output_f.close()

        try:
            count = export_csv(input_f.name, output_f.name)
            self.assertEqual(count, 2)

            with open(output_f.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["service"], "test")
            self.assertEqual(rows[0]["kind"], "span")
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)

    def test_export_csv_custom_columns(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.write(json.dumps({"service": "test", "kind": "span", "name": "run"}) + "\n")
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        output_f.close()

        try:
            count = export_csv(input_f.name, output_f.name, columns=["service", "name"])
            self.assertEqual(count, 1)

            with open(output_f.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(list(rows[0].keys()), ["service", "name"])
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)

    def test_export_csv_empty(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        output_f.close()

        try:
            count = export_csv(input_f.name, output_f.name)
            self.assertEqual(count, 0)
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)

    def test_export_csv_error_flattened(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.write(json.dumps({
            "service": "test", "kind": "span", "phase": "end",
            "name": "run", "error": {"type": "RuntimeError", "message": "boom"},
        }) + "\n")
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        output_f.close()

        try:
            export_csv(input_f.name, output_f.name)
            with open(output_f.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            # Error should be JSON string, not dict
            error_val = rows[0]["error"]
            parsed = json.loads(error_val)
            self.assertEqual(parsed["type"], "RuntimeError")
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)


class TestExportJsonl(unittest.TestCase):
    def test_export_jsonl_normalizes(self):
        input_f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        input_f.write('{"kind":"span","name":"test"}\n')
        input_f.write('this is not json\n')
        input_f.write('{"kind":"event","name":"step"}\n')
        input_f.close()

        output_f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        output_f.close()

        try:
            count = export_jsonl(input_f.name, output_f.name)
            self.assertEqual(count, 2)  # Malformed line skipped

            with open(output_f.name, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(len(lines), 2)
            for line in lines:
                json.loads(line)  # All valid JSON
        finally:
            os.unlink(input_f.name)
            os.unlink(output_f.name)


if __name__ == "__main__":
    unittest.main()
