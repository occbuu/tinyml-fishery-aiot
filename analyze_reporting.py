"""Post-review reporting sensitivities; original test splits/fits remain frozen."""
from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_benchmark import telemetry,SEED

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'


def select_at_budget(rows,budget,tolerance=.05):
    allowed=[r for r in rows if r['parameter_bytes'] is not None and r['parameter_bytes']<=budget]
    best=min(r['validation_mae'] for r in allowed)
    return min((r for r in allowed if r['validation_mae']<=best*(1+tolerance)),
               key=lambda r:(r['parameter_bytes'],r['validation_mae'],r['method']))


def tex_table(name,columns,header,rows):
    lines=[r'\begin{tabular}{'+columns+'}',r'\toprule',header+r' \\',r'\midrule']
    lines += [r+r' \\' for r in rows]
    lines += [r'\bottomrule',r'\end{tabular}']
    (PAPER/'tables'/name).write_text('\n'.join(lines),encoding='utf-8')


def paired_ph_comparison(predictions):
    """Resample paired whole pond-label sequences; enumerate all 6**6 draws.

    Preserve original forecast weighting rather than averaging unequal-size
    pond MAEs. Joining by origin/target dates prevents accidental row pairing.
    """
    ph=predictions[(predictions.task=='ph')&(predictions.package=='TargetOnly')]
    keys=['pond','date','label_date']
    ridge=ph[ph.method=='Ridge'][keys+['label','prediction']]
    persistence=ph[ph.method=='Persistence'][keys+['label','prediction']]
    g=ridge.merge(persistence,on=keys,suffixes=('_ridge','_persistence'),validate='one_to_one')
    if len(g)!=len(ridge) or len(g)!=len(persistence):
        raise ValueError('Unmatched forecast origins in paired pH comparison')
    if not np.allclose(g.label_ridge,g.label_persistence,rtol=0,atol=0):
        raise ValueError('Paired pH observations differ')
    g['ridge_error']=abs(g.prediction_ridge-g.label_ridge)
    g['persistence_error']=abs(g.prediction_persistence-g.label_persistence)
    g['difference']=g.ridge_error-g.persistence_error
    ponds=[]
    for pond,group in g.groupby('pond',sort=True):
        ponds.append(dict(pond=pond,n=len(group),ridge_mae=float(group.ridge_error.mean()),
                          persistence_mae=float(group.persistence_error.mean()),
                          difference_mean=float(group.difference.mean()),difference_sum=float(group.difference.sum())))
    # Full enumeration avoids Monte Carlo uncertainty for this small cluster set.
    indices=np.asarray(list(itertools.product(range(len(ponds)),repeat=len(ponds))))
    sums=np.array([p['difference_sum'] for p in ponds]);counts=np.array([p['n'] for p in ponds])
    bootstrap=sums[indices].sum(axis=1)/counts[indices].sum(axis=1)
    low,high=np.quantile(bootstrap,[.025,.975])
    return dict(n=len(g),pond_labels=len(ponds),difference_mean=float(g.difference.mean()),
                paired_pond_bootstrap_ci95=[float(low),float(high)],
                resamples=len(indices),bootstrap='Exact enumeration of ordered whole-pond resamples with replacement; forecast-count weighted MAE difference.',
                contrast='TargetOnly Ridge minus Persistence absolute error, 2019; descriptive, not national population inference.',
                per_pond=ponds)


