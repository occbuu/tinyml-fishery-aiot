"""Frozen pH transfer and observation-context analyses; no extra model tuning."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from run_benchmark import ROOT,DATA,OUT,features,learner,metrics


def freshwater_nh3_fraction(temp_c,ph,salinity_psu=0):
    """Emerson-type zero-salinity equilibrium illustration, not a toxicity limit.

    Requires TAN expressed as nitrogen for NH3-N multiplication. No application
    to unidentified ammonia columns or brackish/marine water is allowed here.
    """
    if salinity_psu!=0:raise ValueError('A validated salinity correction is required.')
    return 1/(1+10**(.09018+2729.92/(273.15+np.asarray(temp_c))-np.asarray(ph)))


def main():
    tasks={t['key']:t for t in json.loads((DATA/'tasks.json').read_text())}
    out=[]
    for src,dst in [('pond_ph','aquaponic_ph'),('aquaponic_ph','pond_ph')]:
        a=pd.read_csv(DATA/(src+'.csv'),index_col=0,parse_dates=True)
        b=pd.read_csv(DATA/(dst+'.csv'),index_col=0,parse_dates=True)
        cols=['temperature']; ax=features(a,'ph',cols); bx=features(b,'ph',cols)
        H=6; ay=a['ph'].shift(-H); by=b['ph'].shift(-H)
        arange=np.arange(len(a));brange=np.arange(len(b))
        train=(arange<int(.65*len(a))-H)&(arange>=6)&ay.notna()&a['ph'].notna()
        test=(brange>=int(.8*len(b)))&(brange<len(b)-H)&by.notna()&b['ph'].notna()
        model=learner('Ridge').fit(ax.loc[train],ay[train])
        p=model.predict(bx.loc[test])
        for days in (0,1,3,7):
            end=b.index.min()+pd.Timedelta(days=days)
            calibration=(b.index+pd.Timedelta(minutes=30)<end)&(brange<int(.8*len(b))-H)&by.notna()&b['ph'].notna()&(brange>=6)
            if days and (end>=b.index[int(.8*len(b))] or calibration.sum()<10):continue
            correction=float((by[calibration]-model.predict(bx.loc[calibration])).mean()) if days else 0.
            out.append(dict(source=src,destination=dst,calibration_days=days,calibration_samples=int(calibration.sum()) if days else 0,
                intercept_adjustment=correction,**metrics(by[test].to_numpy(),p+correction)))
    grid=[dict(temperature_c=t,ph=p,fraction_nh3_n=float(freshwater_nh3_fraction(t,p)),salinity_psu=0)
          for t in (20,25,30,35) for p in (6.5,7,7.5,8,8.5,9)]
    result=dict(ph_transfer=out,freshwater_ammonia_sensitivity=grid,
        note='Ammonia grid is an illustrative equilibrium calculation, not field NH3 measurement. Source biochemistry labels excluded from predictive validation.')
    (OUT/'transfer_context.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
