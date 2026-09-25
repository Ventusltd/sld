import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_furnace import digest, verify


class FurnaceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data/furnace').mkdir(parents=True)
        (self.root / 'scripts').mkdir()
        self.write('data/library.json', {'components': [{'id': 'a', 'size': {'width': 1, 'height': 1}}]})
        self.write('sources.yaml', {'sources': []})
        self.write('data/source-lock.json', {'files': []})
        (self.root / 'scripts/furnace.py').write_text('test fixture only')
        self.write('data/furnace/photon-library.json', {'library_sha256': digest(self.root / 'data/library.json'), 'production_enabled': False, 'components': [{'id': 'a', 'width': 1., 'height': 1.}]})
        self.receipt = dict(accepted=True, library_sha256=digest(self.root / 'data/library.json'), source_lock_sha256=digest(self.root / 'data/source-lock.json'), script_sha256=digest(self.root / 'scripts/furnace.py'), photon_library_sha256=digest(self.root / 'data/furnace/photon-library.json'), component_count=1, excluded_component_count=0, grid=2, pitch=.5, cpu_reference_cases=4, threshold_fixtures=9, injected_error_detected=True, channels=['raw CUDA interval intersection', 'CuPy centre-distance separation'], unique_cases=4, iterations=[dict(gap=0, unique_cases=4, mismatches=0, separated=1, touching=1, overlapping=2)])
        self.write('data/furnace/photon-evidence.json', self.receipt)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding='utf-8')

    def test_valid_fixture(self):
        self.assertEqual(verify(self.root)['unique_cases'], 4)

    def test_bound_file_mutation_rejected(self):
        for path in ['data/library.json', 'data/source-lock.json', 'scripts/furnace.py', 'data/furnace/photon-library.json']:
            with self.subTest(path=path):
                file = self.root / path
                original = file.read_bytes()
                file.write_bytes(original + b' ')
                with self.assertRaises(ValueError):
                    verify(self.root)
                file.write_bytes(original)

    def test_invalid_receipts(self):
        mutations = [dict(accepted=False), dict(accepted=1), dict(injected_error_detected=False), dict(threshold_fixtures=0), dict(unique_cases=8), dict(cpu_reference_cases=0), dict(component_count=2), dict(iterations=[])]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.write('data/furnace/photon-evidence.json', self.receipt | mutation)
                with self.assertRaises(ValueError):
                    verify(self.root)

    def test_duplicate_domains_and_corrupt_counts(self):
        for edit in ['duplicate', 'mismatch', 'counts']:
            receipt = copy.deepcopy(self.receipt)
            if edit == 'duplicate':
                receipt['iterations'] *= 2
                receipt['unique_cases'] *= 2
            elif edit == 'mismatch':
                receipt['iterations'][0]['mismatches'] = 1
            else:
                receipt['iterations'][0]['separated'] = 0
            self.write('data/furnace/photon-evidence.json', receipt)
            with self.assertRaises(ValueError):
                verify(self.root)


if __name__ == '__main__':
    unittest.main()
