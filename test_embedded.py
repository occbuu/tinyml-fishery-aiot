"""Check that manuscript implementation evidence still matches its actual artifacts."""
from pathlib import Path
import hashlib,json,re,unittest

ROOT=Path(__file__).resolve().parent


class EmbeddedEvidenceTests(unittest.TestCase):
    def test_compiled_parity_results_match_exported_headers(self):
        r=json.loads((ROOT/'results/c_reference_validation.json').read_text())
        self.assertTrue(r['all_passed']);self.assertEqual(len(r['rows']),20)
        self.assertEqual(sum(x['n'] for x in r['rows']),5440)
        for x in r['rows']:
            p=ROOT/f"firmware/c_reference/{x['task']}_{x['method']}.h"
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['header_sha256'])
            self.assertEqual(x['failure_count'],0)

    def test_cross_build_evidence_matches_actual_elf(self):
        r=json.loads((ROOT/'results/esp32_build_summary.json').read_text())
        self.assertEqual(len(r['rows']),5);self.assertFalse(r['physical_board_measured'])
        for x in r['rows']:
            p=ROOT/f"firmware/wokwi_platformio/.pio/build/{x['environment']}/firmware.elf"
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['elf_sha256'])
            self.assertGreater(x['linked_flash_sections_bytes'],x['static_data_bss_bytes'])

    def test_every_bibliography_entry_is_cited_and_every_citation_resolves(self):
        paper=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
        import sys
        sys.path.insert(0,str(ROOT.parent))
        from build_manuscript_references import read_document
        for entry in ('main.tex','supplementary.tex'):
            texts=read_document(paper/entry)
            ref='main_references.tex' if entry=='main.tex' else 'supplementary_references.tex'
            bib=set(re.findall(r'\\bibitem\{([^}]+)\}',(paper/ref).read_text(encoding='utf-8')))
            cites={key.strip() for group in re.findall(r'\\cite\{([^}]+)\}',texts) for key in group.split(',')}
            self.assertFalse(cites-bib);self.assertFalse(bib-cites)


if __name__=='__main__':unittest.main()
