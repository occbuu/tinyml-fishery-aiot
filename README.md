# Companion code for the Vietnamese shrimp-pond benchmark

This folder reproduces the calculations behind:

**Temporal Generalization and Memory-Budget Trade-offs in Vietnamese Shrimp-Pond Monitoring**

Anh Nguyen Thi Dieu and Hieu Le Ngoc.

| Document | Path |
| --- | --- |
| Manuscript | `../Paper2_FisheryAIoT_V4_Research/manuscript.tex` |
| Supplementary material | `../Paper2_FisheryAIoT_V4_Research/supplement.tex` |
| Bibliography | `../Paper2_FisheryAIoT_V4_Research/references.bib` |
| Figures used by both sources | `../Paper2_FisheryAIoT_V4_Research/figures/` |

The manuscript reports two primary experiments on separate historical Vietnamese records: next-day pH forecasting across the 2018–2019 crop years, and contemporaneous total-Vibrio estimation on water-chemistry assays from 2022–2025. The supplement reports four public high-frequency tasks, fault replay, pH transfer, telemetry policies, cost context, and host/firmware checks. Saved CSV and JSON files in `results/` are the numbers behind the tables. Generated LaTeX fragments live in `results/manuscript_assets/tables/` and are inserted into the two sources by label.

The archived run used Python 3.14.8, scikit-learn 1.9.1 and NumPy 2.5.3, with random seed `20261021`. A full check of this checkout on 30 October 2026 ran 34 unit tests and they all passed. `README_VI.md` is a working note; some older paragraphs in it still name `main.tex`. The current sources are `manuscript.tex` and `supplement.tex`.

## What a reader can do

1. Read the saved summaries in `results/` without fitting anything again.
2. Run the unit tests. They check causal features, year splits, the 4 KiB selection rule, checksums, C-export hashes, bibliography keys, and the archived board logs. They finished in about one second here.
3. Refit the benchmarks. The default runner does not open a serial port and does not flash a board.
4. Rebuild manuscript tables from those results. That step rewrites the two LaTeX sources, so run it only when that rewrite is intended.

Paths are resolved from each script. The shell working directory does not matter if the command uses the `simulateCode-v4/` prefix from the project root.

## Folder layout

Keep this arrangement. Vietnam refits and the manuscript tests look one level up.

```text
10_AIoT_Fishery_Review/
  simulateCode-v4/                         this folder
  Paper2_FisheryAIoT_V4_Research/          manuscript.tex, supplement.tex, figures/
  DataVietNam/                             Vietnam workbooks, read only
  build_manuscript_references.py           Paper 2 bibliography builder
  Code/HardwareTests_20261030/backups/     full-flash backups used by the flash guard
```

`DataVietNam/` is not copied into this folder. `data/vietnam_manifest.json` records SHA-256 values for the files the Vietnam analysis reads. Public raw files for the supplement are already in `data/raw/` (21 files, 62,064,944 bytes) with URLs, licences and SHA-256 values in `data/download_manifest.json`. No network access is required to repeat the saved experiments.

## Setup

From the project root:

```powershell
python -m pip install -r simulateCode-v4/requirements.txt
python -m unittest discover -s simulateCode-v4 -p "test_*.py"
```

`requirements.txt` asks for NumPy, pandas, SciPy, scikit-learn, Matplotlib and openpyxl. Excel reading needs pandas and openpyxl. Model fitting needs scikit-learn. The archived tree exports depend on the scikit-learn version above; a different release can change split thresholds even when the Python source is unchanged.

Host C checks and board builds are optional and need a second set of packages:

```powershell
python -m pip install -r simulateCode-v4/requirements-embedded.txt
```

That file pins PlatformIO 6.2.0, Zig 0.16.0 (via `ziglang`), pyelftools 0.33 and pyserial 3.5. Tool caches used in this workspace sit in `../.tooling/`. They are not required to read the results.

## Where the paper numbers are

Start with `reproducibility_manifest.json`. It stores the seed, library versions, and SHA-256 values for the scripts and result files from the last artifact build. Cite the CSV or JSON below when a digit matters. Rounded floats in the manuscript are generated from these files.