def main():
    original=json.loads((OUT/'vietnam_summary.json').read_text(encoding='utf-8'))
    ph_pair=paired_ph_comparison(pd.read_csv(OUT/'vietnam_daily_predictions.csv'))
    base=[r for r in original['vibrio']['trials'] if r['censor']=='half']
    sensitivity=[]
    for package in ('Field4','Field5','Laboratory10'):
        rows=[r for r in base if r['package']==package]
        for budget in (512,1024,2048,4096,8192,16384):
            for tolerance in (0.,.05,.10):
                pick=select_at_budget(rows,budget,tolerance)
                sensitivity.append(dict(package=package,budget_bytes=budget,tolerance=tolerance,**{k:pick[k] for k in ('method','parameter_bytes','validation_mae','test_mae')}))
    pred=pd.read_csv(OUT/'vietnam_vibrio_predictions.csv')
    g=pred[pred.package=='Laboratory10'].pivot(index=['source_row','date'],columns='method',values=['observed','prediction'])
    difference=abs(g['prediction']['Forest16']-g['observed']['Forest16'])-abs(g['prediction']['Mean']-g['observed']['Mean'])
    per_date=difference.groupby(level='date').agg(['sum','count'])
    rng=np.random.default_rng(SEED+900);boot=[]
    for _ in range(5000):
        sample=per_date.iloc[rng.integers(0,len(per_date),len(per_date))]
        boot.append(float(sample['sum'].sum()/sample['count'].sum()))
    forest=next(r for r in base if r['package']=='Laboratory10' and r['method']=='Forest16')
    mean=next(r for r in base if r['package']=='Laboratory10' and r['method']=='Mean')
    comparison=dict(package='Laboratory10',forest=forest,mean=mean,
                    paired_test_mae_difference=float(difference.mean()),date_blocks=len(per_date),
                    date_bootstrap_ci95=[float(x) for x in np.quantile(boot,[.025,.975])],
                    shifted_count_geometric_fold_error=float(10**forest['test_mae']),
                    scope='Descriptive date-block bootstrap; pond identities absent. Fold error uses CFU/mL + 1, not clinical error or a per-sample bound.')
    tasks=json.loads((ROOT/'data/processed/tasks.json').read_text())
    telemetry_grid=[]
    for task in tasks:
        for q in (.5,.75,.9,.95):
            for hb in (60,180,360):
                telemetry_grid.append(dict(trigger_quantile=q,**telemetry(task,q,hb)))
    result=dict(analysis_type='Post-review sensitivity of fixed fitted models and declared policies; not retuning the primary selector on test.',
                ph_paired_comparison=ph_pair,
                budgets=sensitivity,vibrio_comparison=comparison,telemetry_sensitivity=telemetry_grid,
                daily_do_status='Source workbook unit unresolved; exclude from primary physiological and numerical-accuracy claims; native-scale analysis retained in Supplement.',
                primary_endpoint='Next-day Vietnamese pH and simultaneous total-Vibrio log count')
    (OUT/'reporting_sensitivity.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    rows=[f"{p['pond']} & {p['n']} & {p['ridge_mae']:.4f} & {p['persistence_mae']:.4f} & {p['difference_mean']:.4f}" for p in ph_pair['per_pond']]
    tex_table('vietnam_ph_paired.tex','lrrrr',r'Pond label & Forecasts & Ridge MAE & Persistence MAE & Paired difference',rows)
    lo,hi=ph_pair['paired_pond_bootstrap_ci95']
    (PAPER/'tables/vietnam_ph_paired_findings.tex').write_text(
        f"The paired Ridge-minus-persistence test MAE difference is {ph_pair['difference_mean']:.4f} pH units, "
        f"with a descriptive whole-pond bootstrap interval of {lo:.4f} to {hi:.4f}. "
        f"All {ph_pair['resamples']:,} ordered resamples of the six pond-label sequences are enumerated, "
        "preserving matched origins and their forecast-count weights. This interval describes the recorded labels; "
        "it does not establish an advantage across independent farms or later years.",encoding='utf-8')
    lines=[]
    for task in tasks:
        name=task['key']
        group=[x for x in telemetry_grid if x['task']==name]
        if not group:continue
        lines.append(f"{name.replace('_', ' ')} & {100*min(x['reduction'] for x in group):.1f}--{100*max(x['reduction'] for x in group):.1f} & {min(x['reconstruction_mae'] for x in group):.4f}--{max(x['reconstruction_mae'] for x in group):.4f}")
    tex_table('telemetry_sensitivity.tex','lrr',r'Task & Packet reduction (\%) & Reconstruction MAE range',lines)
    rows=[]
    for name in ('Mean','Ridge','Tree4','Forest16','MLP8','HistBoost'):
        r=next(x for x in base if x['package']=='Laboratory10' and x['method']==name)
        b='--' if r['parameter_bytes'] is None else str(r['parameter_bytes'])
        eligible='No export' if r['parameter_bytes'] is None else 'Yes' if r['parameter_bytes']<=4096 else 'Over budget'
        rows.append(f"{name} & {r['validation_mae']:.4f} & {r['test_mae']:.4f} & {b} & {eligible}")
    tex_table('vibrio_memory_frontier.tex','lrrrl','Model & Validation MAE & Test MAE & Payload (B) & 4 KiB eligible',rows)
    rows=[]
    for x in sensitivity:
        if x['package']=='Laboratory10' and x['budget_bytes'] in (4096,8192,16384):
            rows.append(f"{x['budget_bytes']//1024} & {100*x['tolerance']:.0f} & {x['method']} & {x['parameter_bytes']} & {x['validation_mae']:.4f} & {x['test_mae']:.4f}")
    tex_table('vibrio_budget_sensitivity.tex','rrlrrr',r'Budget (KiB) & Tolerance (\%) & Selected & Payload (B) & Val. MAE & Test MAE',rows)
    ph=[r for r in original['daily']['trials'] if r['task']=='ph' and r['package']=='TargetOnly' and not r['domain_qc']]
    tex_table('vietnam_ph_models.tex','lrrr','Model & Validation MAE & 2019 MAE & Payload (B)',
              [f"{r['method']} & {r['validation_mae']:.4f} & {r['test_mae']:.4f} & "+('--' if r['parameter_bytes'] is None else str(r['parameter_bytes'])) for r in ph])
    selected=[r for r in original['daily']['selection'] if r['task']=='ph' and not r['domain_qc']]
    tex_table('vietnam_ph_packages.tex','llrr','Package & Selected & Test MAE & Test forecasts',
              [f"{r['package']} & {r['method']} & {r['test_mae']:.4f} & {r['test_n']}" for r in selected])
    low,high=comparison['date_bootstrap_ci95']
    (PAPER/'tables/vibrio_frontier_findings.tex').write_text(
        f"Laboratory10 Forest16 improves validation MAE from {mean['validation_mae']:.4f} to {forest['validation_mae']:.4f} and test MAE from {mean['test_mae']:.4f} to {forest['test_mae']:.4f}. "
        f"Its {forest['parameter_bytes']:,}-byte estimated payload exceeds 4,096 bytes, so its exclusion is a memory-rule decision, not failure to improve validation. "
        f"The paired test-error difference is {comparison['paired_test_mae_difference']:.4f} log units (descriptive date-block bootstrap interval {low:.4f} to {high:.4f}, {len(per_date)} dates). "
        f"The forest's error corresponds to a geometric mean multiplicative discrepancy of {comparison['shifted_count_geometric_fold_error']:.2f} on the shifted count scale (CFU/mL $+1$). This is neither a per-sample bound nor a disease endpoint.",encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.3))
    for ax,metric in zip(axes,('validation_mae','test_mae')):
        for package in ('Field4','Field5','Laboratory10'):
            a=[r for r in sensitivity if r['package']==package and r['tolerance']==.05]
            ax.plot([r['budget_bytes']/1024 for r in a],[r[metric] for r in a],'o-',label=package)
        ax.set(xlabel='Parameter budget (KiB)',ylabel=metric.replace('_',' '));ax.legend(fontsize=8)
        ax.axvline(4,color='k',ls=':',lw=.8)
        ax.axvline(8,color='k',ls='--',lw=.8,alpha=.4)
        ax.set_xscale('log',base=2)
        ax.set_xticks([.5,1,2,4,8,16],labels=['0.5','1','2','4','8','16'])
    fig.tight_layout();fig.savefig(PAPER/'figures/vibrio_budget_frontier.pdf');fig.savefig(OUT/'vibrio_budget_frontier.png',dpi=180)
    print('Reporting sensitivities computed:',len(sensitivity),'selectors,',len(telemetry_grid),'telemetry cases.')


if __name__=='__main__':main()

