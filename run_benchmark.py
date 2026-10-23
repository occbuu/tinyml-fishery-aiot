"""Original public-data benchmark: purged forward blocks and lightweight models.

No device timings or fish-survival outcomes are inferred from host replay.
Fixed hyperparameters and validation-only selection; keep all adverse outcomes.
"""
from pathlib import Path
import csv,json,time,platform,warnings
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.exceptions import ConvergenceWarning
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/processed'; OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
SEED=20261021
LAGS=(0,1,2,3,6)


def features(frame,target,extras):
    f=pd.DataFrame(index=frame.index)
    s=frame[target]
    for lag in LAGS:f['y_lag'+str(lag)]=s.shift(lag)
    f['y_mean6']=s.rolling(6,min_periods=1).mean()
    f['y_delta']=s-s.shift(1)
    hour=frame.index.hour+frame.index.minute/60
    f['clock_sin']=np.sin(2*np.pi*hour/24); f['clock_cos']=np.cos(2*np.pi*hour/24)
    for col in extras:f[col]=frame[col]
    return f


def learner(name):
    if name=='Ridge':base=Ridge(alpha=1.)
    elif name=='Tree4':base=DecisionTreeRegressor(max_depth=4,min_samples_leaf=12,random_state=SEED)
    elif name=='Forest16':base=RandomForestRegressor(n_estimators=16,max_depth=4,min_samples_leaf=12,random_state=SEED,n_jobs=1)
    elif name=='MLP8':
        base=TransformedTargetRegressor(regressor=MLPRegressor(hidden_layer_sizes=(8,),activation='relu',
            solver='lbfgs',alpha=.01,max_iter=300,random_state=SEED),transformer=StandardScaler())
    elif name=='HistBoost':base=HistGradientBoostingRegressor(max_iter=80,max_leaf_nodes=15,l2_regularization=1.,early_stopping=False,random_state=SEED)
    else:raise ValueError(name)
    return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),base)


def parameter_bytes(model,name):
    """Portable float32 payload estimate; not sklearn pickle or measured MCU RAM."""
    if name in ('Persistence','Mean'):return 4 if name=='Mean' else 0
    n=len(model[0].statistics_)
    front=3*n*4 # imputer median, scaling mean and scaling divisor
    m=model[-1]
    if name=='Ridge':return front+4*(m.coef_.size+1)
    if name=='Tree4':return front+16*m.tree_.node_count
    if name=='Forest16':return front+sum(16*x.tree_.node_count for x in m.estimators_)
    if name=='MLP8':
        nn=m.regressor_
        return front+4*(sum(x.size for x in nn.coefs_+nn.intercepts_)+2)
    return None # host comparator, no portable implementation claimed


def predict(name,model,x,current,mean):
    if name=='Persistence':return pd.Series(np.asarray(current)).ffill().fillna(mean).to_numpy()
    if name=='Mean':return np.full(len(x),mean)
    return model.predict(x)


def metrics(y,p):
    good=np.isfinite(y)&np.isfinite(p)
    e=np.asarray(p)[good]-np.asarray(y)[good]
    eligible=int(np.isfinite(y).sum())
    return dict(n=int(good.sum()),eligible_targets=eligible,prediction_coverage=float(good.sum()/eligible) if eligible else None,
                mae=float(np.mean(abs(e))),rmse=float(np.sqrt(np.mean(e**2))))


def quality_fallback(frame,target,model_pred,train_end):
    """Causal jump/range gate, no access to injection flags or reference target.

    No learning on test. Slow monotone drift may remain undetected. Low raw DO
    remains available to independent protection and is never certified healthy.
    """
    s=frame[target].to_numpy(float)
    train=s[:train_end]
    diff=abs(np.diff(train)); diff=diff[np.isfinite(diff)]
    jump=max(float(np.quantile(diff,.995))*2,1e-6)
    q1,q3=np.nanquantile(train,[.25,.75]); width=max(q3-q1,1e-6)
    low,high=q1-4*width,q3+4*width
    trusted=float(np.nanmedian(train)); invalid=[]; output=[]
    for k,value in enumerate(s):
        valid=np.isfinite(value) and low<=value<=high and (k==0 or not np.isfinite(s[k-1]) or abs(value-s[k-1])<=jump)
        if valid:trusted=value
        p=model_pred[k]
        output.append(p if valid and np.isfinite(p) else trusted)
        invalid.append(not valid)
    return np.asarray(output),np.asarray(invalid)


