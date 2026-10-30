"""Generate manuscript tables/figures from completed experiments, not hand edits."""
from pathlib import Path
from artifact_paths import ASSETS
import json,shutil,hashlib,platform
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
LABEL={'tilapia_do':'Tilapia DO','pond_ph':'Pond pH','aquaponic_ph':'Aquaponic pH','marine_temperature':'Marine temperature'}


def table(name,columns,rows):
    lines=[r'\begin{tabular}{'+columns+'}',r'\toprule',rows[0]+r' \\',r'\midrule']
    lines.extend(r+r' \\' for r in rows[1:])
    lines.extend([r'\bottomrule',r'\end{tabular}'])
    (ASSETS/'tables'/name).write_text('\n'.join(lines),encoding='utf-8')


def main():
    (ASSETS/'tables').mkdir(exist_ok=True);(PAPER/'figures').mkdir(exist_ok=True)
    r=json.loads((OUT/'benchmark_summary.json').read_text())
    trials=pd.read_csv(OUT/'model_trials.csv'); stress=pd.read_csv(OUT/'stress_trials.csv')
    tasks=[t['key'] for t in r['tasks']]
    methods=['Persistence','Mean','Ridge','Tree4','MLP8','Forest16','HistBoost']
    rows=[r'Model & DO (mg/L) & Pond pH & Aquaponic pH & Marine ($^\circ$C)']
    for model in methods:
        vals=[next(x['mae'] for x in r['summary'] if x['task']==task and x['package']=='MultiSensor' and x['method']==model) for task in tasks]
        rows.append(model+' & '+' & '.join(f'{x:.4f}' for x in vals))
    table('models.tex','lrrrr',rows)
    rows=['Task & Target history & Multiple sensors & No target sensor']
    for task in tasks:
        vals=[]
        for package in ('TargetOnly','MultiSensor','NoTarget'):
            chosen=[x for x in r['selection'] if x['task']==task and x['package']==package]
            total=weighted=0
            for item in chosen:
                g=trials[(trials.task==task)&(trials.fold==item['fold'])&(trials.package==package)&(trials.method==item['method'])].iloc[0]
                total+=g['n'];weighted+=item['mae']*g['n']
            vals.append(weighted/total)
        rows.append(LABEL[task]+' & '+' & '.join(f'{x:.4f}' for x in vals))
    table('sensor_ablation.tex','lrrr',rows)
    rows=['Task & Fold & Selected & MAE & Payload (bytes)']
    for x in r['selection']:
        if x['package']=='MultiSensor':rows.append(f"{LABEL[x['task']]} & {x['fold']+1} & {x['method']} & {x['mae']:.4f} & {x['parameter_bytes']}")
    table('selection.tex','lllrr',rows)
    rows=[r'Task & Periodic packets & Event packets & Reduction (\%) & Replay MAE']
    for x in r['telemetry']:rows.append(f"{LABEL[x['task']]} & {x['periodic_packets']} & {x['event_packets']} & {100*x['reduction']:.1f} & {x['reconstruction_mae']:.4f}")
    table('telemetry.tex','lrrrr',rows)
    rows=['Task & Clean: selected & Dropout: selected & Dropout: fallback']
    for task in tasks:
        vals=[]
        for fault,policy in [('clean','Selected'),('dropout','Selected'),('dropout','QualityFallback')]:
            g=stress[(stress.task==task)&(stress.fault==fault)&(stress.policy==policy)]
            vals.append(float(np.average(g.mae,weights=g.n)))
        rows.append(LABEL[task]+' & '+' & '.join(f'{x:.4f}' for x in vals))
    table('stress.tex','lrrr',rows)
    transfer=json.loads((OUT/'transfer_context.json').read_text())
    rows=['Source $\to$ target & No adaptation & 3-day intercept correction']
    for src,dst in [('pond_ph','aquaponic_ph'),('aquaponic_ph','pond_ph')]:
        g=[x for x in transfer['ph_transfer'] if x['source']==src and x['destination']==dst]
        v=[next(x['mae'] for x in g if x['calibration_days']==n) for n in (0,3)]
        rows.append(LABEL[src]+r' $\to$ '+LABEL[dst]+' & '+' & '.join(f'{x:.4f}' for x in v))
    table('transfer.tex','lrr',rows)
    shutil.copy2(OUT/'model_comparison.pdf',PAPER/'figures/model_comparison.pdf')
    vendor=[]
    for line in (ROOT/'data/raw/espressif_performance/esp-tflite-micro__README.md').read_text(encoding='utf-8').splitlines():
        cells=[c.strip() for c in line.strip('|').split('|')]
        if len(cells)==5 and cells[0] in ('ESP32','ESP32-C3','ESP32-S3','ESP32-P4'):
            vendor.append(dict(chip=cells[0],workload=cells[1],without_esp_nn_ms=float(cells[2].replace('ms','')),
                with_esp_nn_ms=float(cells[3].replace('ms','')),cpu_mhz=float(cells[4].replace('MHz','')),
                scope='Vendor invoke-only person-detection example, internal memory; not our water-quality model.'))
    (OUT/'espressif_performance.json').write_text(json.dumps(vendor,indent=2))
    table('espressif.tex','lrrr',[r'Chip & CPU (MHz) & Without ESP-NN (ms) & With ESP-NN (ms)']+
          [f"{v['chip']} & {v['cpu_mhz']:.0f} & {v['without_esp_nn_ms']:.0f} & {v['with_esp_nn_ms']:.0f}" for v in vendor])
    versions=dict(python=platform.python_version(),model_library=r['sklearn'],numpy=r['numpy'])
    from build_vietnam_artifacts import main as build_vietnam
    build_vietnam()
    from build_embedded_artifacts import main as build_embedded
    build_embedded()
    from analyze_reporting import main as analyze_reporting
    analyze_reporting()
    from build_research_visuals import main as build_visuals
    build_visuals()
    import subprocess,sys
    from revise_peer_review import diagnostics
    diagnostics()
    from sync_manuscript_assets import main as sync_assets
    sync_assets()
    from integrate_primary_hardware import main as integrate_hardware
    integrate_hardware()
    from final_review_artifacts import main as final_review
    final_review()
    from reframe_underclaim import main as reframe_underclaim
    reframe_underclaim()
    subprocess.run([sys.executable,str(ROOT.parent/'build_manuscript_references.py'),'--paper2'],check=True)
    project=ROOT/'firmware/wokwi_platformio'
    source_paths=list(ROOT.glob('*.py'))+[ROOT/'data/download_manifest.json',ROOT/'data/vietnam_manifest.json',ROOT/'data/metadata/related_work_verified.json']+list(OUT.glob('*.csv'))+list(OUT.glob('*.json'))
    source_paths+=list((ROOT/'firmware/c_reference').glob('*.h'))+list((project/'src').glob('*.cpp'))+list((project/'include').glob('*.h'))+[project/'platformio.ini',project/'wokwi.toml',project/'diagram.json',project/'run_simulation.py']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    hardware_path=OUT/'primary_hardware/hardware_summary.json'
    measured=hardware_path.exists() and json.loads(hardware_path.read_text())['all_passed']
    manifest=dict(versions=versions,seed=r['seed'],measured_on_device=measured,raw_manifest='data/download_manifest.json',
        dataset_policy='User-supplied Vietnam sources analyzed separately by sampling design; QC0 marine oxygen and threshold-created quality labels excluded.',
        source_and_result_sha256=hashes)
    (ROOT/'reproducibility_manifest.json').write_text(json.dumps(manifest,indent=2))
    raw=json.loads((ROOT/'data/download_manifest.json').read_text(encoding='utf-8'))
    (PAPER/'evidence_ledger.json').write_text(json.dumps(dict(manuscript_type='Original public-data benchmark research',
        new_field_trial=False,new_mcu_measurement=measured,compiled_c_validation=True,esp32_cross_build=True,wokwi_executed=False,source_data_downloaded=True,primary_tasks=2,supplementary_high_frequency_tasks=4,vietnam_daily_tasks=2,vietnam_vibrio_association_task=1,raw_file_count=len(raw['records']),
        vietnam_manifest='../simulateCode-v4/data/vietnam_manifest.json',
        raw_bytes=raw['total_bytes'],selection='Validation only, 4 KiB parameter payload, within 5% of best validation MAE; minimum payload.',
        benchmarks='Primary: Vietnamese next-day pH and simultaneous total Vibrio; Supplement: other tasks, unresolved-unit DO, telemetry, implementation and cost context.',
        reporting_sensitivity='54 fixed-fit memory/tolerance selectors (512 B through 16 KiB); 48 telemetry policies; no test-based fitting.',
        daily_do_unit='Unresolved; excluded from primary physiological and numerical-accuracy claims.',
        ph_paired_comparison='Ridge minus Persistence; 468 matched TargetOnly forecasts, six pond labels, all 46656 ordered whole-label bootstrap resamples; descriptive interval includes zero.',
        descriptive_biochemistry='679-record pooled post-hoc Spearman display with pair counts; includes held-out years, never used for feature or model selection.',
        hardware_evidence=('Primary-model board replay and 64-call batch timing on ESP8266 and ESP32-S3; peak SRAM and energy unmeasured.' if measured else 'Cross-build only; no physical primary-model measurement.'),primary_hardware_summary='results/primary_hardware/hardware_summary.json' if measured else None,
        code='../simulateCode-v4'),indent=2))


if __name__=='__main__':main()
