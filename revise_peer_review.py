"""Reproducible additional diagnostics; leaves original held-out selection intact."""
from pathlib import Path
from artifact_paths import ASSETS
import json, re, shutil, urllib.request, concurrent.futures, html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from vietnam_benchmark import daily_design, fit_and_predict

ROOT=Path(__file__).resolve().parent
P=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
OUT=ROOT/'results/peer_review_20261030'
OUT.mkdir(exist_ok=True)

def diagnostics():
    frame=pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date'])
    d=daily_design(frame,'ph','TargetOnly')
    cols=[c for c in d if c not in ('label','current','date','label_date','year','pond','series')]
    dates=np.sort(d.loc[d.year==2018,'date'].unique()); rows=[]
    for a,b in ((.40,.55),(.55,.70),(.70,.85),(.85,1.0)):
        cut=pd.Timestamp(dates[int(a*len(dates))])
        end=pd.Timestamp(dates[int(b*len(dates))]) if b<1 else pd.Timestamp(dates[-1])+pd.Timedelta(days=2)
        tr=d.label.notna()&(d.year==2018)&(d.label_date<cut)
        va=d.label.notna()&(d.year==2018)&(d.date>=cut)&(d.label_date<end)
        for name in ('Mean','Persistence','Ridge','Tree4','Forest16'):
            _,pred,_=fit_and_predict(name,d.loc[tr,cols],d.loc[tr,'label'],[d.loc[va,cols]],[d.loc[va,'current']])
            rows.append(dict(origin=str(cut.date()),end=str(end.date()),method=name,train_n=int(tr.sum()),validation_n=int(va.sum()),mae=float(np.abs(d.loc[va,'label']-pred[0]).mean())))
    r=pd.DataFrame(rows);r.to_csv(OUT/'rolling_origin_2018.csv',index=False)
    tab=r.pivot(index='origin',columns='method',values='mae')
    text='\\begin{tabular}{lrrrrr}\\toprule\nOrigin & Mean & Persistence & Ridge & Tree4 & Forest16\\\\\\midrule\n'
    for idx,row in tab.iterrows():text+=idx+' & '+' & '.join(f'{row[n]:.4f}' for n in ('Mean','Persistence','Ridge','Tree4','Forest16'))+'\\\\\n'
    text+='\\bottomrule\\end{tabular}\n'
    (ASSETS/'tables/rolling_origin.tex').write_text(text)
    x=pd.read_csv(ROOT/'results/vietnam_daily_predictions.csv')
    x=x[(x.task=='ph')&(x.package=='TargetOnly')]
    fig,axs=plt.subplots(1,2,figsize=(10,3.4),layout='constrained')
    for name,col in [('Persistence','#176b91'),('Ridge','#c06522')]:
        s=x[x.method==name].copy();s['residual']=s.prediction-s.label
        g=s.groupby('pond').apply(lambda z:np.abs(z.residual).mean(),include_groups=False)
        axs[0].plot(g.index,g.values,'o-',label=name,color=col)
        axs[1].hist(s.residual,bins=np.linspace(-1,1,35),histtype='step',label=name,color=col)
    axs[0].set(ylabel='MAE (pH units)',xlabel='2019 pond label')
    axs[1].set(xlabel='Prediction minus observation (pH units)',ylabel='Forecast count')
    for ax in axs:ax.legend(frameon=False);ax.grid(alpha=.2)
    fig.savefig(P/'figures/ph_residual_diagnostics.pdf');plt.close(fig)
    print(r.to_string(index=False))

def bibliography():
    if (P/"manuscript.tex").exists() and (P/"references.bib").exists():
        print("Retaining curated references.bib and the two canonical sources")
        return
    # Prefer the already verified local DOI metadata over another manual transcription.
    local=(ROOT.parent/'Paper1_FisheryAIoT_V3/references.bib').read_text(encoding='utf-8')
    blocks=re.split(r'(?=@\w+\{)',local)[1:]
    old='\n'.join((P/f).read_text(encoding='utf-8') for f in ('main_references.tex','supplementary_references.tex'))
    entries=dict(re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})',old,re.S))
    cache=OUT/'doi_metadata';cache.mkdir(exist_ok=True)
    def one(item):
        k,body=item;m=re.search(r'https://doi.org/([^}\s]+)',body)
        if m:
            doi=m[1]
            match=next((z for z in blocks if doi.lower() in z.lower()),None)
            if match:return re.sub(r'(@\w+\{)[^,]+',lambda a:a[1]+k,match,count=1).strip()
            dest=cache/(k+'.bib')
            if not dest.exists():
                req=urllib.request.Request('https://doi.org/'+doi,headers={'Accept':'application/x-bibtex','User-Agent':'Academic-manuscript-metadata/1.0'})
                try:
                    data=urllib.request.urlopen(req,timeout=40).read().decode('utf-8')
                    if not data.lstrip().startswith('@'):raise ValueError('Not BibTeX')
                    dest.write_text(data,encoding='utf-8')
                except Exception as e:
                    print('METADATA PENDING',k,str(e));return None
            return re.sub(r'(@\w+\{)[^,]+',lambda a:a[1]+k,dest.read_text(encoding='utf-8'),count=1)
        # Preserve identifiable corporate/preprint records with source descriptions.
        plain=re.sub(r'\\url\{([^}]+)\}',r'\1',body)
        url=re.search(r'https?://[^\s}]+',plain)
        label=plain[:url.start()].strip() if url else plain.strip()
        return '@misc{'+k+',\n title = {{'+label.replace('&',r'\&')+'}},\n'+(' url = {'+url[0]+'},\n' if url else '')+' note = {Source description retained from archived bibliography}\n}'
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(one,entries.items()))
    missing=[k for (k,_),v in zip(entries.items(),results) if v is None]
    (OUT/'bibliography_pending.json').write_text(json.dumps(missing))
    if missing:raise RuntimeError('Unresolved DOI metadata: '+str(missing))
    content=html.unescape('\n\n'.join(results))
    content=re.sub(r'(?<!\\)&',r'\\&',content)
    content=re.sub(r'\bmonth\s*=\s*sept\b','month = sep',content,flags=re.I)
    content=re.sub(r'\bmonth\s*=\s*july\b','month = jul',content,flags=re.I)
    content=content.replace('\u2019',"'").replace('\u2013','--').replace('\u2212','-')
    (P/'references.bib').write_text('% DOI metadata reused from verified local library or resolved through doi.org, 2026-10-30.\n\n'+content,encoding='utf-8')
    for filename in ('main.tex','supplementary.tex'):
        dest=P/filename;s=dest.read_text(encoding='utf-8')
        s=re.sub(r'\\input\{(?:main|supplementary)_references.tex\}',r'\\bibliographystyle{IEEEtran}\n\\bibliography{references}',s)
        dest.write_text(s,encoding='utf-8')

if __name__=='__main__':
    diagnostics()
    bibliography()
