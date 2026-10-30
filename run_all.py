"""Reproduce the V4 benchmark and generated manuscript assets."""
from pathlib import Path
import argparse,subprocess,sys

ROOT=Path(__file__).resolve().parent
STEPS={'prepare':'prepare_data.py','benchmark':'run_benchmark.py',
       'transfer':'transfer_and_context.py','vietnam':'vietnam_benchmark.py',
       'sensitivity':'analyze_reporting.py',
       'primary_export':'prepare_primary_hardware.py',
       'artifacts':'build_research_artifacts.py'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',nargs='+',choices=STEPS,help='Reuse unselected existing outputs; selected steps retain dependency order')
    parser.add_argument('--list',action='store_true')
    args=parser.parse_args()
    if args.list:
        for key,value in STEPS.items():print(key,value)
        return
    for key,value in STEPS.items():
        if args.only and key not in args.only:continue
        print('Running',key,flush=True)
        subprocess.run([sys.executable,str(ROOT/value)],cwd=ROOT,check=True)


if __name__=='__main__':main()
