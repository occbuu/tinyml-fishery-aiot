"""Validate physical replay evidence, summarize it, and refresh manuscript blocks."""
from pathlib import Path
import csv,json,hashlib,re,zipfile
from artifact_paths import ROOT
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
OUT=ROOT/'results/primary_hardware'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def latex_scientific(value):
    coefficient,exponent=f'{value:.2e}'.split('e')
    return '$'+coefficient+r'\times10^{'+str(int(exponent))+'}$'

def refresh_manuscript(source,block):
    """Refresh an owned block without growing editorial prose on repeated runs."""
    if '% BEGIN GENERATED PRIMARY HARDWARE' in source:
        if source.count('% BEGIN GENERATED PRIMARY HARDWARE')!=1:raise ValueError('Duplicate hardware block')
        source=re.sub(r'% BEGIN GENERATED PRIMARY HARDWARE.*?% END GENERATED PRIMARY HARDWARE\n',lambda _:block,source,flags=re.S)
    else:
        anchor=next((a for a in [r'\section{Interpretation and Limits}',r'\section{Design Implications and Limits}'] if a in source),None)
        if anchor is None:raise ValueError('Missing insertion anchor for hardware evidence')
        source=source.replace(anchor,block+'\n'+anchor,1)
    sentence='Primary-model replay also establishes numerical agreement on two tested microcontrollers, with execution timing reported separately from the historical payload estimates.'
    # Repair previously generated repetitions; never append to the conclusion.
    source=re.sub('(?:'+re.escape(sentence)+r'\s*){2,}',lambda _:sentence+' ',source)
    return source

