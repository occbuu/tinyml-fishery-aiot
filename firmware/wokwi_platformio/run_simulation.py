"""Run an authorized Wokwi session; retain explicit simulator provenance."""
from pathlib import Path
import argparse,json,os,re,shutil,subprocess

PROJECT=Path(__file__).resolve().parent
RESULTS=PROJECT.parents[1]/'results'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--env',choices=['esp32dev','mean','persistence','tree','baseline'],default='esp32dev')
    parser.add_argument('--cli',default='wokwi-cli');args=parser.parse_args()
    status=RESULTS/('wokwi_'+args.env+'.json')
    if not os.environ.get('WOKWI_CLI_TOKEN'):
        status.write_text(json.dumps(dict(executed=False,status='WOKWI_CLI_TOKEN not configured; firmware/project available.',physical_measurement=False),indent=2))
        print('Wokwi was not run. Configure your token locally or start the project with the Wokwi VS Code extension. Never commit a token.');return
    if not shutil.which(args.cli) and not Path(args.cli).is_file():raise SystemExit('Wokwi CLI not installed; see README.')
    config=PROJECT/'wokwi.toml';old=config.read_text();log=RESULTS/('wokwi_'+args.env+'.log')
    try:
        config.write_text("[wokwi]\nversion = 1\nfirmware = '.pio/build/"+args.env+"/firmware.bin'\nelf = '.pio/build/"+args.env+"/firmware.elf'\n")
        result=subprocess.run([args.cli,str(PROJECT),'--timeout','60000','--expect-text','BENCHMARK_DONE','--fail-text','REPLAY_FAIL','--serial-log-file',str(log)],capture_output=True,text=True)
        text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
        passed=result.returncode==0 and 'REPLAY_PASS' in text and 'BENCHMARK_DONE' in text
        blocks=[int(x) for x in re.findall(r'elapsed_us=(\d+)',text)]
        data=dict(executed=True,passed=passed,scope='Wokwi virtual ESP32 execution; not physical MCU timing, energy or sensor qualification.',
                  environment=args.env,returncode=result.returncode,physical_measurement=False,block_elapsed_us=blocks,
                  raw_serial_log=str(log.relative_to(RESULTS.parent)))
        status.write_text(json.dumps(data,indent=2))
        if not passed:raise SystemExit('Wokwi run failed; inspect the retained serial log and JSON status.')
        print('Wokwi virtual replay passed:',args.env)
    finally:config.write_text(old)


if __name__=='__main__':main()
