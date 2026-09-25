"""Bounded GPU layout furnace: independent CUDA and CuPy rectangle tests.

Reuses the paired-kernel/reference pattern from Ventusltd/worlds-/src/furnace.py.
This checks declared symbol bounding boxes, not electrical safety or SVG ink.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

KERNEL = r'''
extern "C" __global__ void boxes(const double* w, const double* h,
 unsigned long long start, unsigned long long count, int symbols, int grid,
 double gap, unsigned char* out) {
 unsigned long long k = (unsigned long long)blockDim.x*blockIdx.x+threadIdx.x;
 if(k>=count)return;
 unsigned long long id=start+k, plane=(unsigned long long)grid*grid;
 int a=(id/plane)/symbols, b=(id/plane)%symbols;
 double x=((long long)(id%grid)-grid/2)*0.5;
 double y=((long long)((id/grid)%grid)-grid/2)*0.5;
 double left=x-w[b]/2-gap, right=x+w[b]/2+gap;
 double bottom=y-h[b]/2-gap, top=y+h[b]/2+gap;
 bool strict=(left<w[a]/2 && right>-w[a]/2 && bottom<h[a]/2 && top>-h[a]/2);
 bool inclusive=(left<=w[a]/2 && right>=-w[a]/2 && bottom<=h[a]/2 && top>=-h[a]/2);
 out[k]=strict?2:(inclusive?1:0);
}
'''

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def reference(xp, ids, w, h, n, grid, gap):
    pair = ids // (grid * grid)
    a, b = pair // n, pair % n
    x = (ids % grid - grid // 2) * .5
    y = (ids // grid % grid - grid // 2) * .5
    dx = xp.abs(x) - (w[a] + w[b]) / 2 - gap
    dy = xp.abs(y) - (h[a] + h[b]) / 2 - gap
    return xp.where((dx < 0) & (dy < 0), 2,
                    xp.where((dx <= 0) & (dy <= 0), 1, 0)).astype(xp.uint8)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=Path('data/library.json'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--grid', type=int, default=1024)
    parser.add_argument('--batch', type=int, default=4_194_304)
    parser.add_argument('--gaps', type=float, nargs='+', default=[0, 2, 4])
    args = parser.parse_args()
    if not 2 <= args.grid <= 2048 or not 1 <= args.batch <= 16_777_216:
        parser.error('grid must be 2..2048; batch 1..16777216')
    if len(set(args.gaps)) != len(args.gaps) or any(not math.isfinite(g) or g < 0 or g > 100 for g in args.gaps):
        parser.error('gaps must be distinct finite values in 0..100')
    args.out.mkdir(parents=True, exist_ok=True)
    # Invalidate old acceptance before any imports or checks that may fail.
    receipt_path = args.out / 'photon-evidence.json'
    receipt_path.write_text(json.dumps({'accepted': False, 'status': 'running'}))
    started = time.perf_counter()
    import numpy as np
    import cupy as cp
    library = json.loads(args.library.read_text(encoding='utf-8'))
    components = library['components']
    eligible = []
    for item in components:
        size = item.get('size', {})
        w, h = size.get('width', 0), size.get('height', 0)
        if isinstance(w, (int, float)) and isinstance(h, (int, float)) and np.isfinite(w+h) and w > 0 and h > 0:
            eligible.append((item['id'], float(w), float(h)))
    if not eligible:
        raise ValueError('No finite positive declared component sizes')
    width = np.array([e[1] for e in eligible], dtype=np.float64)
    height = np.array([e[2] for e in eligible], dtype=np.float64)
    w, h = cp.asarray(width), cp.asarray(height)
    n = len(eligible)
    total = n * n * args.grid * args.grid
    kernel = cp.RawKernel(KERNEL, 'boxes')
    def electron(start, count, gap):
        out = cp.empty(count, dtype=cp.uint8)
        kernel(((count+255)//256,), (256,), (w, h, np.uint64(start), np.uint64(count), np.int32(n), np.int32(args.grid), np.float64(gap), out))
        return out
    # Separate hand-calculated threshold fixtures for inclusive/strict semantics.
    fixtures = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8], dtype=np.int64)
    # Two identical unit boxes, y=0, x from -2 to +2 in half-unit steps.
    fixture_ids = fixtures + 4*9
    expected = np.array([0,0,1,2,2,2,1,0,0], dtype=np.uint8)
    assert np.array_equal(reference(np, fixture_ids, np.array([1.]), np.array([1.]), 1, 9, 0), expected)
    sample_ids = np.unique(np.linspace(0, total-1, min(total, 8192), dtype=np.int64))
    cpu = reference(np, sample_ids, width, height, n, args.grid, args.gaps[0])
    assert np.array_equal(cp.asnumpy(reference(cp, cp.asarray(sample_ids), w, h, n, args.grid, args.gaps[0])), cpu)
    warm = electron(0, min(total, args.batch), args.gaps[0])
    warm_ref = reference(cp, cp.arange(len(warm), dtype=cp.int64), w, h, n, args.grid, args.gaps[0])
    assert int(cp.count_nonzero(warm != warm_ref).get()) == 0
    broken = warm.copy(); broken[0] = (broken[0] + 1) % 3
    assert int(cp.count_nonzero(broken != warm_ref).get()) == 1
    cp.cuda.Stream.null.synchronize()
    setup_seconds = time.perf_counter() - started
    rows = []
    for gap in args.gaps:
        begin = time.perf_counter()
        last_progress = begin
        counts = np.zeros(3, dtype=np.int64)
        mismatches = 0
        for start in range(0, total, args.batch):
            count = min(args.batch, total-start)
            ids = cp.arange(start, start+count, dtype=cp.int64)
            actual = electron(start, count, gap)
            other = reference(cp, ids, w, h, n, args.grid, gap)
            summary = cp.stack([cp.count_nonzero(actual != other)] + [cp.count_nonzero(actual == i) for i in range(3)])
            values = cp.asnumpy(summary)
            mismatches += int(values[0]); counts += values[1:]
            if mismatches:
                raise AssertionError(f'Channels disagree at batch {start}; refusing photon acceptance')
            if time.perf_counter() - last_progress >= 5:
                print(json.dumps({'gap':gap,'checked':start+count,'total':total,'mismatches':mismatches}),flush=True)
                last_progress = time.perf_counter()
        cp.cuda.Stream.null.synchronize()
        row = dict(gap=gap, unique_cases=total, mismatches=mismatches,
                   separated=int(counts[0]), touching=int(counts[1]), overlapping=int(counts[2]),
                   seconds=time.perf_counter()-begin)
        assert sum(counts) == total
        rows.append(row)
        print(json.dumps(row), flush=True)
    photon = dict(schema_version=1, kind='declared-bounding-box-layout-input',
                  library_sha256=digest(args.library), components=[dict(id=i,width=w,height=h) for i,w,h in eligible],
                  statuses={'0':'separated','1':'touching','2':'overlapping'},
                  production_enabled=False,
                  scope='Declared bounding boxes only; no electrical approval, routing, SVG ink or label collision certification.')
    photon_path = args.out / 'photon-library.json'
    photon_path.write_text(json.dumps(photon,indent=2)+'\n',encoding='utf-8', newline='\n')
    receipt = dict(accepted=True, scope=photon['scope'], device=cp.cuda.runtime.getDeviceProperties(0)['name'].decode(),
                   cupy_version=cp.__version__, cuda_runtime=cp.cuda.runtime.runtimeGetVersion(),
                   library_sha256=digest(args.library), script_sha256=digest(Path(__file__)),
                   photon_library_sha256=digest(photon_path), source_lock_sha256=digest(args.library.parent/'source-lock.json'),
                   channels=['raw CUDA interval intersection','CuPy centre-distance separation'],
                   cpu_reference_cases=len(sample_ids), threshold_fixtures=9, injected_error_detected=True,
                   grid=args.grid, pitch=.5, component_count=n, excluded_component_count=len(components)-n,
                   unique_cases=total*len(rows), iterations=rows, setup_seconds=setup_seconds,
                   whole_seconds=time.perf_counter()-started)
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8', newline='\n')
    print(json.dumps({'accepted':True,'unique_cases':receipt['unique_cases'],'whole_seconds':receipt['whole_seconds']}),flush=True)

if __name__ == '__main__':
    main()
