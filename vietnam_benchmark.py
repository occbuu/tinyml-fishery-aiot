"""Vietnam observations: grouped daily forecasts, assay observability and costs.

Reads user-supplied source files without modifying them or executing depositor code.
Daily pond forecasts and simultaneous Vibrio estimation are distinct experiments.
"""
from pathlib import Path
import hashlib,json,warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.exceptions import ConvergenceWarning
from run_benchmark import features,learner,parameter_bytes,metrics,SEED

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'DataVietNam'
OUT=ROOT/'results'; DATA=ROOT/'data/processed'
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
MODELS=('Mean','Persistence','Ridge','Tree4','Forest16','MLP8','HistBoost')
PACKAGES=('TargetOnly','MultiSensor','NoTarget')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def folder(prefix):
    matches=list(SOURCE.glob(prefix+'_*'))
    if len(matches)!=1: raise ValueError(f'Expected one source folder for {prefix}')
    return matches[0]


def daily_frames():
    frames=[]; audit=[]
    for year,prefix in ((2018,'04'),(2019,'03')):
        path=next(folder(prefix).glob('*water_daily*.xlsx'))
        for sheet,d in pd.read_excel(path,sheet_name=None).items():
            cols={next(c for c in d if str(c).startswith(s)):name
                  for s,name in [('DO','do'),('pH','ph'),('Temp','temperature')]}
            time=pd.to_datetime(d.iloc[:,0],errors='coerce')
            f=d[list(cols)].rename(columns=cols).apply(pd.to_numeric,errors='coerce')
            f.index=time
            f=f[f.index.notna() & (f.index.year==year)].sort_index()
            duplicate_dates=int(f.index.duplicated().sum())
            f=f.groupby(level=0).median()
            f=f.reindex(pd.date_range(f.index.min(),f.index.max(),freq='D'))
            masked={}
            for c,lo,hi in [('do',0,25),('ph',0,14),('temperature',0,45)]:
                bad=(f[c]<lo)|(f[c]>hi);masked[c]=int(bad.sum());f.loc[bad,c]=np.nan
            # Retain unusual but primary-range eligible values; never silently
            # repair 0.1 pH or 2.9 C. A separate domain-QC sensitivity masks them.
            flagged=((f.ph.notna() & ~f.ph.between(4,11)) |
                     (f.temperature.notna() & ~f.temperature.between(10,45)))
            pond=sheet.split('_')[0]
            f.index.name='date'; f=f.reset_index()
            f['year']=year;f['pond']=pond;f['series']=str(year)+'_'+pond
            audit.append(dict(year=year,pond=pond,grid_rows=len(f),duplicate_dates=duplicate_dates,
                              observed={c:int(f[c].notna().sum()) for c in ('do','ph','temperature')},
                              masked=masked,domain_flagged_rows=int(flagged.sum())))
            frames.append(f)
    frame=pd.concat(frames,ignore_index=True)
    frame.to_csv(DATA/'vietnam_daily.csv',index=False)
    return frame,audit


def daily_design(frame,target,package,domain_qc=False):
    blocks=[]
    for series,g in frame.groupby('series',sort=True):
        g=g.sort_values('date').set_index('date').copy()
        if domain_qc:
            g.loc[~g.ph.between(4,11),'ph']=np.nan
            g.loc[~g.temperature.between(10,45),'temperature']=np.nan
        extras=[c for c in ('do','ph','temperature') if c!=target]
        x=features(g,target,extras if package!='TargetOnly' else [])
        if package=='NoTarget':x=x[[c for c in x if not c.startswith('y_')]]
        x=x.reset_index(drop=True)
        x['label']=g[target].shift(-1).to_numpy()
        x['current']=g[target].ffill().to_numpy()
        x['date']=g.index.to_numpy();x['label_date']=g.index.to_numpy()+np.timedelta64(1,'D')
        x['year']=g.year.to_numpy();x['pond']=g.pond.to_numpy();x['series']=series
        blocks.append(x)
    return pd.concat(blocks,ignore_index=True)


def daily_masks(design):
    dates=np.sort(design.loc[design.year==2018,'date'].unique())
    cut=pd.Timestamp(dates[int(.65*len(dates))])
    valid=design.label.notna()
    train=valid & (design.year==2018) & (design.label_date<cut)
    val=valid & (design.year==2018) & (design.date>=cut)
    test=valid & (design.year==2019)
    assert design.loc[train,'label_date'].max()<design.loc[val,'date'].min()
    return train,val,test,cut


