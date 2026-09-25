"""Build safe, local educational previews from the pinned component catalogue.

Source files are never rewritten. The generated previews are derivatives and retain
PowSyBl's MPL-2.0 attribution. Electrical terminals are not inferred from anchors.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "assets" / "previews"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
ALLOWED = {"svg", "g", "path", "circle", "ellipse", "line", "polyline", "polygon", "rect", "text", "tspan", "title", "desc", "defs", "clipPath"}


def local_file(relative):
    path = (DATA / relative).resolve()
    if not path.is_relative_to(DATA.resolve()):
        raise ValueError("Asset path leaves data directory")
    return path


def safe_svg(path):
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError(f"DTD/entity rejected: {path}")
    root = ET.fromstring(raw)
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in ALLOWED:
            raise ValueError(f"Unsupported SVG element {tag}: {path}")
        for key, value in node.attrib.items():
            attr = key.split("}")[-1].lower()
            if attr.startswith("on") or attr in {"href", "src"} or "url(" in value.lower() or "javascript:" in value.lower():
                raise ValueError(f"Unsafe SVG attribute: {path}")
    return root


def build():
    library = json.loads((DATA / "library.json").read_text(encoding="utf-8"))
    css = local_file(library["assets"]["css"]).read_text(encoding="utf-8")
    if re.search(r"url\s*\(|@import|</style", css, re.I):
        raise ValueError("External/embedded content in upstream CSS")
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for c in library["components"]:
        name = c["type"]
        if not re.fullmatch(r"[A-Z0-9_]+", name):
            raise ValueError("Invalid component type")
        width = float(c.get("size", {}).get("width", 20)) or 20
        height = float(c.get("size", {}).get("height", 20)) or 20
        if not (0 < width < 10000 and 0 < height < 10000):
            raise ValueError("Invalid component dimensions")
        subs = c.get("subComponents", [])
        variants = ["closed", "open"] if any(s.get("name") == "OPEN" for s in subs) else ["closed"]
        for state in variants:
            root = ET.Element(f"{{{NS}}}svg", {"viewBox":f"-12 -12 {width+24:g} {height+24:g}", "width":"160", "height":"100", "role":"img"})
            ET.SubElement(root, f"{{{NS}}}title").text = f"{name}: research preview ({state})"
            ET.SubElement(root, f"{{{NS}}}desc").text = "Derived from PowSyBl ConvergenceLibrary, MPL-2.0. Not engineering approved."
            ET.SubElement(root, f"{{{NS}}}style").text = css
            outer = ET.SubElement(root, f"{{{NS}}}g", {"class":f"{c.get('styleClass','')} sld-{state}"})
            for sub in subs:
                if sub.get("name") in {"OPEN", "CLOSED"} and sub["name"].lower() != state:
                    continue
                # Directional arrow alternatives must not be overlaid.
                if sub.get("name") == "DOWN" and any(s.get("name") == "UP" for s in subs):
                    continue
                source = safe_svg(local_file(sub["asset_path"]))
                group = ET.SubElement(outer, f"{{{NS}}}g", {"class":sub.get("styleClass", "")})
                # Preserve root attributes affecting geometry as well as child transforms.
                for attr in ("transform", "style", "fill", "stroke", "stroke-width"):
                    if attr in source.attrib:
                        group.set(attr, source.attrib[attr])
                for child in source:
                    group.append(copy.deepcopy(child))
            if not subs:
                if name == "BUSBAR_SECTION":
                    ET.SubElement(outer, f"{{{NS}}}line", {"x1":"0", "y1":str(height/2), "x2":str(width), "y2":str(height/2), "stroke":"#172a16", "stroke-width":"3"})
                elif name == "TEE_POINT":
                    ET.SubElement(outer, f"{{{NS}}}path", {"d":f"M0,{height/2} H{width} M{width/2},{height/2} V{height}","stroke":"#172a16","fill":"none"})
                    ET.SubElement(outer, f"{{{NS}}}circle", {"cx":str(width/2), "cy":str(height/2), "r":"2", "fill":"#172a16"})
                else:
                    ET.SubElement(outer, f"{{{NS}}}text", {"x":str(width/2), "y":str(height/2), "text-anchor":"middle", "font-size":"8", "fill":"#172a16"}).text = "? %" if "PERCENTAGE" in name else "? A"
            out = OUT / f"{name}{'-open' if state == 'open' else ''}.svg"
            ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
            count += 1
    print(f"Built {count} local previews for {len(library['components'])} components.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Optional deployment directory beneath repository root")
    args = parser.parse_args()
    build()
    if args.out:
        destination = (ROOT / args.out).resolve()
        if not destination.is_relative_to(ROOT) or destination == ROOT or destination.parts[len(ROOT.parts)] in {"assets", "data", "docs", "scripts", "tests", ".git"}:
            raise ValueError("Output must be a separate directory beneath repository root")
        destination.mkdir(parents=True, exist_ok=True)
        # Explicit allowlist excludes git metadata, scripts, credentials and local runtime files.
        for name in ("index.html", "LICENSE", "README.md"):
            if (ROOT / name).is_file():
                shutil.copy2(ROOT / name, destination / name)
        for name in ("assets", "data", "docs"):
            if (ROOT / name).is_dir():
                shutil.copytree(ROOT / name, destination / name, dirs_exist_ok=True)
        print(f"Packaged static site at {destination}")
