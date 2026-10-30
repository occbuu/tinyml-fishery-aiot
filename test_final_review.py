"""Regression tests for repeated generation and frozen campaign sensitivities."""
from pathlib import Path
import json,re,unittest
import pandas as pd
from integrate_primary_hardware import refresh_manuscript,latex_scientific

ROOT=Path(__file__).resolve().parent

class FinalReviewTests(unittest.TestCase):
    def test_hardware_refresh_is_idempotent_and_repairs_legacy_repetition(self):
        sentence='Primary-model replay also establishes numerical agreement on two tested microcontrollers, with execution timing reported separately from the historical payload estimates.'
        source=r'\section{Interpretation and Limits}'+'\n'+r'\section{Conclusions}'+'\n'+(sentence+' ')*4
        block='% BEGIN GENERATED PRIMARY HARDWARE\nNew evidence\n% END GENERATED PRIMARY HARDWARE\n'
        once=refresh_manuscript(source,block)
        self.assertEqual(once.count(sentence),1)
        self.assertEqual(refresh_manuscript(once,block),once)
        self.assertEqual(latex_scientific(1.263641e-6),r'$1.26\times10^{-6}$')

    def test_date_influence_recomputed_from_frozen_predictions(self):
        pred=pd.read_csv(ROOT/'results/vietnam_vibrio_predictions.csv')
        g=pred[pred.package=='Laboratory10'].pivot(index=['source_row','date'],columns='method',values=['observed','prediction'])
        d=abs(g['prediction']['Forest16']-g['observed']['Forest16'])-abs(g['prediction']['Mean']-g['observed']['Mean'])
        result=json.loads((ROOT/'results/reporting_sensitivity.json').read_text())['vibrio_comparison']
        self.assertEqual(len(result['date_influence']),12)
        self.assertEqual(result['dates_favoring_forest'],8)
        for row in result['date_influence']:
            keep=d.index.get_level_values('date')!=row['date']
            self.assertAlmostEqual(d[keep].mean(),row['leave_one_date_out_difference'])
            self.assertLess(row['leave_one_date_out_difference'],0)
        self.assertAlmostEqual(result['equally_weighted_date_difference'],d.mean())

    def test_exact_budget_breakpoint_is_not_a_board_limit(self):
        result=json.loads((ROOT/'results/reporting_sensitivity.json').read_text())
        rows=[r for r in result['budget_breakpoints'] if r['package']=='Laboratory10']
        self.assertEqual([(r['budget_bytes'],r['method']) for r in rows],[(4,'Mean'),(4952,'Forest16')])

    def test_owned_hardware_tables_have_no_blank_rows_or_console_numbers(self):
        source=(ROOT.parent/'Paper2_FisheryAIoT_V4_Research/manuscript.tex').read_text(encoding='utf-8')
        block=re.search(r'% BEGIN GENERATED PRIMARY HARDWARE.*?% END GENERATED PRIMARY HARDWARE',source,re.S)[0]
        for table in re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',block,re.S):
            self.assertNotRegex(table,r'\n\s*\n')
        self.assertNotRegex(block,r'\b\d+(?:\.\d+)?[eE][+-]\d+\b')
        conclusion=source.split(r'\section{Conclusions}')[1].split(r'\section*{Declarations}')[0]
        sentences=[x.strip() for x in conclusion.split('. ') if len(x.strip())>40]
        self.assertEqual(len(sentences),len(set(sentences)))

if __name__=='__main__':unittest.main()