def export_c(model,name,feature_names,path,mean):
    """Allocation-free C reference, float32 coefficients. No unmeasured INT8 claim."""
    path.parent.mkdir(parents=True,exist_ok=True)
    n=len(feature_names)
    lines=['/* Generated from training/validation only; feature order below. */','#pragma once','#include <math.h>',
           f'#define MODEL_INPUTS {n}','/* '+', '.join(feature_names)+' */']
    def arr(key,values):
        vals=np.asarray(values,np.float32).ravel()
        lines.append(f'static const float {key}[{len(vals)}] = '+'{'+','.join(f'{float(v):.9e}f' for v in vals)+'};')
    if name=='Persistence':
        lines.extend([f'static float model_last={mean:.9e}f;',
                      f'static inline void model_reset(void) {{ model_last={mean:.9e}f; }}',
                      'static inline float model_predict(const float *raw) { if(isfinite(raw[0])) model_last=raw[0]; return model_last; }'])
    elif name=='Mean':
        lines.extend(['static inline void model_reset(void) {}',
                      f'static inline float model_predict(const float *raw) {{ (void)raw; return {mean:.9e}f; }}'])
    else:
        arr('model_median',model[0].statistics_); arr('model_center',model[1].mean_); arr('model_scale',model[1].scale_)
        lines.append('static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];')
        m=model[-1]
        if name=='Ridge':
            # Arrays must have file scope, before the function definition.
            lines.pop(); arr('model_w',m.coef_)
            lines.append('static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];')
            lines.append(f'float out={float(m.intercept_):.9e}f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }}')
        elif name=='Tree4':
            tree=m.tree_
            def node(k):
                if tree.children_left[k]<0:return f'return {float(tree.value[k,0,0]):.9e}f;'
                return f'if(x[{tree.feature[k]}]<={float(tree.threshold[k]):.9e}f){{'+node(tree.children_left[k])+'}else{'+node(tree.children_right[k])+'}'
            lines.append(node(0)+'}')
        elif name=='MLP8':
            lines.pop(); nn=m.regressor_; arr('model_w1',nn.coefs_[0]);arr('model_b1',nn.intercepts_[0]);arr('model_w2',nn.coefs_[1])
            lines.append('static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];')
            lines.append(f'float z={float(nn.intercepts_[1][0]):.9e}f; for(int j=0;j<8;j++){{float a=model_b1[j];for(int i=0;i<MODEL_INPUTS;i++)a+=x[i]*model_w1[i*8+j]; z+=fmaxf(a,0)*model_w2[j];}} return z*{float(m.transformer_.scale_[0]):.9e}f+{float(m.transformer_.mean_[0]):.9e}f; }}')
        else:raise ValueError('No C export for '+name)
    if name not in ('Mean','Persistence'):lines.append('static inline void model_reset(void) {}')
    path.write_text('\n'.join(lines),encoding='utf-8')


