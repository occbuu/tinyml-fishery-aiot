"""Refresh embedded tables by stable labels without recreating child .tex files."""
from pathlib import Path
import re
from artifact_paths import ROOT,ASSETS
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'
MAPPING={
 'tab:phmodels':'vietnam_ph_models','tab:phpaired':'vietnam_ph_paired',
 'tab:phablation':'vietnam_ph_packages','tab:rolling':'rolling_origin',
 'tab:frontier':'vibrio_memory_frontier','tab:budgets':'vibrio_budget_sensitivity',
 'tab:mainbuild':'esp32_build',
 'supp:table:errors':'models','supp:table:selection':'selection',
 'supp:table:ablation':'sensor_ablation','supp:table:missing':'stress',
 'supp:table:transfer':'transfer','supp:table:telemetry':'telemetry',
 'supp:table:vendor':'espressif','supp:table:daily':'vietnam_models',
 'supp:table:dailyselection':'vietnam_selection','supp:table:vibrio':'vietnam_vibrio',
 'supp:table:chemistry':'vietnam_chemistry','supp:table:economics':'vietnam_economics',
 'supp:table:breakeven':'vietnam_break_even','supp:table:policy':'telemetry_sensitivity',
}

def main():
    updated=[]
    for stem in ['manuscript','supplement']:
        path=PAPER/(stem+'.tex');source=path.read_text(encoding='utf-8')
        def update(match):
            block=match[0];label=re.search(r'\\label\{([^}]+)\}',block)
            if not label or label[1] not in MAPPING:return block
            file=ASSETS/'tables'/(MAPPING[label[1]]+'.tex')
            if not file.exists():raise FileNotFoundError(file)
            content=file.read_text(encoding='utf-8').strip()
            updated.append(label[1])
            result,n=re.subn(r'\\begin\{tabular\}.*?\\end\{tabular\}',lambda _:content,block,flags=re.S)
            assert n==1,label[1]
            return result
        source=re.sub(r'\\begin\{table\}.*?\\end\{table\}',update,source,flags=re.S)
        path.write_text(source,encoding='utf-8')
    assert len(list(PAPER.rglob('*.tex')))==2
    print('Synchronized',len(updated),'embedded tables; two .tex files retained')

if __name__=='__main__':main()
