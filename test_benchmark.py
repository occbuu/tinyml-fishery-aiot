import unittest,json
from pathlib import Path
import numpy as np
import pandas as pd
from run_benchmark import features,predict,quality_fallback,DATA,OUT,ROOT
from transfer_and_context import freshwater_nh3_fraction


class BenchmarkTests(unittest.TestCase):
    def test_causal_feature_builder(self):
        idx=pd.date_range('2024-01-01',periods=30,freq='h')
        frame=pd.DataFrame({'ph':np.arange(30.),'temperature':25.},index=idx)
        a=features(frame,'ph',['temperature'])
        frame.loc[idx[20]:,'ph']=1000
        b=features(frame,'ph',['temperature'])
        pd.testing.assert_frame_equal(a.iloc[:20],b.iloc[:20])

    def test_missing_persistence_is_causal(self):
        np.testing.assert_array_equal(predict('Persistence',None,None,[5,np.nan,np.nan,7],4),[5,5,5,7])

    def test_gate_marks_missing_unknown(self):
        idx=pd.date_range('2024-01-01',periods=30,freq='h')
        f=pd.DataFrame({'ph':[7.]*20+[np.nan]*5+[7.]*5},index=idx)
        pred,flags=quality_fallback(f,'ph',np.full(30,7.),20)
        self.assertTrue(flags[20:25].all())
        self.assertTrue(np.isfinite(pred).all())

    def test_no_target_package_does_not_smuggle_target(self):
        idx=pd.date_range('2024-01-01',periods=30,freq='h')
        a=pd.DataFrame({'ph':7.,'temperature':25.},index=idx)
        b=a.copy(); b['ph']=9.
        af=features(a,'ph',['temperature']); bf=features(b,'ph',['temperature'])
        cols=[c for c in af if not c.startswith('y_')]
        pd.testing.assert_frame_equal(af[cols],bf[cols])

    def test_salinity_not_silently_ignored_in_ammonia(self):
        with self.assertRaises(ValueError): freshwater_nh3_fraction(28,8,10)
        self.assertLess(freshwater_nh3_fraction(28,7),freshwater_nh3_fraction(28,8))

    def test_download_integrity(self):
        import hashlib
        manifest=json.loads((ROOT/'data/download_manifest.json').read_text(encoding='utf-8'))
        for row in manifest['records']:
            p=ROOT/row['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])

    def test_external_download_manifest_is_separate_from_local_vietnam_manifest(self):
        m=json.loads((ROOT/'data/download_manifest.json').read_text(encoding='utf-8'))
        self.assertFalse(any(x['dataset'].startswith('vietnam_') for x in m['records']))

    def test_primary_marine_does_not_use_unreviewed_oxygen(self):
        frame=pd.read_csv(DATA/'marine_temperature.csv')
        self.assertNotIn('oxygen',frame.columns)

    def test_every_stress_prediction_has_same_target_count(self):
        trials=pd.read_csv(OUT/'stress_trials.csv')
        for _,g in trials.groupby(['task','fold','fault']):
            self.assertEqual(g['n'].nunique(),1)
            self.assertTrue((g['prediction_coverage']==1).all())

    def test_selection_does_not_exceed_parameter_budget(self):
        result=json.loads((OUT/'benchmark_summary.json').read_text())
        self.assertTrue(all(x['parameter_bytes']<=4096 for x in result['selection']))


if __name__=='__main__':unittest.main()
