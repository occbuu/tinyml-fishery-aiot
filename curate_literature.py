"""Resolve explicit bibliographic identities against publisher-deposited Crossref records."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
import json,time

ROOT=Path(__file__).resolve().parent
DOIS={
 'pff':'10.1016/j.biosystemseng.2017.10.014',
 'camargo':'10.3390/s23094424',
 'jais':'10.1016/j.heliyon.2024.e29022',
 'parra':'10.3390/s18030750',
 'garcia':'10.3390/electronics10182192',
 'nuangpirom':'10.3390/s25196159',
 'slongo':'10.1007/s10661-024-12884-9',
 'samuelsson':'10.1016/j.watres.2019.115029',
 'roberts':'10.1111/ecog.02881',
 'bergmeir':'10.1016/j.csda.2017.11.003',
 'hewamalage':'10.1007/s10618-022-00894-5',
 'cerqueira':'10.1007/s10994-020-05910-7',
 'hyndman':'10.1016/j.ijforecast.2006.03.001',
 'efron':'10.1214/aos/1176344552',
 'kapoor':'10.1016/j.patter.2023.100804',
 'hoerl':'10.1080/00401706.1970.10488634',
 'breiman':'10.1023/A:1010933404324',
 'friedman':'10.1214/aos/1013203451',
 'boyd':'10.1007/978-1-4615-5407-3',
 'leigh2017':'10.1111/are.13338',
 'tran2013':'10.3354/dao02621',
 'lee2015':'10.1073/pnas.1503129112',
 'aeration':'10.1016/j.aquaculture.2024.741376',
 'gama':'10.1145/2523813',
 'helsel':'10.1016/j.chemosphere.2006.04.051',
 'fair':'10.1038/sdata.2016.18',
}
QUERIES={
 'leigh2020':'Rice-shrimp ecosystems in the Mekong Delta Linking water quality shrimp and their natural food sources',
 'wyban':'Temperature effects on growth feeding rate and feed conversion of the Pacific white shrimp Penaeus vannamei Wyban Walsh Godin',
 'moult':'The effect of short-term feed-deprivation and moult status on feeding behaviour of the Pacific white shrimp Litopenaeus vannamei',
}


def get(url):
    req=Request(url,headers={'User-Agent':'FisheryAIoT-local-bibliography-audit/1.0'})
    with urlopen(req,timeout=45) as f:return json.load(f)['message']


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    out=ROOT/'data/metadata/related_work_verified.json'
    existing=json.loads(out.read_text(encoding='utf-8')) if out.exists() else {}
    for key,doi in DOIS.items():
        if key in existing:continue
        try:
            m=get('https://api.crossref.org/works/'+quote(doi,safe=''))
            existing[key]=dict(doi=m['DOI'],title=m['title'][0],authors=m.get('author',[]),
                year=m.get('published',m.get('issued'))['date-parts'][0][0],
                venue=m.get('container-title',[]),volume=m.get('volume'),page=m.get('page'),
                url=m['URL'],abstract=m.get('abstract'),verification='Publisher-deposited Crossref metadata; not a new full-text systematic review.')
            print(key,existing[key]['title'],flush=True)
        except Exception as e:print(key,type(e).__name__,str(e)[:100],flush=True)
        out.write_text(json.dumps(existing,indent=2,ensure_ascii=False),encoding='utf-8')
    for key,q in QUERIES.items():
        if key in existing:continue
        m=get('https://api.crossref.org/works?rows=1&query.bibliographic='+quote(q))['items'][0]
        existing[key]=dict(doi=m['DOI'],title=m['title'][0],authors=m.get('author',[]),
                          year=m.get('published',m.get('issued'))['date-parts'][0][0],venue=m.get('container-title',[]),
                          volume=m.get('volume'),page=m.get('page'),url=m['URL'],abstract=m.get('abstract'),
                          verification='Crossref title query; exact identity requires inspection before citation.')
        print(key,existing[key]['title'],flush=True)
        out.write_text(json.dumps(existing,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
