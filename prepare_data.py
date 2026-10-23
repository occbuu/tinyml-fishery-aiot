"""Read-only extraction of source spreadsheets; causal aligned CSV intermediates.

Use the bundled Python runtime for pandas/openpyxl source extraction. Native
observed targets are never imputed. Raw files are retained byte-for-byte.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'data/raw'; OUT=ROOT/'data/processed'
OUT.mkdir(parents=True,exist_ok=True)


def align(frame,time_col,freq,columns,bounds):
    time=pd.to_datetime(frame[time_col],errors='coerce')
    data=frame[list(columns)].apply(pd.to_numeric,errors='coerce').rename(columns=columns)
    data.index=time
    data=data[~data.index.isna()].sort_index()
    invalid={}
    for col,(low,high) in bounds.items():
        bad=(data[col]<low)|(data[col]>high)
        invalid[col]=int(bad.sum()); data.loc[bad,col]=np.nan
    # Right-closed bins are labelled by their end: every constituent observation
    # is in the past at the forecast origin. No centered filter or interpolation.
    binned=data.resample(freq,closed='right',label='right').median()
    return binned,dict(raw_rows=len(frame),invalid_counts=invalid,grid_rows=len(binned),
        observed_per_column={c:int(binned[c].notna().sum()) for c in binned},
        start=str(binned.index.min()),end=str(binned.index.max()))


def main():
    audit=[]; tasks=[]
    def save(key,frame,stats,target,unit,minutes,horizon,source,extras):
        frame.index.name='time'; frame.to_csv(OUT/(key+'.csv'))
        stats.update(key=key,source=source,target=target,unit=unit,step_minutes=minutes,horizon_steps=horizon,extras=extras)
        audit.append(stats); tasks.append({k:stats[k] for k in ('key','source','target','unit','step_minutes','horizon_steps','extras')})
    d=pd.read_excel(RAW/'tilapia_colombia/Monteria_Aquaculture_Data.xlsx')
    f,a=align(d,'DateTime','1h',{'Dissolved_Oxygen':'do','Temperature':'temperature','pH':'ph','Turbidity':'turbidity'},
              {'do':(0,25),'temperature':(0,45),'ph':(0,14),'turbidity':(0,5000)})
    save('tilapia_do',f,a,'do','mg/L',60,1,'10.17632/dgdr2kfbyt.1',['temperature','ph','turbidity'])
    d=pd.read_excel(RAW/'bangladesh_depth/Sensor data for 30 cm.xlsx')
    f,a=align(d,d.columns[0],'5min',{d.columns[1]:'temperature',d.columns[2]:'ph',d.columns[3]:'turbidity'},
              {'temperature':(0,45),'ph':(0,14),'turbidity':(0,5000)})
    lower=pd.read_excel(RAW/'bangladesh_depth/Sensor data for 60 cm.xlsx')
    low,_=align(lower,lower.columns[0],'5min',{lower.columns[1]:'bottom_temperature',lower.columns[2]:'bottom_turbidity'},
                {'bottom_temperature':(0,45),'bottom_turbidity':(0,5000)})
    f=f.join(low)
    save('pond_ph',f,a,'ph','pH units',5,6,'10.17632/34rczh25kc.4',['temperature','turbidity','bottom_temperature'])
    d=pd.read_csv(RAW/'aquaponic_esp8266/pond_iot_2023_raw.csv')
    f,a=align(d,'created_date','5min',{'water_pH':'ph','TDS':'tds','water_temp':'temperature'},
              {'ph':(0,14),'tds':(0,10000),'temperature':(0,45)})
    save('aquaponic_ph',f,a,'ph','pH units',5,6,'10.17632/yd36bx6f8f.2',['temperature','tds'])
    d=pd.read_csv(RAW/'marine_macehead/macehead_2019_may_july.csv',skiprows=[1])
    # Oxygen is QC=0 (unreviewed) throughout this slice. Exclude it as target or
    # feature in the primary benchmark rather than call it validated reference DO.
    for name in ('temperature','salinity'):
        d.loc[~d[name+'_qc'].isin([1,2]),name]=np.nan
    f,a=align(d,'time','30min',{'temperature':'temperature','salinity':'salinity'},
              {'temperature':(-3,45),'salinity':(0,45)})
    a['oxygen_qc_counts']={str(k):int(v) for k,v in d['oxygen_qc'].value_counts().items()}
    a['oxygen_excluded_reason']='All oxygen flags are 0 (no_quality_control); no validated DO test from this slice.'
    save('marine_temperature',f,a,'temperature','degC',30,2,'Marine Institute sbe37_macehead, 2019-05 to 2019-07',['salinity'])
    # Biochemistry is a threshold-constructed table, not a time-stamped field series.
    b=pd.read_excel(RAW/'biochemistry/WQD.xlsx')
    audit.append(dict(key='biochemistry_inventory',raw_rows=len(b),columns=list(b.columns),
        invalid_temperature_if_celsius=int(((b['Temp']<0)|(b['Temp']>45)).sum()),
        use='Inventory and provenance stress audit only; exclude threshold-derived quality labels from predictive validation.',
        source='10.17632/y78ty2g293.1',ammonia_basis='Ammonia unit basis (TAN-N vs NH3) unverified; no free-ammonia conversion.'))
    old=pd.read_excel(RAW/'colombia_pond/Data IoTMLCQ.xlsx')
    audit.append(dict(key='related_transformed_colombia',raw_rows=len(old),columns=list(old.columns),
        use='Excluded: mixed scaled/unscaled features, no complete DateTime; not an independent replication of Monteria.'))
    (OUT/'tasks.json').write_text(json.dumps(tasks,indent=2))
    (OUT/'data_audit.json').write_text(json.dumps(audit,indent=2))
    for r in audit:print(r)


if __name__=='__main__':main()