def task_benchmark(task):
    key=task['key']; target=task['target']; H=task['horizon_steps']
    frame=pd.read_csv(DATA/(key+'.csv'),index_col=0,parse_dates=True)
    X=features(frame,target,task['extras']); y=frame[target].shift(-H).to_numpy()
    current=frame[target].to_numpy(); N=len(frame)
    names=('Persistence','Mean','Ridge','Tree4','Forest16','MLP8','HistBoost')
    results=[]; traces=[]; selected=[]; stress=[]
    cached={}
    for fold,(a,b,c) in enumerate(((.5,.65,.8),(.65,.8,1.))):
        train_end=int(N*a); val_end=int(N*b); test_end=int(N*c)
        pos=np.arange(N)
        # Purge labels that would cross a partition boundary. All methods use
        # the same observed origin/target subset, independent of sensor package.
        eligible=np.isfinite(y)&np.isfinite(current)&(pos>=6)
        train=eligible&(pos<train_end-H)
        val=eligible&(pos>=train_end)&(pos<val_end-H)
        test=eligible&(pos>=val_end)&(pos<test_end-H)
        assert (pos[train]+H).max()<pos[val].min()
        assert (pos[val]+H).max()<pos[test].min()
        mean=float(np.mean(y[train])); scale=float(np.std(y[train]))
        base=[col for col in X if col.startswith('y_') or col.startswith('clock_')]
        packages={'TargetOnly':base,'MultiSensor':list(X),'NoTarget':[c for c in X if not c.startswith('y_')]}
        for package,cols in packages.items():
            if package=='NoTarget' and not task['extras']:continue
            candidates=[]
            for name in names:
                if package=='NoTarget' and name=='Persistence':continue
                model=None
                if name not in ('Persistence','Mean'):
                    model=learner(name)
                    with warnings.catch_warnings(record=True) as captured:
                        warnings.simplefilter('always',ConvergenceWarning)
                        model.fit(X.loc[train,cols],y[train])
                    nonconverged=any(isinstance(w.message,ConvergenceWarning) for w in captured)
                else: nonconverged=False
                vp=predict(name,model,X.loc[val,cols],current[val],mean)
                tp=predict(name,model,X.loc[test,cols],current[test],mean)
                size=parameter_bytes(model,name)
                # Comparable host API latency; includes library dispatch, not acquisition.
                xx=X.loc[test,cols].iloc[:1]
                times=[]
                if model is not None:
                    for _ in range(30):
                        t=time.perf_counter_ns(); model.predict(xx); times.append((time.perf_counter_ns()-t)/1000)
                rec=dict(task=key,fold=fold,package=package,method=name,unit=task['unit'],horizon_minutes=H*task['step_minutes'],
                    train_n=int(train.sum()),validation_n=int(val.sum()),test_n=int(test.sum()),
                    validation_mae=float(np.mean(abs(y[val]-vp))),**metrics(y[test],tp),
                    parameter_bytes=size,estimated_scratch_bytes=4*(len(cols)+8),
                    host_api_median_us=float(np.median(times)) if times else None,convergence_warning=nonconverged)
                results.append(rec); candidates.append((rec,model,cols))
                for k,p in zip(np.flatnonzero(test),tp):traces.append(dict(task=key,fold=fold,package=package,method=name,time=str(frame.index[k]),y=float(y[k]),prediction=float(p)))
            allowed=[v for v in candidates if v[0]['parameter_bytes'] is not None and v[0]['parameter_bytes']<=4096]
            best=min(v[0]['validation_mae'] for v in allowed)
            close=[v for v in allowed if v[0]['validation_mae']<=best*1.05]
            pick=min(close,key=lambda v:(v[0]['parameter_bytes'],v[0]['validation_mae']))
            rec,model,cols=pick
            selected.append({k:rec[k] for k in ('task','fold','package','method','validation_mae','mae','parameter_bytes')})
            if package=='MultiSensor':
                cached[fold]=(model,rec['method'],cols,train_end,val_end,test_end,test,mean,scale)
                if fold==1:
                    export_c(model,rec['method'],cols,ROOT/f'firmware/generated/{key}.h',mean)
                    for label in ('Ridge','Tree4','MLP8'):
                        item=next(v for v in candidates if v[0]['method']==label)
                        export_c(item[1],label,cols,ROOT/f'firmware/generated/{key}_{label}.h',mean)
                    fixture=X.loc[test,cols].iloc[:20].to_numpy()
                    validation_export=dict(features=cols,example_inputs=[[float(v) if np.isfinite(v) else None for v in row] for row in fixture],
                        reference_predictions=predict(rec['method'],model,X.loc[test,cols].iloc[:20],current[test][:20],mean).tolist(),
                        selected_method=rec['method'],parameter_bytes=rec['parameter_bytes'],note='Prediction fixture from the forecasting run; see separate c_reference_validation.json and esp32_build_summary.json for implementation verification.')
                    (OUT/(key+'_export_reference.json')).write_text(json.dumps(validation_export,indent=2,allow_nan=False))
                # Quality gate is exercised only where a target sensor is actually observed.
                for fault in ('clean','spikes','positive_drift','dropout'):
                    corrupted=frame.copy(); start=val_end+(test_end-val_end)//4; end=start+max(4,(test_end-val_end)//4)
                    if fault=='spikes':corrupted.iloc[start:end:12,corrupted.columns.get_loc(target)]+=5*scale
                    elif fault=='positive_drift':corrupted.iloc[start:end,corrupted.columns.get_loc(target)]+=np.linspace(0,2*scale,end-start)
                    elif fault=='dropout':corrupted.iloc[start:end,corrupted.columns.get_loc(target)]=np.nan
                    cx=features(corrupted,target,task['extras'])
                    pred=predict(rec['method'],model,cx[cols],corrupted[target].to_numpy(),mean)
                    gated,flags=quality_fallback(corrupted,target,pred,train_end)
                    for policy,p in [('Selected',pred),('QualityFallback',gated)]:
                        stress.append(dict(task=key,fold=fold,fault=fault,policy=policy,**metrics(y[test],p[test]),
                            fallback_fraction=float(flags[test].mean()) if policy=='QualityFallback' else 0.))
        print(key,'fold',fold,'completed',flush=True)
    return results,traces,selected,stress