| File | What it holds |
| --- | --- |
| `results/vietnam_summary.json` | Daily pH/DO trials, Vibrio trials, crop economics, split description |
| `results/vietnam_daily_trials.csv`, `vietnam_daily_predictions.csv` | One row per model or held-out daily forecast |
| `results/vietnam_vibrio_trials.csv`, `vietnam_vibrio_predictions.csv` | Assay models and the 192 test predictions for 2025 |
| `results/vietnam_crop_economics.csv` | Nominal 2018–2019 VND crop accounts |
| `results/reporting_sensitivity.json` | Memory-budget frontier, paired pH interval, leave-one-date Vibrio checks |
| `results/model_trials.csv`, `predictions.csv` | Supplementary high-frequency folds, packages and models |
| `results/stress_trials.csv` | Spike, drift and dropout replay; dropped inputs stay in the denominator |
| `results/benchmark_summary.json` | Selector, telemetry and external MCU references for the supplement |
| `results/transfer_context.json` | Frozen pH transfer and an illustrative freshwater NH3 fraction |
| `results/c_reference_validation.json` | Host C versus Python: 20 headers, 5,440 predictions |
| `results/esp32_build_summary.json` | Five ESP32 cross-builds; static DRAM and linked flash only |
| `results/primary_hardware/hardware_summary.json` | ESP8266 and ESP32-S3 replay: 3,576 comparisons |
| `results/primary_hardware/RESULTS_VI.md` | Short table of the passing board run |
| `data/processed/data_audit.json` | Native rows, resampled grids, gaps and QC exclusions |

## Experiments

### Primary: Vietnamese records

`vietnam_benchmark.py` reads `../DataVietNam` and does not modify those workbooks or run the depositors' notebooks.

