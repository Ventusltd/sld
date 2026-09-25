"""Bounded, pinned acquisition; never executes remote content.

sources.yaml deliberately uses the JSON subset of YAML (stdlib json parser).
First reviewed fetch: python scripts/fetch_sources.py --accept-first-fetch
Subsequent runs verify the existing hash lock and fail on any upstream change.
--output selects a data directory, e.g. an external drive. No dependencies.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in {".", ".."}:
        raise ValueError(f"Unsafe filename: {name!r}")
    return name


def download(url, limit):
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS sources are accepted")
    request = urllib.request.Request(url, headers={"User-Agent": "SLD-library-research/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("Non-HTTPS redirect")
        length = response.headers.get("Content-Length")
        if length and int(length) > limit:
            raise ValueError(f"Source exceeds byte limit: {url}")
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Source exceeds byte limit: {url}")
    return data


def extract_text_zip(data, allowed, limit=1000000):
    """Return exact allowlisted text members, rejecting traversal/symlinks/bombs."""
    expected = set(allowed)
    result = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        seen = set()
        for info in archive.infolist():
            name = info.filename
            path = PurePosixPath(name)
            if name in seen or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError(f"Unsafe or duplicate ZIP member: {name}")
            seen.add(name)
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("ZIP symlink rejected")
            if info.is_dir():
                if name != "send_network_dsse/":
                    raise ValueError("Unexpected ZIP directory")
                continue
            if name not in expected or path.suffix.lower() not in {".dss", ".csv", ".txt"}:
                raise ValueError(f"ZIP member is not allowlisted text: {name}")
            total += info.file_size
            if total > limit:
                raise ValueError("ZIP expanded-size limit exceeded")
            content = archive.read(info)
            content.decode("utf-8-sig")
            if b"\x00" in content:
                raise ValueError("Binary ZIP member rejected")
            result[name] = content
    if set(result) != expected:
        raise ValueError("ZIP is missing expected members")
    return result


def verify_lock(records, previous):
    old = {entry["path"]: entry for entry in previous["files"]}
    new = {entry["path"]: entry for entry in records}
    if set(old) != set(new):
        raise ValueError("Source file set changed; review required")
    for path, entry in new.items():
        for field in ("sha256", "url", "licence", "source_id"):
            if entry[field] != old[path][field]:
                raise ValueError(f"Locked source changed ({field}): {path}")


def check_offline(config, output):
    """Verify locked local bytes and source attribution without making requests."""
    output = Path(output).resolve()
    lock = json.loads((output / "source-lock.json").read_text(encoding="utf-8"))
    sources = {source["id"]: source for source in config["sources"]}
    seen = set()
    for entry in lock["files"]:
        name = entry["path"]
        path = (output / name).resolve()
        if name in seen or not path.is_relative_to(output):
            raise ValueError(f"Unsafe or duplicate locked path: {name}")
        seen.add(name)
        source = sources.get(entry["source_id"])
        if source is None or source["licence"] != entry["licence"]:
            raise ValueError(f"Locked source attribution mismatch: {name}")
        data = path.read_bytes()
        if len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
            raise ValueError(f"Local source integrity failure: {name}")
    for source in config["sources"]:
        for item in source["files"]:
            name = f"upstream/{source['id']}/{item['name']}"
            matching = [entry for entry in lock["files"] if entry["path"] == name]
            if len(matching) != 1 or matching[0]["url"] != item["url"]:
                raise ValueError(f"Missing or changed configured source: {name}")
    return lock


def acquire(config, output, accept_first=False):
    output = Path(output)
    lock_path = output / "source-lock.json"
    previous = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else None
    if previous is None and not accept_first:
        raise ValueError("No hash lock: review sources.yaml then pass --accept-first-fetch")
    payloads, records = {}, []

    def add(source, name, url, data, origin=None):
        relative = f"upstream/{source['id']}/{name}"
        if relative in payloads:
            raise ValueError(f"Duplicate output: {relative}")
        payloads[relative] = data
        entry = {"path": relative, "source_id": source["id"], "url": url,
                 "sha256": digest(data), "bytes": len(data), "licence": source["licence"]}
        if origin:
            entry["archive_member"] = origin
        records.append(entry)

    for source in config["sources"]:
        safe_name(source["id"])
        fetched = {}
        for item in source["files"]:
            name = safe_name(item["name"])
            data = download(item["url"], source["max_bytes"])
            if item.get("md5") and hashlib.md5(data).hexdigest() != item["md5"]:
                raise ValueError(f"Pinned archive MD5 mismatch: {name}")
            if name.endswith(".pdf") and not data.startswith(b"%PDF-"):
                raise ValueError("Expected PDF signature")
            fetched[name] = data
            add(source, name, item["url"], data)
        if source["id"] == "powsybl":
            components = json.loads(fetched["components.json"])
            names = {safe_name(part["fileName"]) for component in components for part in component.get("subComponents", [])}
            if len(components) != source["expected_components"] or len(names) != source["expected_svgs"]:
                raise ValueError("Unexpected PowSyBl component/SVG counts")
            for name in sorted(names):
                if not name.endswith(".svg"):
                    raise ValueError("Unexpected component format")
                url = source["base_url"] + name
                data = download(url, source["max_bytes"])
                if b"<svg" not in data:
                    raise ValueError("Expected SVG content")
                add(source, name, url, data)
        if source["id"] == "send":
            metadata = json.loads(fetched["metadata.json"])
            if metadata.get("doi") != source["revision"] or metadata.get("license", {}).get("name") != "CC BY 4.0":
                raise ValueError("SEND version/licence mismatch")
            for name, data in extract_text_zip(fetched["send_network_dsse.zip"], source["zip_members"]).items():
                add(source, name, source["files"][1]["url"], data, origin=name)
        if source["id"] == "decc":
            if b"open-government-licence/version/3" not in fetched["source-page.txt"]:
                raise ValueError("DECC source page lacks expected OGL evidence")
    records.sort(key=lambda item: item["path"])
    if previous:
        verify_lock(records, previous)
    # No writes before every download, licence and existing lock check succeeds.
    for relative, data in payloads.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    lock = {"schema_version": "1.0", "files": records}
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    return lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    parser.add_argument("--config", type=Path, default=ROOT / "sources.yaml")
    parser.add_argument("--accept-first-fetch", action="store_true")
    parser.add_argument("--check-offline", action="store_true", help="Verify existing locked local bytes without HTTP")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    lock = check_offline(config, args.output) if args.check_offline else acquire(config, args.output, args.accept_first_fetch)
    print(f"Verified {len(lock['files'])} files in {args.output}")


if __name__ == "__main__":
    main()