def fit_and_predict(name,x,y,others,current=None):
    mean=float(np.mean(y)); model=None; caught=[]
    if name not in ('Mean','Persistence'):
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always',ConvergenceWarning)
            model=learner(name).fit(x,y)
        caught=[str(m.message) for m in messages]
    pred=[]
    for i,a in enumerate(others):
        if name=='Mean':p=np.full(len(a),mean)
        elif name=='Persistence':p=np.nan_to_num(np.asarray(current[i],float),nan=mean)
        else:p=model.predict(a)
        pred.append(p)
    return model,pred,caught


def choose(rows):
    eligible=[r for r in rows if r['parameter_bytes'] is not None and r['parameter_bytes']<=4096]
    best=min(r['validation_mae'] for r in eligible)
    return min((r for r in eligible if r['validation_mae']<=1.05*best),
               key=lambda r:(r['parameter_bytes'],r['validation_mae'],r['method']))


def pond_bootstrap(y,p,pond):
    """Resample six pond identifiers, retaining all within-pond serial dependence."""
    groups=[abs(np.asarray(y)[pond==g]-np.asarray(p)[pond==g]) for g in np.unique(pond)]
    rng=np.random.default_rng(SEED);est=[]
    for _ in range(2000):
        sample=[groups[i] for i in rng.integers(0,len(groups),len(groups))]
        est.append(float(np.concatenate(sample).mean()))
    return list(np.quantile(est,[.025,.975]))


def daily_benchmark(frame):
    trials=[];predictions=[];selected=[]
    for qc in (False,True):
        for target in ('do','ph'):
            for package in PACKAGES:
                d=daily_design(frame,target,package,qc);tr,va,te,cut=daily_masks(d)
                cols=[c for c in d if c not in ('label','current','date','label_date','year','pond','series')]
                x=d[cols]; rows=[]; stored={}
                for name in MODELS:
                    if package=='NoTarget' and name=='Persistence':continue
                    model,p,w=fit_and_predict(name,x[tr],d.loc[tr,'label'],[x[va],x[te]],
                                             [d.loc[va,'current'],d.loc[te,'current']])
                    v=metrics(d.loc[va,'label'],p[0]); t=metrics(d.loc[te,'label'],p[1])
                    row=dict(task=target,package=package,domain_qc=qc,method=name,
                             train_n=int(tr.sum()),validation_n=int(va.sum()),test_n=t['n'],
                             validation_mae=v['mae'],test_mae=t['mae'],test_rmse=t['rmse'],
                             parameter_bytes=parameter_bytes(model,name),warnings=w,cut=str(cut.date()))
                    rows.append(row);stored[name]=p[1];trials.append(row)
                    if not qc:
                        for record,guess in zip(d.loc[te,['date','label_date','pond','label']].to_dict('records'),p[1]):
                            predictions.append(dict(task=target,package=package,method=name,**record,prediction=float(guess)))
                pick=dict(choose(rows));p=stored[pick['method']]
                pick['pond_bootstrap_mae_95']=pond_bootstrap(d.loc[te,'label'].to_numpy(),p,d.loc[te,'pond'].to_numpy())
                pick['per_pond']=[dict(pond=g,**metrics(d.loc[te & (d.pond==g),'label'],p[(d.loc[te,'pond']==g).to_numpy()]))
                                  for g in sorted(d.loc[te,'pond'].unique())]
                selected.append(pick)
    pd.DataFrame(trials).to_csv(OUT/'vietnam_daily_trials.csv',index=False)
    pd.DataFrame(predictions).to_csv(OUT/'vietnam_daily_predictions.csv',index=False)
    return dict(trials=trials,selection=selected,
                protocol='Train early 65% calendar dates of 2018, purge label boundary, validate remaining 2018, frozen-model test all eligible 2019 origins. No final refit; group lags by year and pond.',
                uncertainty='Descriptive percentile bootstrap of six 2019 pond identifiers, 2000 resamples; not national population confidence.')