Daily pond series come from the Nutritious Pond archives for 2018 ([10.7910/DVN/FUCDMC](https://doi.org/10.7910/DVN/FUCDMC)) and 2019 ([10.7910/DVN/VJEDSU](https://doi.org/10.7910/DVN/VJEDSU)). Lags stay inside each pond–year. The label is the next calendar day. Missing targets stay missing. Training uses the early part of the 2018 season, validation starts on 4 June 2018, and the test set is the eligible 2019 forecasts (468 pH forecasts). The model is not refit after validation. Pond labels repeated across years are not treated as independent farms.

Total Vibrio comes from paired water and microbiology samples in Ca Mau, 2022–2025 ([10.5281/zenodo.22057734](https://doi.org/10.5281/zenodo.22057734)): 303 training rows (2022–2023), 184 validation rows (2024) and 192 test rows (2025). The endpoint is simultaneous log10(CFU/mL+1), not a disease label and not a next-day forecast. There is no stable pond identifier, so persistence is not used for this task. The primary substitution for explicit non-detects is half the limit of quantification; zero and full-LOQ substitutions are reported beside it.

Both tasks use the same fixed comparators: mean, persistence (daily tasks only), Ridge, a depth-4 tree, a 16-tree forest, an 8-unit MLP and histogram boosting. Hyperparameters are fixed in `run_benchmark.py`. Selection uses validation only: payload at most 4,096 bytes, error within 5% of the best model that fits that payload, then the smallest payload. The laboratory 16-tree forest beats the mean on validation and on the 2025 test, but its estimated node payload is 4,952 bytes, so the 4 KiB rule keeps the mean. Raising the allowance to 4,952 bytes selects the forest at 5% tolerance. That breakpoint is a declared byte budget. It is not a measurement of ESP32 RAM.

Mangrove–shrimp chemistry ([10.5281/zenodo.14560499](https://doi.org/10.5281/zenodo.14560499)) is descriptive. Repeated values inside five household groups are not 180 independent ponds. Crop costs are nominal 2018–2019 VND. The break-even table is a conditional sensitivity, not a 2026 quote and not a measured saving from a controller.

### Supplement: public high-frequency series

`prepare_data.py` builds causal grids from the raw files. Targets are never interpolated. `run_benchmark.py` then runs two forward blocks with a purge gap at each horizon. Scalers and imputers fit on the training block only.

| Task | Source | Grid | Horizon |
| --- | --- | --- | --- |
| Tilapia dissolved oxygen | [10.17632/dgdr2kfbyt.1](https://doi.org/10.17632/dgdr2kfbyt.1) | 1 hour | 1 step |
| Pond pH, two depths | [10.17632/34rczh25kc.4](https://doi.org/10.17632/34rczh25kc.4) | 5 minutes | 30 minutes |
| Aquaponic pH | [10.17632/yd36bx6f8f.2](https://doi.org/10.17632/yd36bx6f8f.2) | 5 minutes | 30 minutes |
| Marine temperature | [Mace Head SBE37](https://erddap.marine.ie/erddap/info/sbe37_macehead/index.html), May–July 2019 | 30 minutes | 1 hour |

The May–July 2019 marine slice has oxygen quality flag 0 on every row, so oxygen is neither a target nor a predictor. TDS is not treated as salinity. The biochemistry workbook ([10.17632/y78ty2g293.1](https://doi.org/10.17632/y78ty2g293.1)) and a transformed Colombia file ([10.17632/8s73jfvgr5.1](https://doi.org/10.17632/8s73jfvgr5.1)) stay in the audit inventory and are not forecast benchmarks. MLPerf Tiny v1.3 audio-anomaly results and Espressif person-detection kernel timings are external references. They are not timings of the water models.

Sensor packages are target history only, target history plus the other channels, and the other channels without target history. Stress replay adds spikes, drift and dropout without dropping the missing origins from the error. Telemetry changes how often a packet would be sent. It does not claim a matching cut in station or aerator energy.

`DATA_SOURCES.md` is the Vietnamese source ledger. The English summary above matches `data/download_manifest.json` and `data/vietnam_manifest.json`.

## Reproduce

List the runner steps:

```powershell
python simulateCode-v4/run_all.py --list
```

The runner always keeps this order, and it skips a step that is not named after `--only`. It does not fill in missing dependencies. If a selected step needs a file that is not on disk, run the earlier step first or run the full suite.

| Step | Script | Role |
| --- | --- | --- |
| `prepare` | `prepare_data.py` | Public raw files to `data/processed/` |
| `benchmark` | `run_benchmark.py` | Four high-frequency tasks, stress, telemetry, C headers |
| `transfer` | `transfer_and_context.py` | Frozen pH transfer and NH3 context |
| `vietnam` | `vietnam_benchmark.py` | Daily forecasts, Vibrio, chemistry, crop accounts |
| `sensitivity` | `analyze_reporting.py` | Budget frontier, paired pH, date influence |
| `primary_export` | `prepare_primary_hardware.py` | Refit the five primary estimators and check them against the frozen CSVs |
| `artifacts` | `build_research_artifacts.py` | Tables, figures, manuscript sync, evidence ledger |

```powershell
python simulateCode-v4/run_all.py
python simulateCode-v4/run_all.py --only vietnam artifacts
python simulateCode-v4/run_all.py --only artifacts
```

`artifacts` calls the Vietnam table builder, the embedded-evidence builder, the reporting analysis, the figure builder, the hardware summary, and `../build_manuscript_references.py --paper2`. It overwrites generated blocks in `manuscript.tex` and `supplement.tex`, copies figures into the paper folder, and refreshes `evidence_ledger.json` and `reproducibility_manifest.json`. BibTeX, aux and log files are produced outside the submission folder. `references.bib` is the curated library; the reference builder does not replace it with an uncited dump.

To rebuild the PDFs after that step, from `Paper2_FisheryAIoT_V4_Research`:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
bibtex supplement
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
```

Re-download public raw files only when a checksum should be refreshed. `acquire_public_data.py` uses the URLs already recorded in the manifest, refuses files above 20 MB, and does not fetch records that need a Guestbook login or a blocked Zenodo transfer. `discover_public_data.py` reads public metadata only.

## Firmware and the two boards

Three implementation checks are separate. Do not treat one as the other.

**Host C parity.** `firmware/c_reference/` holds float32 exports of the supplementary models. `results/c_reference_validation.json` records a Zig 0.16.0 host compile (`x86_64-windows-gnu`) of 20 headers and 5,440 ordered predictions, all within tolerance. Host time in that file is not microcontroller time. Rebuild with:

```powershell
python simulateCode-v4/prepare_embedded.py
python simulateCode-v4/verify_c.py --compiler-python <python-that-has-ziglang>
```

Missing fixture inputs are JSON `null`. The C side must turn those into NaN before imputation. A zero is not a missing reading.

**ESP32 cross-build, not a board measurement.** `firmware/wokwi_platformio/` is a PlatformIO project for a generic ESP32 module at 240 MHz, with Ridge, mean, persistence, tree and baseline environments. `collect_embedded.py` reads ELF section sizes with pyelftools and writes `results/esp32_build_summary.json`. Static DRAM and linked flash are not peak SRAM. The Wokwi diagram lint passed; the simulator itself was not run, because no Wokwi token was configured. `firmware/wokwi_platformio/README_VI.md` explains that project. `firmware/esp32/` is an earlier ESP-IDF scaffold and is not the measured firmware.

**Physical replay of the five primary estimators.** On 30 October 2026 an ESP8266EX (80 MHz, 4 MB flash, COM4) and an ESP32-S3 revision v0.2 (240 MHz, 16 MB flash, COM5) each replayed the frozen held-out set: 468 pH cases times persistence, Ridge and Forest16, plus 192 Laboratory10 Vibrio cases times mean and Forest16. That is 1,788 comparisons per board and 3,576 in total. Every comparison met the absolute tolerance of 2e-4 plus a relative tolerance of 2e-5. The summary is `results/primary_hardware/hardware_summary.json`. Raw serial logs, sample rows, binaries and a source snapshot are kept under the timestamped folders named in that summary. A later edit of the collector does not replace those snapshots.

The passing forest export keeps double precision for preprocessing constants, raw inputs, split thresholds and leaf accumulation, and float32 for the transformed tree input and the returned value. The other four estimators are float32. An earlier all-float32 forest export missed 5 pH cases and 4 Vibrio cases on each board. Those failed logs are kept and are not folded into the passing timings. The correction did not change the fitted trees, the split or the tolerance. The unrolled forest is also not the 4,748-byte or 4,952-byte node-table estimate used by the memory-budget rule. Payload bytes and on-device flash are different quantities.

The replay firmware does not drive GPIO, a relay or Wi-Fi. The host builds the causal pH history and clock features. The microcontroller imputes, scales and evaluates. The timer wraps 64 calls after one warm-up call and includes dispatch, conversion, an optimizer barrier and a volatile store. Serial parsing is outside that window. The reported median and 95th percentile are percentiles of those per-call batch means, not single-call latencies. The heap figures are free-heap samples before and after the batch, not peak SRAM. Power, radio, sensors, a control loop and any biological benefit were not measured. Laboratory Vibrio features still require the assay. The board test checks numerical agreement and this inference path. It is not a new pond trial.

Replaying the same boards needs PlatformIO, the backup images and the original MAC addresses checked in `run_primary_hardware.py` (`esp8266_4m` and `esp32s3_16m`). COM numbers change when the cables are replugged. The flash path checks the MAC, the backup hash and, on the ESP32-S3, that security flags are clear. It does not burn eFuses. Build one target at a time. The script maps the project root to `W:` to stay under the Windows command-length limit and stops if `W:` is already in use.

```powershell
python simulateCode-v4/prepare_primary_hardware.py
$hwPython = './.tooling/platformio-venv/Scripts/python.exe'
& $hwPython simulateCode-v4/run_primary_hardware.py build --target esp8266_4m
& $hwPython simulateCode-v4/run_primary_hardware.py build --target esp32s3_16m
& $hwPython simulateCode-v4/run_primary_hardware.py flash --target esp8266_4m --port COM4
& $hwPython simulateCode-v4/run_primary_hardware.py flash --target esp32s3_16m --port COM5
& $hwPython simulateCode-v4/run_primary_hardware.py collect --target esp8266_4m --port COM4
& $hwPython simulateCode-v4/run_primary_hardware.py collect --target esp32s3_16m --port COM5
python simulateCode-v4/run_all.py --only artifacts
```

Without those two boards, use the archived `samples.csv` and `serial.jsonl` files. The unit tests recompute the published comparisons from those logs.

## Code map

| Path | Role |
| --- | --- |
| `run_all.py` | Ordered reproduction entry point |
| `prepare_data.py`, `run_benchmark.py`, `transfer_and_context.py` | Supplement data, models, stress, telemetry, transfer |
| `vietnam_benchmark.py`, `build_vietnam_artifacts.py` | Primary Vietnam experiments and their tables |
| `analyze_reporting.py`, `revise_peer_review.py`, `final_review_artifacts.py` | Budget, pairing and date-influence checks on frozen predictions |
| `prepare_embedded.py`, `verify_c.py`, `collect_embedded.py` | Host C parity and ELF section sizes |
| `prepare_primary_hardware.py`, `run_primary_hardware.py`, `integrate_primary_hardware.py` | Primary export, board replay, manuscript hardware block |
| `build_research_artifacts.py`, `build_research_visuals.py`, `sync_manuscript_assets.py` | Tables, figures and label-stable insertion into the two sources |
| `reframe_underclaim.py` | Wording pass that does not change metrics |
| `test_*.py` | Regression tests for the claims above |
| `firmware/c_reference/` | Supplementary float32 headers checked on the host |
| `firmware/generated/` | Headers emitted by the high-frequency benchmark |
| `firmware/primary_hardware/` | Replay sketch for the two measured boards |
| `firmware/wokwi_platformio/` | ESP32 cross-build and simulator-ready project |

## Scope

Validation chooses the model. The test set is not used to fit, tune or break a tie. Daily dissolved oxygen from the Vietnam workbooks has no stated unit, so it is not pooled with the tilapia series in mg/L. A competitive persistence or mean baseline does not mean the corresponding probe can be removed. A smaller uplink count is not a measured cut in farm electricity. No result here is a disease threshold, a hypoxia alarm certified on these ponds, or a profit that an on-pond controller has already earned.
