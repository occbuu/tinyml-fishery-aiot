"""Generate implementation evidence from actual C validation and ESP32 builds."""
from pathlib import Path
from artifact_paths import ASSETS
import json
from integrate_primary_hardware import latex_scientific

ROOT=Path(__file__).resolve().parent
PAPER=ROOT.parent/'Paper2_FisheryAIoT_V4_Research'


def main():
    c=json.loads((ROOT/'results/c_reference_validation.json').read_text())
    b=json.loads((ROOT/'results/esp32_build_summary.json').read_text())
    if not c['all_passed']:raise ValueError('Do not publish all-pass C statement when validation has failed')
    n=sum(x['n'] for x in c['rows']);maximum=max(x['max_absolute_error'] for x in c['rows'])
    text=(f"All {len(c['rows'])} references pass across {n:,} ordered predictions using {c['compiler']} on the declared host target. "
          f"The largest absolute numerical discrepancy is {latex_scientific(maximum)} in the respective source output scales; per-case errors and header hashes are retained in JSON. "
          "This establishes the tested export's arithmetic/state agreement, not a new ecological accuracy score or an MCU latency measurement.")
    (ASSETS/'tables/compiled_findings.tex').write_text(text)
    lines=[r'\begin{tabular}{lrrr}',r'\toprule Firmware & Static DRAM (bytes) & Linked flash (bytes) & App image (bytes) \\',r'\midrule']
    for x in b['rows']:
        lines.append(f"{x['method']} & {x['static_data_bss_bytes']} & {x['linked_flash_sections_bytes']} & {x['firmware_bin_bytes']}"+r' \\')
    lines.extend([r'\bottomrule',r'\end{tabular}'])
    (ASSETS/'tables/esp32_build.tex').write_text('\n'.join(lines))


if __name__=='__main__':main()
