import unittest,json
import numpy as np
import pandas as pd
from vietnam_benchmark import (ROOT,SOURCE,daily_design,daily_masks,load_vibrio,digest,choose)


class VietnamTests(unittest.TestCase):
    def test_group_lags_never_cross_pond_or_year(self):
        f=pd.DataFrame(dict(date=list(pd.date_range('2018-01-01',periods=8))+list(pd.date_range('2019-01-01',periods=8)),
                            year=[2018]*8+[2019]*8,pond=['T1']*16,series=['2018_T1']*8+['2019_T1']*8,
                            do=[5.]*8+[9.]*8,ph=[8.]*16,temperature=[30.]*16))
        d=daily_design(f,'do','MultiSensor')
        self.assertTrue(np.isnan(d.iloc[8].y_lag1))
        self.assertTrue(np.isnan(d.iloc[7].label))
        self.assertEqual(d.iloc[9].y_lag1,9.)

    def test_grouped_features_are_causal(self):
        f=pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date'])
        a=daily_design(f,'do','MultiSensor');f.loc[f.date>'2019-05-01','do']=100
        b=daily_design(f,'do','MultiSensor')
        past=a.date<='2019-05-01'
        cols=[c for c in a if c.startswith('y_')]
        pd.testing.assert_frame_equal(a.loc[past,cols],b.loc[past,cols])

    def test_purge_and_year_boundary(self):
        f=pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date'])
        d=daily_design(f,'do','MultiSensor');tr,va,te,cut=daily_masks(d)
        self.assertLess(d.loc[tr,'label_date'].max(),d.loc[va,'date'].min())
        self.assertEqual(set(d.loc[te,'year']),{2019})
        self.assertFalse(d.loc[te,'label'].isna().any())

    def test_no_target_has_no_target_derived_feature(self):
        f=pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date'])
        a=daily_design(f,'do','NoTarget');f['do']=22.
        b=daily_design(f,'do','NoTarget')
        cols=['ph','temperature','clock_sin','clock_cos']
        pd.testing.assert_frame_equal(a[cols],b[cols])
        self.assertFalse(any(c.startswith('y_') for c in a))

    def test_censor_replacements_and_reference_transform(self):
        low,c=load_vibrio('zero');mid,_=load_vibrio('half');high,_=load_vibrio('loq')
        self.assertEqual(c['Vibrio_CFU'],13)
        self.assertTrue((low.response<=mid.response).all() and (mid.response<=high.response).all())
        p=next(SOURCE.glob('07_*/**/vibrio_dataset_2022_2025.xlsx'))
        ref=pd.read_excel(p)
        np.testing.assert_allclose(mid.response,ref.log_Vibrio,atol=1e-8)

    def test_vibrio_splits_do_not_share_dates(self):
        d,_=load_vibrio()
        train=set(d.loc[d.Year<=2023,'Date']);val=set(d.loc[d.Year==2024,'Date']);test=set(d.loc[d.Year==2025,'Date'])
        self.assertFalse(train&val or train&test or val&test)
        self.assertEqual((len(d[d.Year<=2023]),len(d[d.Year==2024]),len(d[d.Year==2025])),(303,184,192))

    def test_local_source_hashes(self):
        m=json.loads((ROOT/'data/vietnam_manifest.json').read_text(encoding='utf-8'))
        for x in m['records']:self.assertEqual(digest(ROOT.parent/x['path']),x['sha256'])

    def test_selection_uses_validation_not_test(self):
        rows=[dict(method='Mean',parameter_bytes=4,validation_mae=1.,test_mae=100.),
              dict(method='Ridge',parameter_bytes=100,validation_mae=1.02,test_mae=0.)]
        self.assertEqual(choose(rows)['method'],'Mean')

    def test_prediction_denominators_and_economic_identity(self):
        r=json.loads((ROOT/'results/vietnam_summary.json').read_text(encoding='utf-8'))
        for target in ('do','ph'):
            counts={x['test_n'] for x in r['daily']['trials'] if x['task']==target and not x['domain_qc']}
            self.assertEqual(len(counts),1)
        for x in r['economics']['crops']:self.assertAlmostEqual(x['gross_vnd']-x['operating_vnd'],x['net_vnd'])


if __name__=='__main__':unittest.main()
