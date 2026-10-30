"""Render verified references without padding the list with uncited entries."""
from pathlib import Path
from artifact_paths import ASSETS
import html,json,re

ROOT=Path(__file__).resolve().parent
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'


def latex(s):
    s=html.unescape(re.sub('<[^>]+>','',str(s))).strip()
    for c in ('\u2010','\u2011','\u2012','\u2013','\u2014'):s=s.replace(c,'-')
    s=s.replace('\u2019',"'").replace('\u2018',"'").replace('\u00a0',' ')
    return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')


def main():
    records=json.loads((ROOT/'data/metadata/related_work_verified.json').read_text(encoding='utf-8'))
    lines=[]
    for key,x in records.items():
        a=x['authors'][0] if x['authors'] else {}
        author=a.get('family',a.get('name','Unknown author'))
        if len(x['authors'])>1:author+=', et al.'
        venue=x['venue'][0] if x['venue'] else ''
        detail=' '.join(str(v) for v in (x.get('volume'),x.get('page')) if v)
        lines.append(r'\bibitem{lit_'+key+'} '+latex(author)+f" ({x['year']}). "+latex(x['title'])+'. '+latex(venue+' '+detail)+r'. \url{https://doi.org/'+x['doi']+'}')
    extras=[
      ('pedregosa','Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research 12, 2825--2830.','https://jmlr.org/papers/v12/pedregosa11a.html'),
      ('tflm','David, R., et al. (2021). TensorFlow Lite Micro: Embedded Machine Learning on TinyML Systems. Proceedings of Machine Learning and Systems 3; author manuscript.','https://arxiv.org/abs/2010.08678'),
      ('cmsis','Lai, L., Suda, N., and Chandra, V. (2018). CMSIS-NN: Efficient Neural Network Kernels for Arm Cortex-M CPUs. Author preprint.','https://arxiv.org/abs/1801.06601'),
      ('mcunet','Lin, J., et al. (2020). MCUNet: Tiny Deep Learning on IoT Devices. Advances in Neural Information Processing Systems 33.','https://proceedings.neurips.cc/paper/2020/hash/86c51678350f656dcc7f490a43946ee5-Abstract.html'),
      ('mlperf','Banbury, C., et al. (2021). MLPerf Tiny Benchmark. NeurIPS Datasets and Benchmarks.','https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/da4fb5c6e93e74d3df8527599fa62642-Paper-round1.pdf'),
      ('wokwi','Wokwi. Simulating PlatformIO Projects; CLI Usage. Official configuration and simulation documentation. Accessed 21 October 2026.','https://docs.wokwi.com/vscode/platformio'),
      ('platformio','PlatformIO. Espressif ESP32 Dev Module. Official board and build documentation. Accessed 21 October 2026.','https://docs.platformio.org/en/stable/boards/espressif32/esp32dev.html'),
    ]
    for key,title,url in extras:lines.append(r'\bibitem{lit_'+key+'} '+title+r' \url{'+url+'}')
    # Legacy reference rendering is diagnostic only; curated references.bib is canonical.
    (ASSETS/'related_references.tex').write_text('\n'.join(lines),encoding='utf-8')
    print('Related-work references:',len(lines))


if __name__=='__main__':main()
