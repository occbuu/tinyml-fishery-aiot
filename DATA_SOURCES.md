# Nguồn dữ liệu và trạng thái

Các tệp đã tải có SHA-256/URL cụ thể trong `data/download_manifest.json`. Thay đổi xử lý được ghi trong `prepare_data.py`; raw không bị sửa.

| Nguồn | Giấy phép | Trạng thái và cách dùng |
|---|---|---|
| [KU-MWQ V4](https://doi.org/10.17632/34rczh25kc.4) | CC BY 4.0 | Đã tải hai Excel độ sâu 30/60 cm; Arduino Mega; pH, nhiệt độ, turbidity. Benchmark pH, lưu ý chỉ một tuần dữ liệu. |
| [Aquaponics ESP8266 V2](https://doi.org/10.17632/yd36bx6f8f.2) | CC BY 4.0 | Đã tải raw 505.730 dòng và filtered; dùng raw cho benchmark pH. Source gắn PH-4502C, TDS, DS18B20/NodeMCU. |
| [Tilapia Montería V1](https://doi.org/10.17632/dgdr2kfbyt.1) | CC BY 4.0 | Đã tải 4.345 dòng có DateTime; benchmark DO 1 giờ. Không có mẫu DO <3 mg/L, không chứng minh cảnh báo hypoxia. |
| [Marine Institute Mace Head](https://erddap.marine.ie/erddap/info/sbe37_macehead/index.html) | CC BY 4.0 | Đã tải 01/05–31/07/2019, 4.416 dòng; temperature/salinity QC dùng được. Oxygen QC=0 trong lát cắt: loại khỏi target/features chính. |
| [Aquaculture biochemistry](https://doi.org/10.17632/y78ty2g293.1) | CC BY 4.0 | Đã tải 4.300 dòng, 14 biến/nhãn chất lượng; nhãn dựng theo ngưỡng, không phải sự kiện bệnh/thiệt hại đã xác nhận. Chỉ audit/inventory. |
| [Related transformed Colombia data](https://doi.org/10.17632/8s73jfvgr5.1) | CC BY 4.0 | Đã tải 37.284 dòng; lẫn scaled/physical variables, thiếu timestamp đầy đủ. Loại khỏi primary benchmark, không tính là replication độc lập. |
| [MLPerf Tiny v1.3](https://github.com/mlcommons/tiny_results_v1.3) | Xem LICENSE.md và submission notices đã lưu | Đã tải kết quả performance/power/accuracy/system cho hai board STM32 M4/M33, pin Git tree. Workload audio anomaly; không gán số đo đó cho model thủy sản/ESP32. |
| [Espressif ESP-NN](https://github.com/espressif/esp-nn), [ESP TFLite Micro](https://github.com/espressif/esp-tflite-micro) | Apache-2.0, kèm dependency notices | Đã tải README/LICENSE pin commit. Có benchmark kernel và person detection cho ESP32, C3, S3, P4; chỉ là tham chiếu workload vendor, không phải số đo mới của tác giả. |
| [VN 2017](https://doi.org/10.7910/DVN/HFMRNF), [VN 2018](https://doi.org/10.7910/DVN/FUCDMC), [VN 2019](https://doi.org/10.7910/DVN/VJEDSU) | CC BY 4.0 | Người dùng đã cung cấp raw tại DataVietNam. 2018/2019: dự báo DO/pH ngày kế tiếp và kinh tế vụ; 2017: inventory, không ép dùng forecast. |
| [Shrimp respirometry](https://doi.org/10.5281/zenodo.7971310), [Estuary telemetry](https://doi.org/10.5281/zenodo.3459610) | Metadata CC BY 4.0 | Chỉ metadata; tải bị Zenodo từ chối do lưu lượng mạng. Không bypass; không dùng làm empirical rows. |

Đường dẫn tải dữ liệu biển là projection API có giới hạn ba tháng; file CSV giữ dòng đơn vị và QC nguyên bản. Những bản ghi thiếu/khác đơn vị không được đổi thành số 0. TDS không được tự coi là salinity; oxygen µmol/kg không tự coi là mg/L; ammonia không rõ basis không tự coi là TAN-N.

| Nguồn Việt Nam bổ sung | Giấy phép | Phân tích |
|---|---|---|
| [Total Vibrio, Ca Mau 2022–2025](https://doi.org/10.5281/zenodo.22057734) | CC BY 4.0 | 679 mẫu cặp nước/vi sinh; train 2022–2023, val 2024, test 2025; đích đồng thời, không phải dự báo bệnh. |
| [Mangrove–shrimp chemistry](https://doi.org/10.5281/zenodo.14560499) | CC BY 4.0 | 180 giá trị mỗi biến lặp trong 5 nhóm hộ; mô tả hóa học, không coi 180 là 180 ao độc lập. |

Manifest Việt Nam: `data/vietnam_manifest.json`, kiểm SHA-256 cho tệp phân tích và MD5 gốc nơi metadata có cung cấp. Các ghi chú Guestbook trong metadata gốc ghi lại trạng thái lúc thu thập; trạng thái phân tích hiện hành do manifest Việt Nam xác định. Không thực thi code/notebook đi kèm nguồn. Không giải nén dữ liệu ảnh vệ tinh 1,17 GB để ghép vào bài toán cảm biến nước.
