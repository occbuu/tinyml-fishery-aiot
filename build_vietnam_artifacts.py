"""Generate Vietnam manuscript tables and numerical statements from results."""
from pathlib import Path
from artifact_paths import ASSETS
import json,shutil

ROOT=Path(__file__).resolve().parent
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'


def table(name,columns,header,rows):
    text=[r'\begin{tabular}{'+columns+'}',r'\toprule',header+r' \\',r'\midrule']
    text.extend(row+r' \\' for row in rows)
    text.extend([r'\bottomrule',r'\end{tabular}'])
    (ASSETS/'tables'/name).write_text('\n'.join(text),encoding='utf-8')


def main():
    r=json.loads((ROOT/'results/vietnam_summary.json').read_text(encoding='utf-8'))
    (ASSETS/'tables').mkdir(exist_ok=True);(PAPER/'figures').mkdir(exist_ok=True)
    daily=[x for x in r['daily']['trials'] if not x['domain_qc'] and x['package']=='MultiSensor']
    rows=[]
    for name in ('Mean','Persistence','Ridge','Tree4','Forest16','MLP8','HistBoost'):
        d=next(x for x in daily if x['task']=='do' and x['method']==name)
        p=next(x for x in daily if x['task']=='ph' and x['method']==name)
        rows.append(f"{name} & {d['validation_mae']:.4f} & {d['test_mae']:.4f} & {p['validation_mae']:.4f} & {p['test_mae']:.4f}")
    table('vietnam_models.tex','lrrrr','Model & DO val. & DO test & pH val. & pH test',rows)
    selected=[x for x in r['daily']['selection'] if not x['domain_qc']]
    rows=[]
    for x in selected:
        ci=x['pond_bootstrap_mae_95']
        rows.append(f"{x['task'].upper()} & {x['package']} & {x['method']} & {x['test_n']} & {x['test_mae']:.4f} & {ci[0]:.4f}--{ci[1]:.4f}")
    table('vietnam_selection.tex','lllrrl',r'Task & Package & Selected & $n$ & MAE & Pond bootstrap 95\%',rows)
    rows=[]
    for name in ('Mean','Ridge','Tree4','Forest16','MLP8','HistBoost'):
        vals=[next(x['test_mae'] for x in r['vibrio']['trials'] if x['censor']=='half' and x['method']==name and x['package']==pack)
              for pack in ('Field4','Field5','Laboratory10')]
        rows.append(name+' & '+' & '.join(f'{v:.4f}' for v in vals))
    table('vietnam_vibrio.tex','lrrr','Model & Field4 & Field5 & Laboratory10',rows)
    rows=[]
    for x in r['economics']['summary']:
        rows.append(f"{x['year']} & {x['pond_crops']} & {x['operating_median_vnd']/1e6:.2f} & {100*x['energy_share_median']:.1f} & {100*x['feed_share_median']:.1f} & {x['negative_net_count']}")
    table('vietnam_economics.tex','rrrrrr',r'Year & Crops & Cost (M VND) & Energy (\%) & Feed (\%) & Negative net',rows)
    rows=[]
    for x in r['economics']['break_even_scenarios']:
        rows.append(f"{x['assumed_annual_monitoring_vnd']/1e3:.0f} & {x['assumed_crops_per_year']} & {x['allocated_vnd_per_crop']/1e3:.0f} & {100*x['median_required_energy_reduction']:.1f} & {x['crops_requiring_over_100pct_energy_reduction']}")
    table('vietnam_break_even.tex','rrrrr',r'Annual (k VND) & Crops/year & Per crop (k VND) & Median $r_{\rm req}$ (\%) & $r_{\rm req}>1$',rows)
    m=r['mangrove'];rows=[]
    labels=['Salinity (per mille)','pH','DO (mg/L)',r'H$_2$S ($\mu$g/L)',r'N-NO$_2$ (mg/L)',r'N-NO$_3$ (mg/L)',r'N-NH$_4$ (mg/L)',r'N-NH$_3$ ($\mu$g/L)']
    for label,x in zip(labels,m['parameters'][:8]):
        rows.append(label+f" & {x['n']} & {x['minimum']:.3f} & {x['median']:.3f} & {x['maximum']:.3f}")
    table('vietnam_chemistry.tex','lrrrr','Source variable/unit & Values & Minimum & Median & Maximum',rows)
    a=r['daily_audit']; total={y:{c:sum(x['observed'][c] for x in a if x['year']==y) for c in ('do','ph','temperature')} for y in (2018,2019)}
    lines=[]
    lines.append(f"The daily workbooks contain {sum(x['grid_rows'] for x in a)} pond-day grid rows across twelve year--pond series (six pond labels per year). There are {total[2018]['do']} observed DO and {total[2018]['ph']} observed pH entries in 2018, and {total[2019]['do']} DO and {total[2019]['ph']} pH entries in 2019. Templates continue beyond some crops; blank trailing dates are not invented observations.")
    d=next(x for x in selected if x['task']=='do' and x['package']=='MultiSensor')
    p=next(x for x in selected if x['task']=='ph' and x['package']=='MultiSensor')
    lines.append(f"Validation-only selection chooses persistence for both daily tasks: 2019 DO MAE {d['test_mae']:.4f} on {d['test_n']} eligible forecasts, and pH MAE {p['test_mae']:.4f} on {p['test_n']}. Ridge has a lower post-hoc pH point MAE than persistence, but this marginal comparison does not quantify a paired advantage and it was not chosen by the frozen validation rule; the test winner is not relabelled as the selected model. The stricter domain-QC sensitivity leaves both selected model names unchanged. Selected persistence needs no learned coefficient payload, while still requiring sampling and state storage.")
    v=r['vibrio'];s=next(x for x in v['selection'] if x['censor']=='half' and x['package']=='Field4')
    lines.append(f"The Vibrio experiment has {v['rows']} paired observations: {s['train_n']} training, {s['validation_n']} validation and {s['test_n']} test rows. For all three input packages the resource rule selects the training mean, with 2025 MAE {s['test_mae']:.4f} log units. Across zero/half-LOQ/LOQ replacements the selected mean remains unchanged; its MAE spans {min(x['test_mae'] for x in v['selection']):.4f}--{max(x['test_mae'] for x in v['selection']):.4f}. These observations include {v['do_below3']} source DO values below 3 mg/L, but provide no prospective illness or mechanically verified failure endpoint.")
    (ASSETS/'tables/vietnam_findings.tex').write_text('\n\n'.join(lines[:2]),encoding='utf-8')
    (ASSETS/'tables/vietnam_vibrio_findings.tex').write_text(lines[2],encoding='utf-8')
    shutil.copy2(ROOT/'results/vietnam_benchmark.pdf',PAPER/'figures/vietnam_benchmark.pdf')


if __name__=='__main__':main()
