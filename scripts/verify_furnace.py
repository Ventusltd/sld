"""Fail closed when a furnace receipt does not bind the exact published inputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from fetch_sources import check_offline


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root, evidence_dir=None):
    root = Path(root)
    check_offline(json.loads((root / 'sources.yaml').read_text(encoding='utf-8')), root / 'data')
    evidence_dir = Path(evidence_dir) if evidence_dir else root / 'data/furnace'
    receipt = json.loads((evidence_dir / 'photon-evidence.json').read_text(encoding='utf-8'))
    photon_path = evidence_dir / 'photon-library.json'
    photon = json.loads(photon_path.read_text(encoding='utf-8'))
    library = json.loads((root / 'data/library.json').read_text(encoding='utf-8'))
    require(receipt.get('accepted') is True, 'Furnace has not accepted this candidate')
    for key, path in [('library_sha256', root / 'data/library.json'),
                      ('source_lock_sha256', root / 'data/source-lock.json'),
                      ('script_sha256', root / 'scripts/furnace.py'),
                      ('photon_library_sha256', photon_path)]:
        require(receipt.get(key) == digest(path), f'Stale or altered {key}')
    require(photon.get('library_sha256') == receipt['library_sha256'], 'Photon library binding differs')
    require(photon.get('production_enabled') is False, 'Photon must not claim production approval')
    eligible = []
    for item in library['components']:
        w, h = item.get('size', {}).get('width', 0), item.get('size', {}).get('height', 0)
        if all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in [w, h]):
            eligible.append(dict(id=item['id'], width=float(w), height=float(h)))
    require(bool(eligible) and len({c['id'] for c in eligible}) == len(eligible), 'Invalid component IDs')
    require(photon.get('components') == eligible, 'Photon component inputs differ')
    n = len(eligible)
    require(receipt.get('component_count') == n, 'Component count differs')
    require(receipt.get('excluded_component_count') == len(library['components']) - n, 'Excluded count differs')
    grid = receipt.get('grid')
    require(type(grid) is int and 2 <= grid <= 2048, 'Invalid grid')
    require(receipt.get('pitch') == .5, 'Invalid grid pitch')
    total = n * n * grid * grid
    require(receipt.get('cpu_reference_cases') == min(total, 8192), 'Incomplete CPU reference')
    require(receipt.get('threshold_fixtures') == 9, 'Missing threshold fixtures')
    require(receipt.get('injected_error_detected') is True, 'Missing injected-error detection')
    require(receipt.get('channels') == ['raw CUDA interval intersection', 'CuPy centre-distance separation'], 'Missing independent channels')
    rows = receipt.get('iterations')
    require(isinstance(rows, list) and bool(rows), 'Missing iterations')
    gaps = []
    for row in rows:
        gap = row.get('gap')
        require(type(gap) in (float, int) and math.isfinite(gap) and 0 <= gap <= 100, 'Invalid gap')
        gaps.append(gap)
        require(row.get('unique_cases') == total and row.get('mismatches') == 0, 'Incomplete or mismatched cases')
        counts = [row.get(k) for k in ['separated', 'touching', 'overlapping']]
        require(all(type(v) is int and v >= 0 for v in counts), 'Invalid classification counts')
        require(sum(counts) == total, 'Classification count sum differs')
    require(len(set(gaps)) == len(gaps), 'Duplicate gap domains inflate unique cases')
    require(receipt.get('unique_cases') == total * len(rows), 'Unique case total differs')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args()
    receipt = verify(args.root, args.evidence_dir)
    print(f"Accepted exact furnace inputs: {receipt['unique_cases']:,} unique cases")
