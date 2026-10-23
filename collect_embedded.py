"""Read ESP32 ELF sections without executing firmware or inferring peak RAM."""
from pathlib import Path
import argparse,hashlib,json,sys

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pyelftools-path')
    args=parser.parse_args()
    if args.pyelftools_path:sys.path.insert(0,args.pyelftools_path)
    from elftools.elf.elffile import ELFFile
    project=ROOT/'firmware/wokwi_platformio';rows=[]
    for env,name in [('esp32dev','Ridge'),('mean','Mean'),('persistence','Persistence'),('tree','Tree4'),('baseline','Loop baseline')]:
        p=project/'.pio/build'/env/'firmware.elf'
        with p.open('rb') as f:
            elf=ELFFile(f);sections={s.name:int(s['sh_size']) for s in elf.iter_sections()}
        data=sum(v for k,v in sections.items() if k in ('.dram0.data','.dram0.bss','.noinit'))
        flash=sum(v for k,v in sections.items() if k in ('.dram0.data','.iram0.vectors','.iram0.text','.flash.text','.flash.rodata'))
        rows.append(dict(environment=env,method=name,static_data_bss_bytes=data,linked_flash_sections_bytes=flash,
                         firmware_bin_bytes=(p.parent/'firmware.bin').stat().st_size,elf_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),sections=sections))
        print(env,data,flash)
    result=dict(platformio='6.2.0',platform='espressif32@6.10.0',framework='Arduino ESP32 2.0.17',compiler='xtensa-esp32-elf GCC 8.4.0',cpu_mhz=240,
                rows=rows,wokwi_executed=False,wokwi_status='Ready project; WOKWI_CLI_TOKEN not configured.',physical_board_measured=False,
                scope='Actual cross-compilation and ELF-section accounting, not runtime SRAM, peak heap or physical flash write verification. Fixture arrays/framework are included.')
    (ROOT/'results/esp32_build_summary.json').write_text(json.dumps(result,indent=2))


if __name__=='__main__':main()
