"""Bind reported primary-board measurements to raw rows, fixtures and binaries."""
from pathlib import Path
import csv,hashlib,json,re,unittest

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/primary_hardware'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class PrimaryHardwareTests(unittest.TestCase):
    def setUp(self):
        self.summary=json.loads((OUT/'hardware_summary.json').read_text())
        self.fixture=json.loads((OUT/'fixture.json').read_text())

    def test_full_fixture_and_both_physical_boards_pass(self):
        self.assertEqual(self.summary['total_comparisons'],3576)
        self.assertEqual({b['target'] for b in self.summary['boards']},{'esp8266_4m','esp32s3_16m'})
        self.assertEqual(len(self.fixture['cases']),1788)
        for board in self.summary['boards']:
            self.assertTrue(board['physical_board_measured'] and board['all_passed'])
            self.assertEqual(board['fixture_sha256'],sha(OUT/'fixture.json'))
            for model in board['models']:
                self.assertEqual(model['mismatches'],0)
                self.assertEqual(model['n'],468 if model['key'].startswith('ph_') else 192)
                self.assertGreater(model['batch_mean_us_p50'],0)

    def test_raw_serial_rows_and_tolerance(self):
        for board in self.summary['boards']:
            folder=(ROOT/board['run_summary']).parent
            with (folder/'samples.csv').open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),1788)
            serial=[json.loads(x) for x in (folder/'serial.jsonl').read_text().splitlines()]
            rx=[bytes.fromhex(x['hex']).decode('ascii','replace').strip() for x in serial if x['direction']=='RX']
            responses=[x for x in rx if x.startswith('R,')]
            self.assertEqual(len(responses),1788)
            for row,response,case in zip(rows,responses,self.fixture['cases']):
                self.assertEqual(int(row['id']),case['id'])
                self.assertEqual(int(response.split(',')[1]),case['id'])
                error=abs(float(row['prediction'])-case['expected'])
                self.assertLessEqual(error,2e-4+2e-5*abs(case['expected']))
                self.assertAlmostEqual(float(row['mean_us_per_call']),int(row['batch_us'])/64)

    def test_replay_source_binary_snapshots_are_immutable(self):
        for board in self.summary['boards']:
            folder=(ROOT/board['run_summary']).parent
            for name,digest in board['source_sha256'].items():
                self.assertEqual(sha(folder/'snapshot'/name),digest)
            for name,digest in board['binary_sha256'].items():
                self.assertEqual(sha(folder/'artifacts'/name),digest)
            for model in board['models']:
                header=ROOT/'firmware/primary_hardware/include'/(model['key']+'.h')
                self.assertEqual(sha(header),model['header_sha256'])

    def test_two_sources_have_anchored_floats_and_no_shared_figures(self):
        paper=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
        self.assertEqual(sorted(x.name for x in paper.rglob('*.tex')),['manuscript.tex','supplement.tex'])
        images=[]
        for stem in ['manuscript','supplement']:
            text=(paper/(stem+'.tex')).read_text(encoding='utf-8')
            refs=re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',text)
            labels=re.findall(r'\\label\{([^}]+)\}',text)
            self.assertEqual(len(labels),len(set(labels)))
            self.assertFalse(set(refs)-set(labels))
            for m in re.finditer(r'\\begin\{(table|figure)\}.*?\\end\{\1\}',text,re.S):
                label=re.findall(r'\\label\{([^}]+)\}',m[0])
                self.assertEqual(len(label),1)
                self.assertIn(label[0],refs)
            images.append(set(re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',text)))
        self.assertFalse(images[0]&images[1])

if __name__=='__main__':unittest.main()