def load_vibrio(censor='half'):
    base=folder('07');p=next(base.rglob('vibrio_dataset_2022_2025_raw.xlsx'))
    d=pd.read_excel(p)
    dictionary=pd.read_csv(next(base.rglob('data_dictionary.csv')))
    counts={}
    for _,row in dictionary.iterrows():
        c=row['variable']
        if c not in d or c in ('Date','Year','Area'):continue
        raw=d[c].astype(str); flagged=raw.str.contains('KPH|<',case=False,regex=True,na=False)
        number=pd.to_numeric(d[c],errors='coerce')
        # Use only explicitly censored strings, not arbitrary missing cells.
        if flagged.any():
            loq=float(row['loq']);counts[c]=int(flagged.sum())
            number.loc[flagged]=loq*{'zero':0.,'half':.5,'loq':1.}[censor]
        d[c]=number
    d['Date']=pd.to_datetime(d.Date);d['response']=np.log10(d.Vibrio_CFU+1)
    if d['response'].isna().any():raise ValueError('Unparsed Vibrio outcomes')
    if not np.array_equal(d.Year.to_numpy(),d.Date.dt.year.to_numpy()):raise ValueError('Year/date mismatch')
    return d,counts


def vibrio_benchmark():
    packages={'Field4':['Temp','pH','DO','Sal'],
              'Field5':['Temp','pH','DO','Sal','Alk'],
              'Laboratory10':['Temp','pH','DO','Sal','Alk','N-NO2-','N-NH4+','P-PO43-','TSS','COD']}
    trials=[]; selections=[]; predictions=[]
    for censor in ('half','zero','loq'):
        d,counts=load_vibrio(censor)
        tr=d.Year.isin([2022,2023]);va=d.Year==2024;te=d.Year==2025
        for package,cols in packages.items():
            rows=[];saved={}
            for name in MODELS:
                if name=='Persistence':continue # No persistent pond identity in source.
                model,p,w=fit_and_predict(name,d.loc[tr,cols],d.loc[tr,'response'],[d.loc[va,cols],d.loc[te,cols]])
                row=dict(package=package,censor=censor,method=name,validation_mae=metrics(d.loc[va,'response'],p[0])['mae'],
                         test_mae=metrics(d.loc[te,'response'],p[1])['mae'],test_rmse=metrics(d.loc[te,'response'],p[1])['rmse'],
                         train_n=int(tr.sum()),validation_n=int(va.sum()),test_n=int(te.sum()),
                         parameter_bytes=parameter_bytes(model,name),warnings=w)
                rows.append(row);saved[name]=p[1];trials.append(row)
                if censor=='half':
                    for i,guess in zip(d.index[te],p[1]):
                        predictions.append(dict(source_row=int(i)+2,package=package,method=name,date=str(d.loc[i,'Date'].date()),
                                                area=d.loc[i,'Area'],observed=float(d.loc[i,'response']),prediction=float(guess)))
            selections.append(dict(choose(rows)))
    d,_=load_vibrio();pd.DataFrame(trials).to_csv(OUT/'vietnam_vibrio_trials.csv',index=False)
    pd.DataFrame(predictions).to_csv(OUT/'vietnam_vibrio_predictions.csv',index=False)
    return dict(rows=len(d),censored_counts=counts,trials=trials,selection=selections,
                do_below3=int((d.DO<3).sum()),salinity_range=[float(d.Sal.min()),float(d.Sal.max())],
                protocol='Train 2022-2023; validate 2024; frozen test 2025. No random splits. All sampling dates/campaigns stay within a year block. Pond IDs unavailable; cannot certify unseen-pond generalization.',
                target='Contemporaneous total genus-level log10(CFU/mL+1), not disease, species-specific pathogen, future outbreak or sensor-failure label.')


