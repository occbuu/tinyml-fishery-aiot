"""Build, guard/flash and collect primary-model evidence on the two named boards."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,subprocess,sys,os,json,time,hashlib,csv,statistics,re

ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
PROJECT=ROOT/'firmware/primary_hardware';OUT=ROOT/'results/primary_hardware'
DEVICES={
 'esp8266_4m':dict(chip='esp8266',mac='c8:c9:a3:2d:61:9f',size=4194304,backup='com4_original_4MB.bin'),
 'esp32s3_16m':dict(chip='esp32s3',mac='7c:e8:b1:a3:f3:64',size=16777216,backup='com5_original_16MB.bin')}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def logged(folder,name,args,cwd=WS,env=None,timeout=600):
    start=datetime.now(timezone.utc).isoformat();t=time.monotonic()
    r=subprocess.run([str(x) for x in args],cwd=cwd,env=env,capture_output=True,timeout=timeout)
    item=dict(command=[str(x) for x in args],start_utc=start,duration_s=time.monotonic()-t,exit_code=r.returncode,stdout=r.stdout.decode('utf-8','replace'),stderr=r.stderr.decode('utf-8','replace'))
    (folder/(name+'.json')).write_text(json.dumps(item,indent=2),encoding='utf-8')
    print(name,item['exit_code'],item['stdout'][-1800:],item['stderr'][-500:],flush=True)
    if r.returncode:raise RuntimeError(name+' failed; see '+str(folder))
    return item['stdout']

def percentile(a,q):
    a=sorted(a);p=(len(a)-1)*q;i=int(p);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)

def collect(target,port,folder):
    import serial
    fixture=json.loads((OUT/'fixture.json').read_text());raw=(folder/'serial.jsonl').open('w',encoding='utf-8')
    def log(direction,data):
        raw.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),monotonic_ns=time.monotonic_ns(),direction=direction,hex=data.hex()))+'\n');raw.flush()
    rows=[]
    with serial.Serial(port,115200,timeout=.1,write_timeout=3) as ser:
        ser.dtr=False;ser.rts=False;time.sleep(2);ser.reset_input_buffer()
        def request(text,prefix,timeout=5):
            payload=(text+'\n').encode('ascii');log('TX',payload);ser.write(payload);ser.flush();deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                line=ser.readline()
                if not line:continue
                log('RX',line);value=line.decode('ascii','replace').strip()
                if value.startswith(prefix):return value
                if value.startswith('ERROR'):raise RuntimeError(value)
            raise TimeoutError('No '+prefix+' for '+text[:45])
        info=request('INFO','INFO,');assert 'PRIMARY_V4,20261030' in info,info
        request('RESET','RESET,OK')
        previous=None
        for case in fixture['cases']:
            group=(case['model'],case['metadata'].get('pond'))
            if group!=previous:request('RESET','RESET,OK');previous=group
            values=','.join('nan' if x is None else format(x,'.17g') for x in case['inputs'])
            result=request('P,'+str(case['id'])+','+str(case['model'])+','+values,'R,').split(',')
            assert len(result)==7 and int(result[1])==case['id'] and int(result[2])==case['model']
            got=float(result[3]);expected=case['expected'];error=abs(got-expected)
            row=dict(id=case['id'],model=case['model'],key=case['key'],prediction=got,expected=expected,absolute_error=error,passed=error<=fixture['tolerance_absolute']+fixture['tolerance_relative']*abs(expected),batch_us=int(result[4]),calls_per_batch=fixture['batch_calls'],mean_us_per_call=int(result[4])/fixture['batch_calls'],heap_before=int(result[5]),heap_after=int(result[6]))
            rows.append(row)
            if len(rows)%300==0:print(target,len(rows),'/',len(fixture['cases']),flush=True)
        request('RESET','RESET,OK')
    raw.close()
    with (folder/'samples.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    results=[]
    for model in fixture['models']:
        group=[r for r in rows if r['model']==model['id']];times=[r['mean_us_per_call'] for r in group]
        results.append(dict(**model,n=len(group),mismatches=sum(not r['passed'] for r in group),max_absolute_error=max(r['absolute_error'] for r in group),batch_mean_us_p50=statistics.median(times),batch_mean_us_p95=percentile(times,.95),batch_mean_us_p99=percentile(times,.99),batch_mean_us_max=max(times),min_observed_free_heap=min(min(r['heap_before'],r['heap_after']) for r in group)))
    hashes={str(p.relative_to(WS)):digest(p) for p in list(PROJECT.glob('src/*.cpp'))+list(PROJECT.glob('include/*.h'))+[PROJECT/'platformio.ini',OUT/'fixture.json',Path(__file__),ROOT/'prepare_primary_hardware.py',ROOT/'run_benchmark.py']}
    summary=dict(target=target,port=port,info=info,recorded_utc=datetime.now(timezone.utc).isoformat(),physical_board_measured=True,all_passed=all(r['passed'] for r in rows),comparisons=len(rows),models=results,scope=fixture['scope'],precision=fixture['precision'],fixture_sha256=digest(OUT/'fixture.json'),source_sha256=hashes)
    artifacts=PROJECT/'.pio/build'/target
    summary['binary_sha256']={p.name:digest(p) for p in artifacts.glob('*') if p.suffix in ('.bin','.elf')}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary['models'],indent=2),flush=True)
    assert summary['all_passed'],'Prediction mismatches retained; investigate before publication'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['build','flash','collect']);parser.add_argument('--target',choices=DEVICES,required=True);parser.add_argument('--port');args=parser.parse_args()
    folder=OUT/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+args.target+'_'+args.action);folder.mkdir(parents=True)
    if args.action=='build':
        env=os.environ.copy();env['PLATFORMIO_CORE_DIR']=str(WS/'.tooling/platformio-core');env['PLATFORMIO_SETTING_ENABLE_TELEMETRY']='no'
        # Short workspace alias avoids the Windows compiler command-length limit.
        if Path('W:/').exists():raise RuntimeError('W: is already in use')
        logged(folder,'subst',['subst','W:',str(WS)])
        try:
            env['PLATFORMIO_CORE_DIR']='W:/.tooling/platformio-core'
            logged(folder,'build',[sys.executable,'-m','platformio','run','-d','W:/simulateCode-v4/firmware/primary_hardware','-e',args.target,'-j','4'],env=env)
        finally:logged(folder,'unsubst',['subst','W:','/d'])
    elif args.action=='flash':
        if not args.port:raise ValueError('--port required')
        d=DEVICES[args.target];esptool=WS/'.tooling/platformio-core/packages/tool-esptoolpy/esptool.py'
        def tool(name,tail):return logged(folder,name,[sys.executable,esptool,'--port',args.port,'--baud','460800']+tail)
        identity=tool('identity',['chip_id']);assert d['mac'] in identity.lower(),'Unexpected board MAC'
        backup=WS/'Code/HardwareTests_20261030/backups'/d['backup'];assert backup.stat().st_size==d['size'],'Incomplete backup'
        provenance=json.loads((WS/'Code/HardwareTests_20261030/results/provenance.json').read_text())
        entry=next(x for x in provenance['files'] if x['path']=='backups/'+d['backup'])
        assert digest(backup)==entry['sha256'],'Original backup hash differs'
        (folder/'backup_verified.json').write_text(json.dumps(dict(path=str(backup),sha256=digest(backup),bytes=backup.stat().st_size)))
        b=PROJECT/'.pio/build'/args.target
        if args.target=='esp8266_4m':images=['0',b/'firmware.bin'];size='4MB'
        else:
            status=tool('security',['--chip','esp32s3','get_security_info']);assert 'Flags: 0x00000000' in status
            bootapp=WS/'.tooling/platformio-core/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin'
            images=['0',b/'bootloader.bin','0x8000',b/'partitions.bin','0xe000',bootapp,'0x10000',b/'firmware.bin'];size='16MB'
        tool('flash',['--chip',d['chip'],'write_flash','--flash_mode','dio','--flash_size',size]+images)
    else:
        if not args.port:raise ValueError('--port required')
        collect(args.target,args.port,folder)

if __name__=='__main__':main()
