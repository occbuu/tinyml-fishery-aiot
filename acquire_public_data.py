"""Versioned, bounded public-data downloads with checksum/provenance manifests.

Only public unrestricted research files, under the workspace data directory.
No authentication, request to authors or executable download is performed.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,datetime

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; META=DATA/'metadata'; RAW=DATA/'raw'
MAX_FILE=20_000_000


def get(url,max_bytes=MAX_FILE):
    req=Request(url,headers={'User-Agent':'AquacultureResearchBenchmark/1.0'})
    with urlopen(req,timeout=90) as r:
        size=int(r.headers.get('Content-Length',0))
        if size>max_bytes:raise ValueError(f'File exceeds bounded download: {size}')
        b=r.read(max_bytes+1)
        if len(b)>max_bytes:raise ValueError('File exceeds bounded download')
        return b


def store(job):
    key,name,url,licence,source,expected=job
    p=RAW/key/name
    if not p.resolve().is_relative_to((RAW/key).resolve()):raise ValueError('Unsafe source filename')
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        b=p.read_bytes()
        old=DATA/'download_manifest.json'
        if old.exists():
            record=next((r for r in json.loads(old.read_text(encoding='utf-8'))['records'] if r['path']==p.relative_to(ROOT).as_posix()),None)
            if record and hashlib.sha256(b).hexdigest()!=record['sha256']:raise ValueError('Existing raw file hash changed')
    else:
        b=get(url); p.write_bytes(b)
    if expected:
        alg,digest=expected.split(':',1)
        if hashlib.new(alg,b).hexdigest()!=digest:raise ValueError('Source checksum mismatch: '+str(p))
    record=dict(dataset=key,file=name,path=p.relative_to(ROOT).as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
                licence=licence,source=source,download_url=url,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    print(key,name,len(b),flush=True)
    return record


def main():
    jobs=[]
    blocked=[dict(dataset=f'vietnam_{year}',reason='Automatic Guestbook download not attempted; user-supplied local files are inventoried in data/vietnam_manifest.json') for year in (2017,2018,2019)]
    # User-supplied local Vietnam files are handled by vietnam_benchmark.py; no automatic Guestbook submission.
    # Zenodo file requests were explicitly denied for network traffic; do not
    # circumvent that restriction through alternative endpoints or identities.
    blocked.extend(dict(dataset=key,reason='Zenodo file access denied: unusual network traffic; metadata retained, no bypass attempted') for key in ('shrimp_respirometry','estuary_telemetry'))
    sources=[('colombia_pond','8s73jfvgr5',1),('biochemistry','y78ty2g293',1),('bangladesh_depth','34rczh25kc',4),('tilapia_colombia','dgdr2kfbyt',1),('aquaponic_esp8266','yd36bx6f8f',2)]
    for key,id,version in sources:
        # Metadata and CC BY licence records are supplied with the archive.
        state_file=META/(key+'_state.json')
        if state_file.exists():
            state=json.loads(state_file.read_text(encoding='utf-8'))['snapshot']
            if state['licence']['short_name']!='CC BY 4.0': raise ValueError('Review source licence: '+key)
        url=f'https://data.mendeley.com/public-api/datasets/{id}/files?folder_id=root&version={version}'
        files=json.loads(get(url))
        (META/(key+'_files.json')).write_text(json.dumps(files,indent=2),encoding='utf-8')
        for f in files:
            name=f.get('filename','')
            if name.endswith(('.csv','.xlsx','.xls','.txt')):
                jobs.append((key,name,f['content_details']['download_url'],'CC BY 4.0',f'https://doi.org/10.17632/{id}.{version}',None))
    query='station_id,SBE37_serial_number,time,depth,temperature,salinity,oxygen,temperature_qc,salinity_qc,oxygen_qc&time>=2019-05-01T00:00:00Z&time<2019-08-01T00:00:00Z'
    url='https://erddap.marine.ie/erddap/tabledap/sbe37_macehead.csv?'+quote(query,safe=',=&:')
    jobs.append(('marine_macehead','macehead_2019_may_july.csv',url,'CC BY 4.0','https://erddap.marine.ie/erddap/info/sbe37_macehead/index.html',None))
    tree=json.loads((META/'mlperf_tree.json').read_text())['tree']
    prefixes=['closed/STMicroelectronics/systems/NUCLEO_L4R5ZI-P.json','closed/STMicroelectronics/systems/NUCLEO_U575ZI_Q.json',
              'closed/STMicroelectronics/results/NUCLEO_L4R5ZI-P/ad/','closed/STMicroelectronics/results/NUCLEO_U575ZI_Q/ad/']
    wanted=[r['path'] for r in tree if r['path']=='LICENSE.md' or (r['path'].endswith('.json') and any(r['path'].startswith(p) for p in prefixes))]
    # Pin the repository commit rather than silently tracking main on rerun.
    commit=json.loads((META/'mlperf_tree.json').read_text())['sha']
    for name in wanted:
        jobs.append(('mlperf_tiny',name.replace('/','__'),f'https://raw.githubusercontent.com/mlcommons/tiny_results_v1.3/{commit}/'+quote(name,safe='/'),
                     'See downloaded LICENSE.md; submission notices apply','https://github.com/mlcommons/tiny_results_v1.3/tree/'+commit,None))
    for repo in ('esp-nn','esp-tflite-micro'):
        pin=json.loads((META/(repo+'_commit.json')).read_text())['sha']
        for name in ('README.md','LICENSE'):
            jobs.append(('espressif_performance',repo+'__'+name,f'https://raw.githubusercontent.com/espressif/{repo}/{pin}/{name}',
                         'Apache-2.0; dependency/submission notices apply',f'https://github.com/espressif/{repo}/tree/{pin}',None))
    records=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[(job,pool.submit(store,job)) for job in jobs]
        for job,future in futures:
            try: records.append(future.result())
            except Exception as e:
                blocked.append(dict(dataset=job[0],file=job[1],reason=str(e)))
                print('PENDING',job[0],job[1],str(e),flush=True)
    (DATA/'download_manifest.json').write_text(json.dumps(dict(records=records,blocked=blocked,total_bytes=sum(r['bytes'] for r in records),mlperf_commit=commit),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Total files',len(records),'bytes',sum(r['bytes'] for r in records),flush=True)


if __name__=='__main__':main()