def main():
    if not OUT.exists():return
    fixture=OUT/'fixture.json'
    if not fixture.exists():return
    selected=[]
    for target in ['esp8266_4m','esp32s3_16m']:
        candidates=sorted(OUT.glob('*_'+target+'_collect/summary.json'))
        if not candidates:return
        path=candidates[-1];s=json.loads(path.read_text())
        # A new failed run must never be silently replaced with an old pass.
        assert s['all_passed'] and s['fixture_sha256']==sha(fixture)
        assert s['comparisons']==1788
        rows=list(csv.DictReader((path.parent/'samples.csv').open()))
        assert len(rows)==1788 and len({r['id'] for r in rows})==1788
        assert all(r['passed']=='True' for r in rows)
        for name,digest in s['source_sha256'].items():
            assert sha(path.parent/'snapshot'/name)==digest,('Missing source snapshot',name)
        for name,digest in s['binary_sha256'].items():
            assert sha(path.parent/'artifacts'/name)==digest
        builds=sorted(q for q in OUT.glob('*_'+target+'_build/build.json') if q.parent.name.split('_')[0]<=path.parent.name.split('_')[0])
        build=json.loads(builds[-1].read_text())
        text=build['stdout'];ram=re.search(r'RAM:.*?used (\d+) bytes',text);flash=re.search(r'Flash:.*?used (\d+) bytes',text)
        assert ram and flash
        s['static_ram_bytes']=int(ram[1]);s['program_bytes']=int(flash[1])
        s['run_summary']=path.relative_to(ROOT).as_posix()
        s['build_log']=builds[-1].relative_to(ROOT).as_posix()
        selected.append(s)
    failures=[]
    for path in sorted(OUT.glob('*_collect/summary.json')):
        old=json.loads(path.read_text())
        if not old['all_passed']:failures.append(dict(run=path.relative_to(ROOT).as_posix(),target=old['target'],mismatches={x['key']:x['mismatches'] for x in old['models'] if x['mismatches']}))
    combined=dict(all_passed=True,physical_board_measured=True,total_comparisons=sum(x['comparisons'] for x in selected),boards=selected,initial_failed_exports=failures,scope=selected[0]['scope'],precision=selected[0]['precision'])
    (OUT/'hardware_summary.json').write_text(json.dumps(combined,indent=2),encoding='utf-8')
    work=ROOT.parent/'.artifact_checks/primary_hardware_integration';work.mkdir(exist_ok=True)
    backup=work/'before_integration.zip'
    if not backup.exists():
        with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
            for f in PAPER.glob('*'):
                if f.is_file():z.write(f,f.name)
    names=['pH Persistence','pH Ridge','pH Forest16','Vibrio Mean','Vibrio Forest16']
    lines=[r'\subsection{Physical primary-model replay on two microcontrollers}\label{sec:primaryhardware}',
      r'We exported the primary pH Persistence, Ridge and Forest16 fits trained on 324 early-2018 outcomes, and the Laboratory10 Mean and Forest16 fits trained on 303 observations from 2022--2023. The 468 held-out pH feature vectors are replayed for each of three models and the 192 held-out microbial vectors for each of two models, giving 1,788 comparisons per board. Refitted export predictions are checked against the archived frozen predictions before code generation; neither the split nor model selection is changed.',
      r'The Laboratory10 deployment is a computational-feasibility stress test of the fitted forest on the two available microcontrollers, not a proposed pond-side laboratory workflow. A laboratory workstation or gateway is an equally valid execution location once chemistry results exist. The assay turnaround was not recorded in these datasets; the measured microsecond computation cannot shorten the unmeasured acquisition and assay stages.',
      r'The physical devices are an ESP8266EX at 80 MHz with 4 MB flash and an ESP32-S3 revision v0.2 at 240 MHz with 16 MB flash. MAC-guarded flashing verifies the retained full original firmware backups. PlatformIO pins Espressif8266 4.2.1 / Arduino 3.1.2 / GCC 10.3.0 and Espressif32 6.10.0 / Arduino 2.0.17 / GCC 8.4.0, respectively, with an explicit \texttt{-O2} application build flag. Wi-Fi, sensor acquisition and relay outputs are not enabled in this harness.',
      r'An initial all-float32 forest export failed the stated parity tolerance on five pH and four Vibrio inputs on each board. Finite-precision changes near tree split boundaries can alter a branch. The corrected forest export retains double-precision raw input parsing, preprocessing constants, thresholds and leaf accumulation, with float32 transformed tree inputs and returned predictions, following the reference estimator\textquotesingle s transform-and-split precision. Other models use float32 arithmetic. No trees are retrained. These unrolled implementations differ from the historical 16-byte/node portable allowance: the extra forest preprocessing precision alone changes stored constants from $12d$ to $24d$ bytes, and actual linked code must be accounted for separately. The historical resource frontier remains an estimated representation study rather than the measured size of this export.',
      r'Table~\ref{tab:primarytiming} reports board-side execution profiles and numerical agreement. Every held-out model/input pair meets $|\widehat y_{\mathrm{MCU}}-\widehat y_{\mathrm{Python}}|\le2\times10^{-4}+2\times10^{-5}|\widehat y_{\mathrm{Python}}|$ on both devices (3,576 comparisons total). The maximum discrepancy over these comparisons is '+latex_scientific(max(m['max_absolute_error'] for b in selected for m in b['models']))+r'. Initial failing runs remain archived alongside the corrected runs.',
      r'Each timing sample uses the MCU microsecond clock around 64 repeated calls on one held-out feature vector, after a warm-up prediction. The reported quantiles are across these batch means, not a distribution of single-call latency. Imputation, scaling, dispatch, input conversion, an optimizer barrier and volatile output assignment lie inside the timed loop; serial parsing/output and the warm-up lie outside it. A no-inline dispatch and memory barrier prevent invariant-input inference from being hoisted out of the loop. Features and pH history are prepared causally on the host; feature construction and acquisition are outside this timing boundary. Framework interrupts are retained, and harness overhead is not subtracted.',
      r'\begin{table}[H]\centering\small',
      r'\caption{On-board inference-path timing, excluding acquisition, feature construction and communication. Values are median / 95th percentile of per-call means from 64-call batches, in microseconds. $n$ is the held-out model/input count per board; all pass numerical tolerance. The forests use the precision-preserving export described in the text.}\label{tab:primarytiming}',
      r'\begin{tabular}{lrrr}\toprule Model & $n$ & ESP8266 (80 MHz) & ESP32-S3 (240 MHz) \\\midrule']
    for i,name in enumerate(names):
        a=selected[0]['models'][i];b=selected[1]['models'][i]
        lines.append(f"{name} & {a['n']} & {a['batch_mean_us_p50']:.2f} / {a['batch_mean_us_p95']:.2f} & {b['batch_mean_us_p50']:.2f} / {b['batch_mean_us_p95']:.2f}"+r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table}',
      r'Table~\ref{tab:primaryimages} accounts for each combined five-model firmware image, including the Arduino framework and serial harness. The reported free heap is sampled before and after inference batches and is not peak SRAM or a stack bound. No per-model flash increment or inference energy is inferred from these aggregate values.',
      r'\begin{table}[H]\centering\small',
      r'\caption{Combined primary-model firmware accounting. Static RAM and program bytes come from PlatformIO build accounting; minimum free heap is observed on the physical board at batch boundaries. Image bytes are the complete application BIN file size, not model payload.}\label{tab:primaryimages}',
      r'\begin{tabular}{lrrrr}\toprule Board & Static RAM (B) & Program (B) & App BIN (B) & Min. free heap (B) \\\midrule']
    for board,name in zip(selected,['ESP8266','ESP32-S3']):
        artifact=ROOT/Path(board['run_summary']).parent/'artifacts/firmware.bin'
        lines.append(f"{name} & {board['static_ram_bytes']} & {board['program_bytes']} & {artifact.stat().st_size} & {min(m['min_observed_free_heap'] for m in board['models'])}"+r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table}',
      r'The design implication is to qualify numeric export and whole-firmware accounting separately from the statistical payload frontier. \textbf{The measured interval is an on-board inference path with harness overhead, not end-to-end edge latency or sensor-to-decision latency.} Sensor sampling, bus transactions, lag/rolling-feature construction, radio wake-up/transmission, assay turnaround, energy and peak SRAM require separate acquisition-to-action measurements. The Laboratory10 stress test establishes arithmetic execution on the tested devices while preserving its laboratory observation requirements.']
    block='% BEGIN GENERATED PRIMARY HARDWARE\n'+'\n\n'.join(lines)+'\n% END GENERATED PRIMARY HARDWARE\n'
    block=re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}',lambda m:re.sub(r'\n\s*\n','\n',m[0]),block,flags=re.S)
    path=PAPER/'manuscript.tex';source=path.read_text(encoding='utf-8')
    source=refresh_manuscript(source,block)
    source=source.replace('Physical latency, energy and peak SRAM of the primary fitted models remain prospective measurements.',r'Physical replay of the primary fitted models is reported in Section~\ref{sec:primaryhardware}; energy and peak SRAM remain unmeasured.')
    source=source.replace('The Vietnamese Laboratory10 forest is assessed by parameter accounting and held-out predictions; this diagram does not depict an implemented laboratory-to-MCU pipeline.',r'This diagram documents the earlier replay implementation. Primary-model board inference is measured separately in Section~\ref{sec:primaryhardware}; a laboratory acquisition pipeline is not implemented here.')
    source=source.replace('Physical runtime and energy assessment therefore remain a separate implementation stage.',r'The separate physical primary-model experiment in Section~\ref{sec:primaryhardware} supplies board-side batch timing; energy assessment remains a separate implementation stage.')
    source=source.replace('Linked ESP32 image accounting complements portable parameter estimates,', 'Primary-model replay on ESP8266 and ESP32-S3 passes all 3,576 numerical comparisons; board-side batch timing complements portable parameter estimates,')
    # textquotesingle is not guaranteed by the minimal article preamble.
    source=source.replace(r'\textquotesingle s',"'s")
    path.write_text(source,encoding='utf-8')
    path=PAPER/'supplement.tex';source=path.read_text(encoding='utf-8')
    sentence=r'The primary-model physical-board replay is reported in the main manuscript, Section 5.1 and Tables 10--11; the implementation discussion below concerns the earlier supplementary fixtures.'
    if sentence not in source:source=source.replace(r'\section*{Scope of this Supplement}',r'\section*{Scope of this Supplement}'+'\n'+sentence)
    source=source.replace('MLP8 and Forest16 are retained host comparators without a firmware image in this project.', 'For these supplementary high-frequency fixtures, MLP8 and Forest16 have no firmware image; the primary-task forest board exports are reported separately in the main manuscript.')
    path.write_text(source,encoding='utf-8')
    report=['# Primary-model hardware results — 30/10/2026','', 'PASS: 1,788 model/input pairs per board, 3,576 total. Full held-out pH and Laboratory10 inputs; no retraining on test.','', '| Model | ESP8266 median / p95 (us) | ESP32-S3 median / p95 (us) |','|---|---:|---:|']
    for i,name in enumerate(names):
        a,b=[board['models'][i] for board in selected]
        report.append(f"| {name} | {a['batch_mean_us_p50']:.2f} / {a['batch_mean_us_p95']:.2f} | {b['batch_mean_us_p50']:.2f} / {b['batch_mean_us_p95']:.2f} |")
    report += ['',combined['scope'],'',combined['precision'],'','Initial all-float32 forest exports had 5 pH and 4 Vibrio mismatches on each board; failed logs are retained. The corrected export passes without changing trained trees or test splits. Timings from the failed export are not mixed into the corrected results.','', 'Firmware currently left on both boards: Paper 2 primary-model replay; no GPIO, relay or Wi-Fi commands. Original full firmware backups and Paper 1 binaries remain available.']
    (OUT/'RESULTS_VI.md').write_text('\n'.join(report),encoding='utf-8')
    print('Validated two boards, integrated primary-model timing into manuscript')

if __name__=='__main__':main()