def economic_context():
    rows=[]
    for year,prefix in ((2018,'04'),(2019,'03')):
        p=next(folder(prefix).glob('*output*.xlsx'))
        d=pd.read_excel(p,sheet_name='Economic Analysis',header=None)
        lookup={str(row.iloc[0]).strip():row.iloc[1:7].to_numpy() for _,row in d.iterrows()}
        for i,pond in enumerate(('T1','T2','T3','C1','C2','C3')):
            def val(key):return float(lookup[key][i])
            cost=val('Total operational cost (vnd)');energy=val('Fuel (vnd)')+val('Electricity (vnd)')
            feed=val('Feed (vnd)');income=val('Gross Income (vnd)');net=val('Net Income shrimp (vnd)')
            assert abs(income-cost-net)<1.
            rows.append(dict(year=year,pond=pond,operating_vnd=cost,energy_vnd=energy,feed_vnd=feed,
                             gross_vnd=income,net_vnd=net,energy_share=energy/cost,feed_share=feed/cost))
    pd.DataFrame(rows).to_csv(OUT/'vietnam_crop_economics.csv',index=False)
    summaries=[]
    for year in (2018,2019):
        g=[x for x in rows if x['year']==year]
        summaries.append(dict(year=year,pond_crops=len(g),
                             operating_median_vnd=float(np.median([x['operating_vnd'] for x in g])),
                             energy_share_median=float(np.median([x['energy_share'] for x in g])),
                             feed_share_median=float(np.median([x['feed_share'] for x in g])),
                             negative_net_count=sum(x['net_vnd']<0 for x in g)))
    # Historical nominal-VND sensitivity, not a vendor quotation or benefit claim.
    sensitivity=[]
    for annual in (300000,600000,1200000):
        for crops in (1,2):
            cost=annual/crops
            sensitivity.append(dict(assumed_annual_monitoring_vnd=annual,assumed_crops_per_year=crops,
                                    allocated_vnd_per_crop=cost,
                                    median_required_energy_reduction=float(np.median([cost/x['energy_vnd'] for x in rows])),
                                    crops_requiring_over_100pct_energy_reduction=sum(cost>x['energy_vnd'] for x in rows)))
    return dict(crops=rows,summary=summaries,break_even_scenarios=sensitivity,
                basis='2018-2019 nominal VND. Energy includes crop fuel and electricity; excludes sensor-specific attribution. No inflation conversion, causal trial/control claim, measured monitoring cost or asserted savings.')


def weekly_context():
    audit=[]
    for year,prefix in ((2018,'04'),(2019,'03')):
        p=next(folder(prefix).glob('Water_growth_weekly*.xlsx'))
        for sheet,d in pd.read_excel(p,sheet_name=None).items():
            chemistry=d.iloc[:,6:13]
            active=chemistry.notna().any(axis=1) & d.iloc[:,0].notna()
            dates=pd.to_datetime(d.loc[active].iloc[:,1],format='ISO8601',errors='coerce')
            audit.append(dict(year=year,pond=sheet.split('_')[0],observation_rows=int(active.sum()),
                              parseable_dates=int(dates.notna().sum()),
                              salinity_numeric_count=int(pd.to_numeric(d.loc[active].iloc[:,12],errors='coerce').notna().sum()),
                              tan_numeric_count=int(pd.to_numeric(d.loc[active].iloc[:,11],errors='coerce').notna().sum()),
                              forecasting_use=False,nitrogen_basis='TAN header lacks an explicit unit/basis; no inferred free-ammonia conversion.'))
    return audit


def mangrove_context():
    p=folder('08')/'Water data.xlsx';sheets=pd.read_excel(p,sheet_name=None,header=None)
    summaries=[];paired=[]
    for sheet,d in sheets.items():
        # Source has 30 household x age x replicate rows, six repeated observations.
        d=d.iloc[2:32];a=d.iloc[:,4:10].apply(pd.to_numeric,errors='coerce')
        values=a.to_numpy().ravel();values=values[np.isfinite(values)]
        summaries.append(dict(sheet=sheet,n=int(len(values)),minimum=float(values.min()),median=float(np.median(values)),maximum=float(values.max())))
        if sheet.startswith('3.'):
            for h,g in d.groupby(1):
                a=g.iloc[:,4:10].apply(pd.to_numeric,errors='coerce').to_numpy()
                diff=a[:,[1,3,5]]-a[:,[0,2,4]]
                paired.append(float(np.nanmean(diff)))
    return dict(parameters=summaries,households=len(paired),
                household_mean_do_after_minus_before=paired,
                median_household_do_difference=float(np.median(paired)),
                basis='Repeated before/after water exchange at three tides; household, age and replicate nesting. Descriptive only, no causal intervention or independent n=180 claim.')


