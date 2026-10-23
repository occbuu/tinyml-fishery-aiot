"""Read-only public metadata acquisition. No account, credentials or private APIs."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import json,re

ROOT=Path(__file__).resolve().parent
META=ROOT/'data/metadata'; META.mkdir(parents=True,exist_ok=True)
SOURCES={
    'shrimp_respirometry':'https://zenodo.org/api/records/7971310',
    'estuary_telemetry':'https://zenodo.org/api/records/3459610',
    'colombia_pond_html':'https://data.mendeley.com/datasets/8s73jfvgr5/1',
    'colombia_pond_doi':'https://api.datacite.org/dois/10.17632/8s73jfvgr5.1',
    'biochemistry_html':'https://data.mendeley.com/datasets/y78ty2g293/1',
    'vietnam_search':'https://dataverse.harvard.edu/api/search?q='+quote('"Nutritious Pond"')+'&type=dataset&per_page=20',
    'mlperf_tree':'https://api.github.com/repos/mlcommons/tiny_results_v1.3/git/trees/main?recursive=1',
}

def fetch(item):
    key,url=item
    try:
        req=Request(url,headers={'User-Agent':'AquacultureResearchBenchmark/1.0'})
        with urlopen(req,timeout=60) as r: body=r.read(4_000_000)
        (META/(key+('.html' if key.endswith('_html') else '.json'))).write_bytes(body)
        if key.endswith('_html'):
            s=body.decode('utf-8')
            for term in ('download_url','downloadUrl','file_download','fileDownload','__PRELOADED_STATE__','licence','license'):
                i=s.find(term)
                if i>=0: print(key,term,s[max(0,i-60):i+400],flush=True)
        else:
            d=json.loads(body)
            if key.startswith('mlperf'):
                paths=[x['path'] for x in d.get('tree',[]) if x['path'].endswith(('.csv','.json','.md'))]
                print(key,paths[:35],flush=True)
            elif key=='vietnam_search':
                print(key,[(x.get('name'),x.get('global_id')) for x in d.get('data',{}).get('items',[])],flush=True)
            else:print(key,d.get('metadata',{}).get('license'),[(x.get('key'),x.get('size')) for x in d.get('files',[])],flush=True)
    except Exception as e: print(key,'ERROR',str(e),flush=True)

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(fetch,SOURCES.items()))
