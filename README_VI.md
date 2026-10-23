# Phạm vi bản thảo chính và phân tích bổ sung

Bài chính `../Paper2_FisheryAIoT_V4_Research/main.tex` tập trung pH Việt Nam qua hai năm và ước lượng total Vibrio. `supplementary.tex` giữ benchmark tần suất cao, DO chưa rõ đơn vị, telemetry, firmware và kinh tế. Không coi compiled C/cross-build là số đo thiết bị thật; Wokwi chưa thực thi.

`python run_all.py --only sensitivity artifacts` tái tạo frontier bộ nhớ và tài liệu từ các model đã fit. `analyze_reporting.py` thực hiện 54 lựa chọn budget/tolerance và 48 chính sách telemetry. Forest16 Laboratory10 tốt hơn Mean ở validation lẫn test nhưng cần 4.952 byte: 4 KiB/5% chọn Mean, 8 KiB/5% chọn Forest16. Thay đổi này không dùng test để fit hoặc chọn model. Kiểm thử: `python -m unittest discover -p "test*.py"`.

# Research benchmark: phần cứng phổ thông, dữ liệu và chi phí có kiểm chứng

Đây là nghiên cứu tái sử dụng dữ liệu công khai với xử lý, thí nghiệm và kết quả mới. Bản thảo là `../Paper2_FisheryAIoT_V4_Research/main.tex`. Mọi số trong bản thảo đến từ gói này và từ các tệp công khai đã lưu.

## Đã có trong workspace

- 21 tệp nguyên bản, tổng 62.064.944 byte; nguồn, giấy phép, phiên bản, thời điểm tải và SHA-256 trong `data/download_manifest.json`.
- Dữ liệu Arduino Mega ở hai độ sâu; NodeMCU ESP8266 với PH-4502C/TDS/DS18B20; dữ liệu DO tilapia; nhiệt độ/độ mặn biển có cờ QC.
- Các tệp sinh hóa và dữ liệu Colombia đã biến đổi được giữ để audit, không đưa vào benchmark dự báo nếu không đủ điều kiện.
- Kết quả MLPerf Tiny v1.3 công khai của Cortex-M4/M33, gồm accuracy/performance/power/system/license. Đây là workload audio anomaly bên ngoài, không phải đo model thủy sản hay ESP32 của nghiên cứu này.
- Bảng hiệu năng chính thức Espressif cho ESP32/C3/S3/P4 cùng kernel benchmarks và license, pin commit. Trích xuất ở `results/espressif_performance.json`; không gán timing của person detection cho model nước.
- Bốn bài toán × hai fold thời gian × ba gói cảm biến; persistence, mean, Ridge, cây depth-4, forest nhỏ, MLP-8 và histogram boosting. Chọn model chỉ theo validation, payload ≤4 KiB, nhỏ nhất trong mức sai số +5% so với tốt nhất đủ ngân sách.
- Stress replay spike/drift/dropout; transfer pH giữa hai hệ; telemetry sự kiện có heartbeat và cờ unknown; tính nhạy NH3 ở nước ngọt với điều kiện đơn vị rõ ràng.

Danh sách nguồn/điều kiện: `DATA_SOURCES.md`. Dữ liệu Việt Nam đã được người dùng cung cấp tại `../DataVietNam/`; manifest riêng là `data/vietnam_manifest.json`. Các bộ 2018–2019, Vibrio và hóa học ao rừng–tôm đã được phân tích; các nguồn khác có trong inventory, không ép thành chuỗi IoT.

## Chạy lại

Các tệp raw đã có, không cần mạng để tái tạo kết quả. Đọc Excel bằng bundled Python mà Codex cung cấp; phần ML dùng môi trường Python có scikit-learn (bundled Python của phiên này chưa có thư viện đó).

