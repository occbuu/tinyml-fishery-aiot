"""Regression checks for the scientific interpretation of resource selection."""
import json
import unittest
from analyze_reporting import ROOT, select_at_budget, paired_ph_comparison
import pandas as pd
import numpy as np


class ReportingTests(unittest.TestCase):
    def test_ph_pairing_is_order_invariant_and_retains_whole_ponds(self):
        pred=pd.read_csv(ROOT/'results/vietnam_daily_predictions.csv')
        a=paired_ph_comparison(pred)
        b=paired_ph_comparison(pred.sample(frac=1,random_state=7))
        self.assertEqual(a['n'],468)
        self.assertEqual(a['resamples'],6**6)
        self.assertAlmostEqual(a['difference_mean'],b['difference_mean'])
        np.testing.assert_allclose(a['paired_pond_bootstrap_ci95'],b['paired_pond_bootstrap_ci95'])
        rows=pd.read_csv(ROOT/'results/vietnam_daily_trials.csv')
        pair=rows[(rows.task=='ph')&(rows.package=='TargetOnly')&(~rows.domain_qc)]
        delta=pair.loc[pair.method=='Ridge','test_mae'].iloc[0]-pair.loc[pair.method=='Persistence','test_mae'].iloc[0]
        self.assertAlmostEqual(a['difference_mean'],delta)

    def test_ph_pairing_rejects_missing_origins(self):
        pred=pd.read_csv(ROOT/'results/vietnam_daily_predictions.csv')
        drop=pred[(pred.task=='ph')&(pred.package=='TargetOnly')&(pred.method=='Ridge')].index[0]
        with self.assertRaises(ValueError):paired_ph_comparison(pred.drop(index=drop))

    def test_lab_forest_is_excluded_by_budget_despite_validation_advantage(self):
        data=json.loads((ROOT/'results/vietnam_summary.json').read_text())
        rows=[r for r in data['vibrio']['trials'] if r['censor']=='half' and r['package']=='Laboratory10']
        forest=next(r for r in rows if r['method']=='Forest16')
        mean=next(r for r in rows if r['method']=='Mean')
        self.assertLess(forest['validation_mae'],mean['validation_mae'])
        self.assertLess(forest['test_mae'],mean['test_mae'])
        self.assertEqual(select_at_budget(rows,4096)['method'],'Mean')
        self.assertEqual(select_at_budget(rows,8192)['method'],'Forest16')
        self.assertEqual(select_at_budget(rows,8192,.10)['method'],'Mean')
        altered=[dict(r,test_mae=1e9 if r['method']=='Forest16' else 0) for r in rows]
        self.assertEqual(select_at_budget(altered,8192)['method'],'Forest16')

    def test_sensitivity_denominators_and_do_scope(self):
        r=json.loads((ROOT/'results/reporting_sensitivity.json').read_text())
        self.assertEqual(len(r['budgets']),54)
        self.assertEqual(len(r['telemetry_sensitivity']),48)
        self.assertIn('unresolved',r['daily_do_status'])


if __name__=='__main__':unittest.main()