def source_manifest():
    records=[];inventory=[]
    eligible_prefixes=('03','04','07','08')
    for d in sorted(SOURCE.iterdir()):
        if not d.is_dir():continue
        m=d/'_metadata.json';meta=json.loads(m.read_text(encoding='utf-8-sig')) if m.exists() else {}
        version=meta.get('latestVersion',{});zen=meta.get('metadata',{})
        doi=meta.get('persistentUrl') or meta.get('doi_url') or str(meta.get('doi',''))
        licence=version.get('license',zen.get('license',meta.get('data_licence',{})))
        used=d.name.startswith(eligible_prefixes)
        inventory.append(dict(folder=d.name,doi=doi,license=licence,used_in_analysis=used,
                              role='Daily forecasting/economics' if d.name.startswith(('03','04')) else
                              'Contemporaneous assay observability' if d.name.startswith('07') else
                              'Repeated chemistry context' if d.name.startswith('08') else
                              'Inventory only: heterogeneous survey, protocol, growth, host, microbiome or spatial data; no forced IoT task.'))
        if not used:continue
        expected={}
        for entry in version.get('files',meta.get('files',[])):
            entry=entry.get('dataFile',entry)
            checksum=entry.get('checksum')
            if isinstance(checksum,dict) and checksum.get('type')=='MD5':checksum='md5:'+checksum['value']
            if checksum:expected[entry.get('filename',entry.get('key'))]=checksum
        for p in sorted(d.rglob('*')):
            if not p.is_file() or p.suffix.lower() not in ('.xlsx','.csv','.json','.pdf','.docx','.rar') :continue
            if p.name.startswith('Monitoring_form'):continue
            check=expected.get(p.name)
            if check and check.startswith('md5:'):
                if hashlib.md5(p.read_bytes()).hexdigest()!=check.split(':',1)[1]:
                    raise ValueError(f'Source metadata checksum mismatch: {p.name}')
            records.append(dict(path=p.relative_to(ROOT.parent).as_posix(),bytes=p.stat().st_size,sha256=digest(p),
                                source_checksum=check,source_checksum_verified=bool(check),
                                dataset=d.name,doi=doi,license=licence,acquisition='User-supplied local download; download time and Guestbook identity not inferred.'))
    result=dict(source_root='../DataVietNam',records=records,inventory=inventory,
                total_bytes=sum(x['bytes'] for x in records),source_files_unchanged=True,
                status='Vietnam sources are locally available; supersedes historical pending-access notes for these sources.')
    (ROOT/'data/vietnam_manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result


def plot_results(result):
    fig,grid=plt.subplots(2,2,figsize=(9,6.8));axes=list(grid.flat)
    for ax,target,label in zip(axes[:2],('do','ph'),('Next-day DO (source scale)','Next-day pH')):
        rows=[x for x in result['daily']['trials'] if x['task']==target and x['package']=='MultiSensor' and not x['domain_qc']]
        ax.barh([x['method'] for x in rows],[x['test_mae'] for x in rows],color='#187b80');ax.set_xlabel('2019 test MAE');ax.set_title(label)
    rows=[x for x in result['vibrio']['selection'] if x['censor']=='half']
    axes[2].barh([x['package'] for x in rows],[x['test_mae'] for x in rows],color='#b67538')
    axes[2].set_xlabel('2025 test MAE (log units)');axes[2].set_title('Total Vibrio: simultaneous estimate')
    econ=result['economics']['summary'];position=np.arange(len(econ))
    axes[3].bar(position-.17,[100*x['energy_share_median'] for x in econ],.34,label='Energy')
    axes[3].bar(position+.17,[100*x['feed_share_median'] for x in econ],.34,label='Feed')
    axes[3].set_xticks(position,[str(x['year']) for x in econ]);axes[3].set_ylabel('Median crop expenditure share (%)')
    axes[3].set_title('Historical cost context');axes[3].legend()
    fig.tight_layout();fig.savefig(OUT/'vietnam_benchmark.pdf');fig.savefig(OUT/'vietnam_benchmark.png',dpi=180);plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    manifest=source_manifest();frame,audit=daily_frames()
    result=dict(seed=SEED,daily_audit=audit,daily=daily_benchmark(frame),vibrio=vibrio_benchmark(),
                economics=economic_context(),mangrove=mangrove_context(),weekly_audit=weekly_context(),
                source_manifest='data/vietnam_manifest.json',local_file_count=len(manifest['records']))
    (OUT/'vietnam_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    plot_results(result)
    print('Vietnam benchmark complete: daily forecasts, Vibrio observability, chemistry and crop economics.')


if __name__=='__main__':main()