```powershell
# Cài thư viện nếu chạy trên máy khác:
python -m pip install -r simulateCode-v4/requirements.txt

# Có thể chạy preparation bằng bundled Python hoặc Python đã có pandas/openpyxl:
python simulateCode-v4/run_all.py
python -m unittest discover -s simulateCode-v4 -p 'test_*.py'

Set-Location Paper2_FisheryAIoT_V4_Research
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Chỉ khi cần tải lại raw mới chạy `simulateCode-v4/acquire_public_data.py` với quyền mạng. Script dùng các URL công khai đã xác minh, giới hạn mỗi tệp 20 MB, không tự tải các nguồn cần Guestbook hoặc Zenodo bị chặn, kiểm tra hash tệp hiện có. Metadata đã được lưu cùng gói; `discover_public_data.py` hỗ trợ xem lại các nguồn ban đầu nhưng không tải tệp hạn chế. Cần giữ cấu trúc hai thư mục paper/code khi muốn tái sinh các bảng.

## Cách đọc kết quả

- `results/model_trials.csv`: mỗi fold/gói/model, train/validation/test, MAE/RMSE, cảnh báo hội tụ, payload ước tính và thời gian gọi API trên host.
- `results/predictions.csv`: từng dự báo held-out để kiểm tra độc lập.
- `results/stress_trials.csv`: cùng bộ target cho các policy, có số dự báo và coverage; không bỏ mẫu mất đầu vào để làm đẹp error.
- `results/benchmark_summary.json`: kết quả tổng hợp, selector, stress, telemetry và tham chiếu MCU.
- `results/transfer_context.json`: chuyển miền pH và lưới NH3 minh họa, không phải số đo NH3 thực tế.
- `data/processed/data_audit.json`: giữ rõ native rows/grid rows, khoảng trống, loại trừ và cờ QC.
- `reproducibility_manifest.json`: phiên bản và hash code/kết quả; các tệp raw có manifest riêng.

Hai fold giữ test theo thời gian, purge horizon giữa các partition. Không random split; scaler/imputer chỉ fit train; không interpolate target. Model có warning vẫn được báo cáo. Khoảng resampling theo ngày là mô tả tập hiện có, không chứng nhận hiệu quả tại quần thể ao Việt Nam. Không điều chỉnh hyperparameter theo kết quả test.

Một số kết quả quan trọng: Ridge/persistence thường cạnh tranh tốt; thêm cảm biến không luôn cải thiện dự báo; bỏ lịch sử target làm ba bài toán kém rõ rệt. Mean được chọn cho DO vì chuỗi không có thiếu oxy nặng, không có nghĩa bỏ được đầu dò DO. Quality fallback có thể giúp hoặc hại tùy miền; drift chậm vẫn khó. Giảm 62,9–84,0% gói chỉ là uplink replay, không phải giảm tương ứng điện toàn trạm/quạt nước.

## Code cho thiết bị giá phổ thông

`firmware/generated/` chứa model C float32, fixture và thứ tự feature; một số model chọn chỉ là mean/persistence. `firmware/esp32/` giữ scaffold ESP-IDF; dự án thử đầy đủ hơn là `firmware/wokwi_platformio/`, có PlatformIO, sơ đồ Wokwi, fixture và log parser. Copy một header thành `model.h`, đặt vào project ESP-IDF và cấp đúng vector feature từ fixture hoặc bộ lấy mẫu đã kiểm chứng. Fixture JSON dùng `null` cho input thiếu; firmware phải chuyển thành NaN để áp dụng imputation đúng.

Đã compile 20 reference C và kiểm 5.440 dự báo so với Python; đã cross-build năm firmware ESP32 bằng PlatformIO. Chưa có bo thật hoặc token chạy Wokwi nên chưa đo timing/peak SRAM/điện trên ESP32; không gán số đo host cho MCU. Payload 0–196 byte không phải tổng RAM/flash firmware. Cần thêm acquisition, calibration, timestamp/staleness, history buffer, watchdog, bảo vệ cục bộ, điện/relay độc lập, UART logs và kiểm tra dự báo C khớp fixture trước thử ngoài ao. Scaffold không phải bộ điều khiển thương mại.

## Hướng sản phẩm và nghiên cứu tiếp theo

Ưu tiên MCU sẵn có, local logs/protection, đầu dò thay thế được, reference check dùng chung theo HTX, giảm uplink và chỉ thêm kênh có quyết định sử dụng rõ. Không cần camera/GPU/SBC nếu bài toán không chứng minh giá trị của chúng. Ngược lại, model không thể bù cho đầu dò không đủ chuẩn hoặc hoàn toàn thiếu tín hiệu sinh hóa thiết yếu.

Dữ liệu Việt Nam hiện có benchmark qua năm 2018→2019, đánh giá Vibrio theo năm 2022–2025, hóa học ao rừng–tôm và 12 tài khoản vụ nuôi. Chi phí là VND danh nghĩa 2018–2019; bảng hòa vốn là độ nhạy có điều kiện, không phải báo giá 2026 hay ROI đã chứng minh. Chưa có thử nghiệm thiết bị mới, độ bền qua vụ hoặc lợi nhuận đối chứng do AI. “Hiệu quả kinh tế tốt nhất” là mục tiêu tối ưu dưới ràng buộc còn phải đo. Cần dữ liệu có hypoxia thực, TAN có đơn vị xác định, salinity, biomass/feed, reference probes và nhật ký service trước khi tối ưu nuôi tôm nước ngọt, nước lợ hoặc loài khác.


## Thí nghiệm Việt Nam

Đọc `VIETNAM_STUDY_VI.md` để xem nguồn, chia tập và giới hạn. Chạy riêng phần Việt Nam và cập nhật paper từ kết quả high-frequency đã có:

```powershell
python simulateCode-v4/run_all.py --only vietnam artifacts
```

`run_all.py` mặc định chạy toàn bộ: prepare → benchmark → transfer → vietnam → artifacts. Có thể chạy từ bất kỳ thư mục terminal nào bằng đường dẫn tuyệt đối. `DataVietNam/` phải nằm cạnh thư mục code; nguồn không bị sửa. `artifacts` sinh bảng/hình vào `Paper2_FisheryAIoT_V4_Research/`.

## Xác minh nhúng và tài liệu

Hướng dẫn: `firmware/wokwi_platformio/README_VI.md`. Kết quả C: `results/c_reference_validation.json`; build ESP32: `results/esp32_build_summary.json`. Firmware baseline và model đều chứa fixture/framework; static DRAM và linked flash không phải peak SRAM. Lệnh tái tạo model C: `python simulateCode-v4/prepare_embedded.py`; kiểm C bằng `verify_c.py --compiler-python <python-có-ziglang>`.

Danh mục V4 có 53 mục được trích trong nội dung, gồm 29 record DOI đối chiếu metadata Crossref, năm công trình phương pháp/nhúng từ trang chính thức, tài liệu Wokwi/PlatformIO và các nguồn dữ liệu/tài liệu đã có. `curate_literature.py` hỗ trợ đối chiếu danh tính, không tự thay cho đọc toàn văn hoặc systematic review. `build_related_work.py` sinh bibliography từ metadata đã lưu.

## So cặp pH theo ao

`analyze_reporting.py` ghép Ridge–persistence theo ao/ngày nguồn/ngày mục tiêu, không theo thứ tự dòng; enumerate 46.656 resample của sáu chuỗi ao. Kết quả trong `results/reporting_sensitivity.json`, bảng `vietnam_ph_paired.tex`. Chênh −0,0127 pH, khoảng mô tả [−0,0273; +0,0036] chứa zero; không đổi model đã chọn bằng validation.

## Hình và định vị nghiên cứu

`python build_research_artifacts.py` sinh thêm pipeline thời gian, frontier 512 B–16 KiB (54 lựa chọn), Spearman mô tả trên 679 mẫu và sơ đồ firmware đúng implementation. EDA gồm cả test, không dùng tuning. Bảng phần cứng chỉ có linked/static memory; runtime/peak/energy chưa đo. Đánh giá báo cáo và kiểm tra 51 trích dẫn: `../RESPONSE_TO_Q1_PROPOSAL_VI.md`.

Hình pH theo năm được sinh trong `build_research_visuals.py`, giữ missing và điểm 0,1 pH; không gán nguyên nhân thời tiết. Hai panel có thang tung riêng và caption nêu rõ. Lag-one correlation trong CSV dùng cặp ngày được quan sát, không phải predictor forward-fill. Đối chiếu báo cáo mới: `../RESPONSE_TO_VISUAL_REVIEW_VI.md`.
