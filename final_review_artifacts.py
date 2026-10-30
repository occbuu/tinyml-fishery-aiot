"""Refresh small-sample diagnostics from frozen predictions; no refitting."""
from pathlib import Path
import json,re
from artifact_paths import ROOT
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'

def replace_owned(source,key,body,anchor):
    begin='% BEGIN '+key;end='% END '+key
    block=begin+'\n'+body+'\n'+end+'\n'
    if begin in source:
        if source.count(begin)!=1 or source.count(end)!=1:raise ValueError('Duplicate/malformed owned block '+key)
        return re.sub(re.escape(begin)+'.*?'+re.escape(end)+'\n',lambda _:block,source,flags=re.S)
    if source.count(anchor)!=1:raise ValueError('Missing or ambiguous anchor for '+key)
    return source.replace(anchor,block+'\n'+anchor,1)

def main():
    result=json.loads((ROOT/'results/reporting_sensitivity.json').read_text())
    r=result['vibrio_comparison'];low,high=r['leave_one_date_out_range']
    body=(r'\paragraph{Sensitivity to individual sampling dates.} '
      +f"Forest16 has lower mean absolute error on {r['dates_favoring_forest']} of the {r['date_blocks']} recorded 2025 dates; each date contributes 16 observations. "
      +f"The equally date-weighted difference is {r['equally_weighted_date_difference']:.4f} log units, identical to the row-weighted contrast because date sizes are equal. "
      +f"Omitting each date in turn gives paired error differences from {low:.4f} to {high:.4f}; all twelve deletion contrasts retain the same direction. "
      +r'Table~\ref{supp:table:dateinfluence} in the supplement gives every date contrast. The consistent deletion direction shows that the observed pooled improvement is retained after removal of any single campaign. Date-level grouping preserves within-campaign dependence in this diagnostic. Broader validation requires additional seasons and identifiable ponds, because the twelve dates may also share serial or pond-level dependence. The deletion range is a sensitivity statistic rather than a confidence interval.')
    p=PAPER/'manuscript.tex';source=p.read_text(encoding='utf-8')
    source=replace_owned(source,'VIBRIO DATE INFLUENCE',body,r'\subsection{An external pond-identified assay does not supply the missing threshold}')
    # Cross-document reference uses a verified explicit supplement number, keeping both sources standalone.
    source=source.replace(r'Table~\ref{supp:table:dateinfluence} in the supplement',r'The supplementary date-influence table (Table~S18)')
    p.write_text(source,encoding='utf-8')
    lines=[r'\section{Sampling-Date Influence in the Frozen Vibrio Comparison}',
      r'Table~\ref{supp:table:dateinfluence} retains all 12 date-level Forest16-minus-Mean MAE contrasts and the row-weighted contrast after deleting that date. No model is refitted or selected in this sensitivity; all values use the original 2025 predictions. Four dates favor Mean and eight favor Forest16. Equal date sizes make the row- and date-weighted pooled contrasts coincide.',
      r'\begin{table}[H]\centering\small',
      r'\caption{Sampling-date influence on Laboratory10 test MAE, in $\log_{10}(\mathrm{CFU/mL}+1)$ units. Negative differences favor Forest16. The last column omits the named date and retains the other 11; it is a sensitivity statistic, not a confidence bound.}\label{supp:table:dateinfluence}',
      r'\begin{tabular}{lrrr}\toprule Date & Observations & Date MAE difference & Leave-one-date-out difference \\\midrule']
    for row in r['date_influence']:
        lines.append(f"{row['date']} & {row['n']} & {row['mean_error_difference']:.4f} & {row['leave_one_date_out_difference']:.4f}"+r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table}',r'The 12 recorded sampling dates span June--September 2025. Their seasonal and possible repeated-pond dependence limits extrapolation to other campaigns or farms. Whole-date resampling retains within-date dependence but cannot reconstruct missing pond identities or assure independence between dates. More temporally and spatially separated sampling campaigns are the next unit of validation.']
    p=PAPER/'supplement.tex';source=p.read_text(encoding='utf-8')
    source=re.sub(r'\b(\d+(?:\.\d+)?)[eE]([+-]\d+)\b',lambda m:'$'+m[1]+r'\times10^{'+str(int(m[2]))+'}$',source)
    source=replace_owned(source,'VIBRIO DATE DIAGNOSTICS','\n'.join(lines),r'\bibliographystyle{IEEEtran}')
    p.write_text(source,encoding='utf-8')
    print('Frozen date-level influence diagnostics integrated; no model refit')

if __name__=='__main__':main()
