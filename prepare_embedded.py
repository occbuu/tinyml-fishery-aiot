"""Freeze model/fixture exports for host-C verification and ESP32 simulation."""
from pathlib import Path
import json,shutil,warnings
import numpy as np
import pandas as pd
from run_benchmark import ROOT,DATA,OUT,features,learner,export_c,predict

PROJECT=ROOT/'firmware/wokwi_platformio'
METHODS=('Ridge','Mean','Persistence','Tree4','MLP8')


def literal(value):return 'NAN' if value is None or not np.isfinite(value) else f'{float(value):.9e}f'


def main():
    refs=ROOT/'firmware/c_reference';refs.mkdir(parents=True,exist_ok=True)
    cases=[];warnings_count=0
    for task in json.loads((DATA/'tasks.json').read_text()):
        key=task['key'];target=task['target'];H=task['horizon_steps']
        f=pd.read_csv(DATA/(key+'.csv'),index_col=0,parse_dates=True);x=features(f,target,task['extras'])
        y=f[target].shift(-H).to_numpy();current=f[target].to_numpy();pos=np.arange(len(f))
        train_end=int(.65*len(f));val_end=int(.8*len(f));test_end=len(f)
        eligible=np.isfinite(y)&np.isfinite(current)&(pos>=6)
        train=eligible&(pos<train_end-H);test=eligible&(pos>=val_end)&(pos<test_end-H)
        mean=float(np.mean(y[train]));a=x.loc[test].iloc[:256].copy()
        # Missing-value checks are controlled input overlays, not field faults.
        # Append 16 sequential copies, including missing target and other channels.
        overlay=a.iloc[:16].copy();overlay.iloc[::2,0]=np.nan;overlay.iloc[1::3,-1]=np.nan
        a=pd.concat([a,overlay],ignore_index=True)
        values=[[float(v) if np.isfinite(v) else None for v in row] for row in a.to_numpy()]
        selected=json.loads((OUT/(key+'_export_reference.json')).read_text())['selected_method']
        for method in METHODS:
            model=None
            if method not in ('Mean','Persistence'):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');model=learner(method).fit(x.loc[train],y[train])
                warnings_count+=len(caught)
            header=refs/(key+'_'+method+'.h');export_c(model,method,list(x),header,mean)
            expected=predict(method,model,a,a.iloc[:,0].to_numpy(),mean)
            case=dict(key=key,method=method,features=list(x),inputs=values,
                      expected=[float(v) for v in expected],header=header.relative_to(ROOT).as_posix(),
                      tolerance_absolute=2e-4,tolerance_relative=2e-5,
                      note='Float32 C output versus sklearn/Python; test-prefix inputs plus declared missing-input overlays, not new accuracy evaluation.')
            cases.append(case)
            if method in ('Ridge','Tree4','MLP8'):
                shutil.copy2(header,ROOT/f'firmware/generated/{key}_{method}.h')
            if method==selected:shutil.copy2(header,ROOT/f'firmware/generated/{key}.h')
    (OUT/'c_reference_cases.json').write_text(json.dumps(dict(cases=cases,fit_warnings=warnings_count),indent=2,allow_nan=False))
    inc=PROJECT/'include';inc.mkdir(parents=True,exist_ok=True)
    pond=[c for c in cases if c['key']=='pond_ph']
    names=('Ridge','Mean','Persistence','Tree4')
    for name in names:shutil.copy2(refs/('pond_ph_'+name+'.h'),inc/(name+'.h'))
    base=pond[0];n=len(base['inputs']);p=len(base['features'])
    lines=['// Generated fixture replay; do not call these synthetic overlays new pond measurements.','#pragma once','#include <math.h>',
           f'#define REPLAY_ROWS {n}',f'#define REPLAY_INPUTS {p}',
           f'static const float replay_inputs[{n}][{p}]={{']
    lines+=['{'+','.join(literal(v) for v in row)+'},' for row in base['inputs']];lines+=['};',f'static const float replay_expected[{n}][4]={{']
    for i in range(n):lines.append('{'+','.join(literal(next(c for c in pond if c['method']==name)['expected'][i]) for name in names)+'},')
    lines+=['};'];(inc/'replay_fixture.h').write_text('\n'.join(lines),encoding='utf-8')
    print('Exported',len(cases),'C references and',n,'ESP32 replay inputs.')


if __name__=='__main__':main()
