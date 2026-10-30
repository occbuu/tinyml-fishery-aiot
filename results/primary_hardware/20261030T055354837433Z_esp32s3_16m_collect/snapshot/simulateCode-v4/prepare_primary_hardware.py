"""Export frozen Vietnamese primary models, with complete held-out replay cases."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from vietnam_benchmark import daily_design,daily_masks,fit_and_predict,load_vibrio
from run_benchmark import export_c,parameter_bytes

ROOT=Path(__file__).resolve().parent
HW=ROOT/'firmware/primary_hardware'
OUT=ROOT/'results/primary_hardware'

def export_primary_forest(model,path):
    """Preserve sklearn's double transform -> float32 tree input -> double split.

    A float32 threshold can move a midpoint onto an input value and change a
    branch. This export preserves transform/split precision; it is distinct
    from the historical all-float32 node-payload estimate.
    """
    lines=['#pragma once']
    for name,values in [('median',model[0].statistics_),('center',model[1].mean_),('scale',model[1].scale_)]:
        lines.append('static const double '+name+'[]={'+','.join(format(float(v),'.17g') for v in values)+'};')
    n=len(model[0].statistics_)
    lines.append('static void model_reset() {}')
    lines.append(f'static float model_predict(const double* raw) {{ float x[{n}];')
    lines.append(f'for(int i=0;i<{n};i++) x[i]=(float)(((isfinite(raw[i])?raw[i]:median[i])-center[i])/scale[i]);')
    lines.append('double total=0;')
    for estimator in model[-1].estimators_:
        tree=estimator.tree_
        def node(k):
            if tree.children_left[k]<0:return 'total+='+format(float(tree.value[k,0,0]),'.17g')+';'
            return f'if((double)x[{tree.feature[k]}]<={float(tree.threshold[k]):.17g}){{'+node(tree.children_left[k])+'}else{'+node(tree.children_right[k])+'}'
        lines.append('{'+node(0)+'}')
    lines.append(f'return (float)(total/{len(model[-1].estimators_):.1f}); }}')
    path.write_text('\n'.join(lines),encoding='utf-8')

def main():
    inc=HW/'include';inc.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
    d=daily_design(pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date']),'ph','TargetOnly')
    tr,va,te,cut=daily_masks(d)
    cols=[c for c in d if c not in ('label','current','date','label_date','year','pond','series')]
    specs=[]
    for method in ['Persistence','Ridge','Forest16']:
        specs.append(('ph_'+method,method,d.loc[tr,cols],d.loc[tr,'label'],d.loc[te,cols],d.loc[te,'current'],d.loc[te,['date','label_date','pond','label']].astype(str).to_dict('records')))
    v,_=load_vibrio('half');cols_v=['Temp','pH','DO','Sal','Alk','N-NO2-','N-NH4+','P-PO43-','TSS','COD']
    for method in ['Mean','Forest16']:
        specs.append(('vibrio_'+method,method,v.loc[v.Year.isin([2022,2023]),cols_v],v.loc[v.Year.isin([2022,2023]),'response'],v.loc[v.Year==2025,cols_v],None,[{'source_row':int(i)+2,'date':str(v.loc[i,'Date'].date())} for i in v.index[v.Year==2025]]))
    cases=[];models=[];includes=['#pragma once','#include <math.h>']
    for index,(key,method,x,y,test,current,metadata) in enumerate(specs):
        model,pred,_=fit_and_predict(method,x,y,[test],[current] if current is not None else None)
        mean=float(y.mean());header=inc/(key+'.h');export_c(model,method,list(x),header,mean)
        if method=='Forest16':export_primary_forest(model,header)
        raw=test.to_numpy(float)
        # Persistence consumes the same causally available reading as the benchmark.
        if method=='Persistence':raw[:,0]=np.asarray(current)
        archive=pd.read_csv(ROOT/'results'/('vietnam_daily_predictions.csv' if key.startswith('ph_') else 'vietnam_vibrio_predictions.csv'))
        archive=archive[(archive.method==method)&(archive.package==('TargetOnly' if key.startswith('ph_') else 'Laboratory10'))]
        if key.startswith('ph_'):archive=archive[archive.task=='ph']
        assert len(archive)==len(raw)
        assert np.allclose(archive.prediction,pred[0],rtol=0,atol=1e-12),'Frozen prediction drift'
        models.append(dict(id=index,key=key,method=method,features=list(x),train_n=len(x),test_n=len(raw),parameter_bytes=parameter_bytes(model,method),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest()))
        includes.extend([f'namespace m{index} {{',f'#include "{key}.h"','#undef MODEL_INPUTS','}'])
        for i,(row,expected,meta) in enumerate(zip(raw,pred[0],metadata)):
            cases.append(dict(id=len(cases),model=index,key=key,row=i,inputs=[float(z) if np.isfinite(z) else None for z in row],expected=float(expected),metadata=meta))
    includes+=['__attribute__((noinline)) static float dispatch(int model,const double* x) { float f[10]; for(int i=0;i<10;i++)f[i]=(float)x[i]; switch(model) {']
    includes += [f'case {m["id"]}:return m{m["id"]}::model_predict('+('x' if m['method']=='Forest16' else 'f')+');' for m in models]
    includes+=['default:return NAN;} }','static void reset_models() {']+[f'm{m["id"]}::model_reset();' for m in models]+['}']
    (inc/'models.h').write_text('\n'.join(includes),encoding='utf-8')
    fixture=dict(models=models,cases=cases,batch_calls=64,tolerance_absolute=2e-4,tolerance_relative=2e-5,precision='Forests preserve double preprocessing constants, raw inputs, split thresholds and leaf accumulation, with float32 transformed tree inputs and output; other models use float32. Unrolled code is not the historical 16-byte/node payload representation.',scope='Host-prepared causal features; imputation/scaling/inference onboard. Timing includes dispatch, conversion, optimizer barrier and volatile sink. No sensor, feature-generation, RF or energy measurement. Timings are per-call means of 64-call batches on each held-out input, not single-call samples.')
    (OUT/'fixture.json').write_text(json.dumps(fixture,indent=2,allow_nan=False),encoding='utf-8')
    print('Exported',len(models),'models,',len(cases),'held-out model/input pairs; archived predictions identical')

if __name__=='__main__':main()
