import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_sources import extract_text_zip, verify_lock, safe_name, download, check_offline, digest, decc_licence_evidence
from build_catalogue import build


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as value:
        for name, data in files:
            value.writestr(name, data)
    return stream.getvalue()


class AcquisitionTests(unittest.TestCase):
    def test_decc_evidence_stable_despite_nonce_changes(self):
        source = next(item for item in json.loads((ROOT / "sources.yaml").read_text())["sources"] if item["id"] == "decc")
        pdf = next(item["url"] for item in source["files"] if item["name"].endswith(".pdf"))
        html = f'<h1>{source["title"]}</h1><a href="{pdf}">PDF</a><footer>All content is available under the <a rel="license" href="{source["licence_url"]}">Open Government Licence v3.0</a>, except where otherwise stated <a>Crown copyright</a></footer>'
        expected = decc_licence_evidence(html.encode(), source)
        self.assertEqual(expected, decc_licence_evidence((html + '<script nonce="random">analytics=42</script>').encode(), source))
        self.assertNotIn(b"\r", expected)
        for changed in (html.replace("Licence v3.0", "Licence v2.0"), html.replace(source["licence_url"], "https://example.org/restricted"), html.replace(pdf, "https://example.org/wrong.pdf")):
            with self.assertRaises(ValueError):
                decc_licence_evidence(changed.encode(), source)

    def test_offline_detects_local_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "upstream/s/file.txt"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"original")
            entry = dict(path="upstream/s/file.txt", source_id="s", licence="CC-BY-4.0", url="https://example.org/file", bytes=8, sha256=digest(b"original"))
            (root / "source-lock.json").write_text(json.dumps({"files": [entry]}))
            config = {"sources": [{"id": "s", "licence": "CC-BY-4.0", "files": [{"name": "file.txt", "url": entry["url"]}]}]}
            check_offline(config, root)
            path.write_bytes(b"modified")
            with self.assertRaises(ValueError):
                check_offline(config, root)

    def test_zip_rejects_traversal_and_executables(self):
        for name in ("../escape.dss", "C:/escape.dss", "send_network_dsse/evil.exe"):
            with self.assertRaises(ValueError):
                extract_text_zip(archive([(name, b"hello")]), [name])

    def test_zip_rejects_binary_missing_and_oversize(self):
        name = "send_network_dsse/master.dss"
        for files, limit in (([(name, b"\x00")], 100), ([], 100), ([(name, b"abc")], 2)):
            with self.assertRaises(ValueError):
                extract_text_zip(archive(files), [name], limit)

    def test_zip_preserves_text_without_execution(self):
        name = "send_network_dsse/master.dss"
        data = b"compile an-untrusted-command\n"
        self.assertEqual(extract_text_zip(archive([(name, data)]), [name]), {name: data})

    def test_lock_rejects_changed_hash_url_and_file_set(self):
        item = dict(path="x", sha256="abc", url="https://example.org/x", licence="CC-BY-4.0", source_id="s")
        previous = {"files": [item]}
        for field in ("sha256", "url", "licence", "source_id"):
            changed = dict(item, **{field: "changed"})
            with self.assertRaises(ValueError):
                verify_lock([changed], previous)
        with self.assertRaises(ValueError):
            verify_lock([], previous)

    def test_filename_rejects_paths(self):
        for name in ("../x.svg", "a/b.svg", "a\\b.svg", ".."):
            with self.assertRaises(ValueError):
                safe_name(name)

    def test_download_rejects_oversize_body(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://example.org/file"
        response.headers = {}
        response.read.return_value = b"1234"
        with patch("urllib.request.urlopen", return_value=response), self.assertRaises(ValueError):
            download("https://example.org/file", 3)


@unittest.skipUnless((ROOT / "data/source-lock.json").exists(), "Acquire sources for catalogue integration check")
class CatalogueTests(unittest.TestCase):
    def test_full_library_preserves_geometry_and_is_deterministic(self):
        config = json.loads((ROOT / "sources.yaml").read_text())
        result = build(config, ROOT / "data")
        original = json.loads((ROOT / "data/upstream/powsybl/components.json").read_text())
        by_type = {item["type"]: item for item in result["components"]}
        self.assertEqual(result["counts"], {"components": 35, "svg_files": 37})
        for item in original:
            actual = by_type[item["type"]]
            for key in ("size", "anchorPoints", "transformations"):
                self.assertEqual(item.get(key), actual.get(key))
            self.assertFalse(actual["production_enabled"])
            self.assertEqual(actual["standards_status"], "unverified")
        self.assertEqual(result, build(config, ROOT / "data"))


if __name__ == "__main__":
    unittest.main()
