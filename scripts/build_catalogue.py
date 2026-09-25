"""Build a deterministic research catalogue from hash-verified local sources."""
import argparse
import copy
import json
from pathlib import Path
from fetch_sources import ROOT, check_offline


def build(config, data_dir):
    data_dir = Path(data_dir)
    lock = check_offline(config, data_dir)
    entries = {entry["path"]: entry for entry in lock["files"]}
    raw = json.loads((data_dir / "upstream/powsybl/components.json").read_text(encoding="utf-8"))
    components = []
    for original in raw:
        component = copy.deepcopy(original)
        component.update(id=original["type"], source_id="powsybl", production_enabled=False,
                         standards_status="unverified", source_ref="upstream/powsybl/components.json")
        for part in component.get("subComponents", []):
            part["asset_path"] = "upstream/powsybl/" + part["fileName"]
            if part["asset_path"] not in entries:
                raise ValueError(f"Unverified component asset: {part['asset_path']}")
        components.append(component)
    powsybl = next(source for source in config["sources"] if source["id"] == "powsybl")
    unique = {part["fileName"] for component in raw for part in component.get("subComponents", [])}
    if len(raw) != powsybl["expected_components"] or len(unique) != powsybl["expected_svgs"]:
        raise ValueError("Catalogue count mismatch")
    sources = []
    for source in config["sources"]:
        item = {key: source[key] for key in ("id", "title", "kind", "revision", "licence", "url")}
        item.update(status="acquired", production_enabled=False, standards_status="unverified",
                    files=[entry for entry in lock["files"] if entry["source_id"] == source["id"]])
        sources.append(item)
    return {"schema_version": "1.0", "production_enabled": False, "standards_status": "unverified",
            "components": sorted(components, key=lambda item: item["id"]), "sources": sources,
            "assets": {"css": "upstream/powsybl/components.css"},
            "counts": {"components": len(raw), "svg_files": len(unique)},
            "networks": [{"id": "send", "source_id": "send", "format": "OpenDSS",
                          "execution_allowed": False, "production_enabled": False,
                          "files": [entry["path"] for entry in lock["files"] if entry.get("archive_member")]}],
            "references": config["references"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--config", type=Path, default=ROOT / "sources.yaml")
    args = parser.parse_args()
    result = build(json.loads(args.config.read_text(encoding="utf-8")), args.data)
    path = args.data / "library.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"Built {path}: {result['counts']}")


if __name__ == "__main__":
    main()
