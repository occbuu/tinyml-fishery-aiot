"""Vector diagrams and descriptive biochemistry; no hardware timing invented."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.dates as mdates
from vietnam_benchmark import load_vibrio

ROOT=Path(__file__).resolve().parent
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'


def daily_traces():
    d=pd.read_csv(ROOT/'data/processed/vietnam_daily.csv',parse_dates=['date'])
    cut=pd.Timestamp('2018-06-04');ponds=sorted(d.pond.unique());colors={p:plt.get_cmap('tab10')(i) for i,p in enumerate(ponds)}
    fig,axes=plt.subplots(1,2,figsize=(9,3.7));rows=[]
    for ax,year in zip(axes,[2018,2019]):
        year_data=d[d.year==year]
        if year==2018:
            ax.axvspan(year_data.date.min(),cut,color='#dcecf5');ax.axvspan(cut,year_data.date.max(),color='#fff0cc');ax.axvline(cut,c='gray',ls=':',lw=.8)
        else:ax.axvspan(year_data.date.min(),year_data.date.max(),color='#eeeeee')
        for pond,g in year_data.groupby('pond',sort=True):
            g=g.sort_values('date');ax.plot(g.date,g.ph,'o-',ms=2,lw=.8,color=colors[pond],label=pond)
            unusual=g.ph.notna() & ~g.ph.between(4,11)
            ax.scatter(g.loc[unusual,'date'],g.loc[unusual,'ph'],s=55,facecolors='none',edgecolors='red',linewidths=.8)
            pairs=pd.DataFrame(dict(current=g.ph,previous=g.ph.shift(1))).dropna()
            rows.append(dict(year=year,pond=pond,observed_n=int(g.ph.notna().sum()),adjacent_pair_n=len(pairs),
                             lag1_pearson=float(pairs.current.corr(pairs.previous)),mean_absolute_daily_change=float(abs(pairs.current-pairs.previous).mean())))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'));ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3,maxticks=5))
        low=max(0,float(np.floor(year_data.ph.min()*2)/2-.5));high=min(14,float(np.ceil(year_data.ph.max()*2)/2+.5))
        ax.tick_params(axis='x',labelsize=8);ax.set(title='2018: train / validation' if year==2018 else '2019: frozen test',xlabel='Recorded calendar date',ylabel='Observed pH',ylim=(low,high));ax.grid(alpha=.2)
    axes[1].legend(ncol=3,fontsize=8,loc='lower right');fig.tight_layout();fig.savefig(PAPER/'figures/vietnam_ph_traces.pdf');plt.close(fig)
    pd.DataFrame(rows).to_csv(ROOT/'results/vietnam_ph_trace_diagnostics.csv',index=False)
    return rows


def box(ax,x,y,w,h,text,color='#e7f0f7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.012',facecolor=color,edgecolor='#34536d'))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9)


def pipeline():
    fig,ax=plt.subplots(figsize=(9,4.7));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(.5,.97,'Recorded crop-year evaluation and resource selection',ha='center',fontsize=12,weight='bold')
    box(ax,.03,.67,.26,.17,'2018 early dates\nTraining only\n324 eligible pH labels')
    box(ax,.37,.67,.26,.17,'2018 validation\nStarts 4 June\n77 eligible pH labels')
    box(ax,.71,.67,.26,.17,'2019 frozen test\n468 pH forecasts\nSix recorded pond labels')
    for a,b in [(.29,.37),(.63,.71)]:ax.annotate('',xy=(b,.755),xytext=(a,.755),arrowprops=dict(arrowstyle='->',lw=1.4))
    ax.text(.33,.57,'Purge labels\ncrossing boundary',ha='center',fontsize=8)
    ax.text(.67,.57,'Freeze fit, preprocessing\nand validation selector',ha='center',fontsize=8)
    box(ax,.03,.25,.26,.17,'Fixed comparator fits\nTrain-only imputation\nand scaling')
    box(ax,.37,.25,.26,.17,'Eligible parameter payload\nHistorical: <=4,096 B\nNot the ESP32 RAM limit')
    box(ax,.71,.25,.26,.17,'Validation MAE only\nSmallest within +5%\nNo test-based reselection')
    for a,b in [(.29,.37),(.63,.71)]:ax.annotate('',xy=(b,.335),xytext=(a,.335),arrowprops=dict(arrowstyle='->',lw=1.4))
    ax.text(.5,.075,'Separate Vibrio task: train 2022–2023 / validate 2024 / test 2025.\nBudget sensitivity 512 B–16 KiB uses the same frozen fitted models.',ha='center',fontsize=9)
    fig.savefig(PAPER/'figures/temporal_memory_pipeline.pdf',bbox_inches='tight');plt.close(fig)


def biochemistry():
    d,censor=load_vibrio('half')
    cols=['Temp','pH','DO','Sal','Alk','N-NO2-','N-NH4+','P-PO43-','TSS','COD','response']
    labels=['Temp','pH','DO','Salinity','Alkalinity','Nitrite-N','Ammonium-N','Phosphate-P','TSS','COD','Vibrio log+1']
    corr=d[cols].corr(method='spearman');valid=d[cols].notna().astype(int);n=valid.T@valid
    target=pd.DataFrame(dict(variable=cols[:-1],spearman=corr.loc[cols[:-1],'response'].to_numpy(),
                             pearson=d[cols].corr(method='pearson').loc[cols[:-1],'response'].to_numpy(),n=n.loc[cols[:-1],'response'].to_numpy()))
    target.to_csv(ROOT/'results/vibrio_target_associations.csv',index=False)
    corr.to_csv(ROOT/'results/vibrio_spearman.csv');n.to_csv(ROOT/'results/vibrio_spearman_pair_counts.csv')
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,5),gridspec_kw={'width_ratios':[1.6,1]})
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r');ax.set_xticks(range(len(labels)),labels,rotation=65,ha='right',fontsize=8);ax.set_yticks(range(len(labels)),labels,fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):ax.text(j,i,f'{corr.iloc[i,j]:.1f}',ha='center',va='center',fontsize=6,color='white' if abs(corr.iloc[i,j])>.65 else 'black')
    ax.set_title('Pooled descriptive Spearman correlation\n679 records; pairwise nonmissing observations',fontsize=10);fig.colorbar(im,ax=ax,shrink=.7,label='Spearman rho')
    years=sorted(d.Year.unique());data=[d.loc[d.Year==year,'response'].to_numpy() for year in years]
    bx.boxplot(data,tick_labels=[f'{y}\nn={len(a)}' for y,a in zip(years,data)],showfliers=True)
    bx.set(ylabel='Total Vibrio: log10(CFU/mL + 1)',title='Observed distribution by recorded year');bx.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(PAPER/'figures/vibrio_biochemistry.pdf');plt.close(fig)
    return dict(rows=len(d),censor=censor,min_pair_n=int(n.to_numpy().min()),max_pair_n=int(n.to_numpy().max()),target_associations=target.to_dict('records'),
                scope='Post-hoc descriptive EDA including held-out years; not used to fit/select features, tune thresholds or infer causal effects. Half-LOQ substitution; no persistent pond IDs.')


def firmware():
    fig,ax=plt.subplots(figsize=(9,4.6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(.5,.96,'Implemented firmware replay and separate host telemetry experiment',ha='center',fontsize=12,weight='bold')
    box(ax,.025,.68,.28,.15,'ESP32 setup(): replay fixture\nReset model; C parity check\nSerial: REPLAY_PASS / FAIL')
    box(ax,.36,.68,.28,.15,'Warm-up, then 40 blocks\n1,000 predictions per block\nUART / ADC outside timing')
    box(ax,.695,.68,.28,.15,'Heap / stack instrumentation\nSerial output hooks\nNo executed runtime evidence')
    for a,b in [(.305,.36),(.64,.695)]:ax.annotate('',xy=(b,.755),xytext=(a,.755),arrowprops=dict(arrowstyle='->',lw=1.4))
    box(ax,.025,.32,.45,.17,'ESP32 loop(): virtual ADC + invalid button\nPrint protection request; 1 s delay\nNo physical DO probe, relay or aerator')
    box(ax,.535,.32,.44,.17,'Separate Python telemetry replay\nQuantile trigger + heartbeat + invalid state\nPacket / reconstruction accounting')
    ax.text(.5,.105,'No dual-core task pinning, Modbus, LoRaWAN radio stack or deep-sleep integration is claimed.\nHost replay and cross-build evidence are distinct from physical runtime measurements.',ha='center',fontsize=9)
    fig.savefig(PAPER/'figures/firmware_evidence_flow.pdf',bbox_inches='tight');plt.close(fig)


def hardware_table():
    from analyze_reporting import tex_table
    builds=json.loads((ROOT/'results/esp32_build_summary.json').read_text())
    models={r['method']:r for r in builds['rows']}
    rows=[]
    for model in ['Persistence','Mean','Ridge','Tree4','MLP8','Forest16']:
        r=models.get(model)
        flash=str(r['linked_flash_sections_bytes']) if r else '--'
        ram=str(r['static_data_bss_bytes']) if r else '--'
        rows.append(f'{model} & {flash} & {ram} & -- & -- & --')
    tex_table('hardware_evidence_status.tex','lrrrrr',r'Model & Linked flash (B) & Static RAM (B) & Peak SRAM & Latency & Energy',rows)


def main():
    pipeline();summary=biochemistry();summary['daily_ph_traces']=daily_traces();firmware();hardware_table()
    (ROOT/'results/research_visuals_summary.json').write_text(json.dumps(summary,indent=2))
    print('Temporal pipeline, descriptive chemistry, implemented firmware flow and hardware evidence table exported.')


if __name__=='__main__':main()
