# Primary-model hardware results — 30/10/2026

PASS: 1,788 model/input pairs per board, 3,576 total. Full held-out pH and Laboratory10 inputs; no retraining on test.

| Model | ESP8266 median / p95 (us) | ESP32-S3 median / p95 (us) |
|---|---:|---:|
| pH Persistence | 7.77 / 7.88 | 1.95 / 2.08 |
| pH Ridge | 62.39 / 62.93 | 5.22 / 5.34 |
| pH Forest16 | 139.57 / 145.41 | 36.68 / 38.65 |
| Vibrio Mean | 7.12 / 7.17 | 1.95 / 2.07 |
| Vibrio Forest16 | 182.70 / 186.49 | 45.66 / 46.84 |

Host-prepared causal features; imputation/scaling/inference onboard. Timing includes dispatch, conversion, optimizer barrier and volatile sink. No sensor, feature-generation, RF or energy measurement. Timings are per-call means of 64-call batches on each held-out input, not single-call samples.

Forests preserve double preprocessing constants, raw inputs, split thresholds and leaf accumulation, with float32 transformed tree inputs and output; other models use float32. Unrolled code is not the historical 16-byte/node payload representation.

Initial all-float32 forest exports had 5 pH and 4 Vibrio mismatches on each board; failed logs are retained. The corrected export passes without changing trained trees or test splits. Timings from the failed export are not mixed into the corrected results.

Firmware currently left on both boards: Paper 2 primary-model replay; no GPIO, relay or Wi-Fi commands. Original full firmware backups and Paper 1 binaries remain available.