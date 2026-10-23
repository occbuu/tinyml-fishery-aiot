"""Compile exported C and check ordered predictions; host timing is not MCU timing."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,subprocess
import numpy as np

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--compiler-python',required=True,help='Python environment containing ziglang')
    args=parser.parse_args();build=ROOT/'firmware/host_build';build.mkdir(exist_ok=True)
    env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(ROOT.parent/'.tooling/zig-cache')
    tmp=ROOT.parent/'.tooling/zig-tmp';tmp.mkdir(exist_ok=True)
    env['TEMP']=str(tmp);env['TMP']=str(tmp)
    version=subprocess.check_output([args.compiler_python,'-m','ziglang','version'],env=env,text=True).strip()
    cases=json.loads((ROOT/'results/c_reference_cases.json').read_text())['cases'];rows=[]
    for case in cases:
        stem=case['key']+'_'+case['method'];c=build/(stem+'.c');dll=build/(stem+'.dll')
        header=(ROOT/case['header']).resolve().as_posix()
        c.write_text('#include "'+header+'"\n__declspec(dllexport) void reset_state(void){ model_reset(); }\n__declspec(dllexport) float evaluate(const float *x){return model_predict(x);}\n')
        compiled=subprocess.run([args.compiler_python,'-m','ziglang','cc','-target','x86_64-windows-gnu','-O2','-shared',str(c),'-o',str(dll)],env=env,capture_output=True,text=True)
        if compiled.returncode:raise RuntimeError(compiled.stderr)
        lib=ctypes.CDLL(str(dll));lib.reset_state();lib.evaluate.argtypes=[ctypes.POINTER(ctypes.c_float)];lib.evaluate.restype=ctypes.c_float
        values=np.array([[np.nan if v is None else v for v in row] for row in case['inputs']],np.float32)
        got=np.array([lib.evaluate(row.ctypes.data_as(ctypes.POINTER(ctypes.c_float))) for row in values])
        expected=np.asarray(case['expected']);errors=abs(got-expected)
        ok=np.isclose(got,expected,atol=case['tolerance_absolute'],rtol=case['tolerance_relative'])
        rows.append(dict(task=case['key'],method=case['method'],n=len(got),max_absolute_error=float(errors.max()),passed=bool(ok.all()),
                         failure_count=int((~ok).sum()),header_sha256=hashlib.sha256((ROOT/case['header']).read_bytes()).hexdigest()))
        print(stem,len(got),'PASS' if ok.all() else 'FAIL',float(errors.max()),flush=True)
    result=dict(compiler='Zig '+version,target='x86_64-windows-gnu',scope='Compiled C host parity only, not ESP32 timing or SRAM measurement.',
                rows=rows,all_passed=all(x['passed'] for x in rows))
    (ROOT/'results/c_reference_validation.json').write_text(json.dumps(result,indent=2))
    if not result['all_passed']:raise SystemExit('C parity failures retained in JSON; do not claim full export equivalence.')


if __name__=='__main__':main()