def telemetry(task, trigger_quantile=.9, heartbeat_minutes=180):
    """Every observation is still sensed; only uplink frequency is changed."""
    f=pd.read_csv(DATA/(task['key']+'.csv'),index_col=0,parse_dates=True)
    s=f[task['target']].to_numpy(float); N=len(s)
    val=s[int(.65*N):int(.8*N)]; delta=abs(np.diff(val)); delta=delta[np.isfinite(delta)]
    threshold=float(np.quantile(delta,trigger_quantile)); heartbeat=max(1,int(heartbeat_minutes/task['step_minutes']))
    start=int(.8*N); last=np.nan; since=heartbeat; packets=0; reconstructed=[]; truth=[]; invalid_notices=0; prev_invalid=False
    for value in s[start:]:
        since+=1
        invalid=not np.isfinite(value)
        send=bool((invalid and (not prev_invalid or since>=heartbeat)) or (not invalid and (not np.isfinite(last) or abs(value-last)>threshold or since>=heartbeat)))
        # DO-specific immediate low-reading event; not a universal species limit.
        if task['target']=='do' and np.isfinite(value) and value<3:send=True
        if send:
            packets+=1; since=0
            if invalid:invalid_notices+=1
            else:last=value
        if np.isfinite(value) and np.isfinite(last):reconstructed.append(last); truth.append(value)
        prev_invalid=invalid
    baseline=len(s)-start
    return dict(task=task['key'],threshold=threshold,heartbeat_minutes=heartbeat*task['step_minutes'],
        periodic_packets=baseline,event_packets=packets,reduction=1-packets/baseline,
        reconstruction_mae=float(np.mean(abs(np.array(truth)-np.array(reconstructed)))),invalid_notifications=invalid_notices,
        nominal_frame_bytes=32,radio_tx_joule_assumption=.1,periodic_tx_j=baseline*.1,event_tx_j=packets*.1,
        note='Assumed radio-only energy, not measured. No sensor sampling reduction or aerator saving is claimed.')


def device_context():
    output=[]
    for p in (ROOT/'data/raw/mlperf_tiny').glob('*performance*json'):
        rows=json.loads(p.read_text())
        # MLPerf tiny harness timestamps are microseconds; throughput is infer/s.
        ms=[1000/r['infer']['throughput'] for r in rows]
        out=dict(board='NUCLEO_L4R5ZI-P' if 'L4R5' in p.name else 'NUCLEO_U575ZI_Q',task='MLPerf Tiny anomaly detection (audio)',
            mean_latency_ms=float(np.mean(ms)),source_file=p.name,
            applies_to='Published external reference workload; not our water-quality model, not ESP32 timing.')
        output.append(out)
    return output


def aggregate(results,traces):
    frame=pd.DataFrame(traces)
    summary=[]
    for (task,package,method),g in frame.groupby(['task','package','method']):
        error=abs(g['prediction']-g['y'])
        daily=pd.DataFrame({'day':g['time'].str[:10],'error':error}).groupby('day')['error'].mean().to_numpy()
        boot=np.random.default_rng(SEED).choice(daily,(3000,len(daily))).mean(axis=1)
        summary.append(dict(task=task,package=package,method=method,mae=float(error.mean()),n=len(g),test_days=len(daily),
            daily_mean_mae_interval=[float(x) for x in np.quantile(boot,[.025,.975])]))
    return summary


def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    tasks=json.loads((DATA/'tasks.json').read_text())
    allrows=[];alltraces=[];allselect=[];allstress=[]
    started=time.perf_counter()
    for task in tasks:
        rows,traces,select,stress=task_benchmark(task)
        allrows+=rows;alltraces+=traces;allselect+=select;allstress+=stress
    write_csv(OUT/'model_trials.csv',allrows);write_csv(OUT/'predictions.csv',alltraces)
    write_csv(OUT/'stress_trials.csv',allstress)
    result=dict(seed=SEED,python=platform.python_version(),sklearn=sklearn.__version__,numpy=np.__version__,
        tasks=tasks,summary=aggregate(allrows,alltraces),selection=allselect,stress=allstress,
        telemetry=[telemetry(t) for t in tasks],device_context=device_context(),runtime_s=time.perf_counter()-started,
        epistemic_limit='Public observed-target prediction and injected-stream replay; no new device, field intervention or mortality trial.')
    (OUT/'benchmark_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    plot_benchmark(result)
    print('Saved benchmark_summary.json',flush=True)


def plot_benchmark(result):
    fig,axes=plt.subplots(2,2,figsize=(8,5.8))
    for ax,task in zip(axes.flat,result['tasks']):
        group=[r for r in result['summary'] if r['task']==task['key'] and r['package']=='MultiSensor']
        order=['Persistence','Mean','Ridge','Tree4','MLP8','Forest16','HistBoost']
        group=sorted(group,key=lambda r:order.index(r['method']))
        ax.barh([r['method'] for r in group],[r['mae'] for r in group],color='#287d8e')
        ax.set(title=task['key'],xlabel='MAE ('+task['unit']+')')
    fig.tight_layout();fig.savefig(OUT/'model_comparison.pdf');fig.savefig(OUT/'model_comparison.png',dpi=180)


if __name__=='__main__':main()
