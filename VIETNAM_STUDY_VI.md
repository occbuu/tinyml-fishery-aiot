# Nghiên cứu Việt Nam trong V4

Paper: `../Paper2_FisheryAIoT_V4_Research/main.tex`. Code chính: `vietnam_benchmark.py`; bảng/hình do `build_vietnam_artifacts.py` sinh. `DataVietNam/` được đọc nguyên trạng, không sửa workbook gốc và không chạy code/notebook của nguồn.

## Nguồn và cách sử dụng

| Nguồn | Phân tích |
| --- | --- |
| Nutritious Pond 2018, DOI `10.7910/DVN/FUCDMC` | Sáu nhãn ao; train đầu năm vụ và validation cuối vụ, bảng kinh tế |
| Nutritious Pond 2019, DOI `10.7910/DVN/VJEDSU` | Sáu nhãn ao; test khác năm cho DO/pH ngày kế tiếp, bảng kinh tế |
| Ca Mau Vibrio 2022–2025, DOI `10.5281/zenodo.22057734` | 679 mẫu cặp nước/vi sinh; 303 train, 184 validation, 192 test theo năm |
| Mangrove–shrimp chemistry, DOI `10.5281/zenodo.14560499` | 180 giá trị mỗi biến, lặp trong năm nhóm hộ; mô tả hóa học và chênh lệch DO trước/sau trao đổi nước |

Các nguồn khác trong `DataVietNam` được ghi inventory theo metadata; không tự coi khảo sát hộ, số liệu vật chủ, metagenome hoặc ảnh ao là chuỗi cảm biến nước. Không giải nén archive vệ tinh 1,17 GB. Nguồn 2016–2017 có sẵn nhưng định dạng/nhịp lấy mẫu khác; chưa dùng để suy diễn forecast hằng ngày.

`data/vietnam_manifest.json` ghi 21 tệp phân tích/provenance, SHA-256, metadata giấy phép, đường dẫn tương đối từ thư mục gốc và MD5 nơi kho nguồn cung cấp. Hiện có 11 MD5 đối chiếu được, gồm container RAR Vibrio; các thành viên giải nén có SHA-256 riêng. Đây không phải 21 dataset độc lập. Inventory có 13 thư mục nguồn, chỉ bốn nhóm được phân tích định lượng ở đây.

## Phương pháp

- Daily: đặc trưng lag/rolling theo riêng từng năm–ao, không nối cuối ao này sang đầu ao khác. Nhãn là ngày lịch kế tiếp; không đổi thành quan sát kế tiếp nếu thiếu ngày. Không điền target.
- Train: 65% ngày đầu năm vụ 2018, bỏ nhãn chạm ranh giới validation. Validation từ 04/06/2018; test toàn bộ forecast đủ điều kiện năm 2019. Không refit sau validation; không giả định các nhãn ao qua năm là hộ độc lập.
- Giữ nguyên bảy baseline, siêu tham số cố định và quy tắc chọn model theo validation, ngân sách coefficient payload 4 KiB, sai số không quá +5% so với tốt nhất đủ ngân sách, ưu tiên nhỏ nhất. Payload không phải tổng RAM/flash.
- So sánh TargetOnly, MultiSensor và NoTarget. Không dùng tên hộ, tổng thu hoạch, lợi nhuận hoặc thông tin cuối vụ làm feature. Không dùng feed/fuel tổng ngày vì chưa chắc đã có lúc quan sát sáng.
- Daily DO header không ghi rõ đơn vị: giữ thang số nguồn, không gộp sai số với DO mg/L của nguồn khác. Giữ pH 0.1 và nhiệt độ 2.9 trong kết quả chính, có sensitivity domain-QC riêng; không tự chữa lỗi nhập liệu.
- Bootstrap 2.000 lần theo sáu nhãn ao test, giữ chuỗi trong ao; chỉ mô tả bộ mẫu, không phải khoảng tin cậy cho toàn Việt Nam.
- Vibrio: đồng thời, không phải dự báo ngày mai hoặc nhãn bệnh. Train 2022–2023, validation 2024, test 2025. Không có pond ID bền vững nên không dùng persistence hoặc tuyên bố unseen-pond performance. Chỉ thay chuỗi non-detect rõ ràng; so sánh zero/half-LOQ/LOQ. Không đưa raw outcome/log outcome vào predictor.
- Kinh tế: dùng VND danh nghĩa 2018–2019, tự tính tỷ trọng feed/energy từ lượng tiền, kiểm gross−cost=net. Công thức hòa vốn chỉ tính mức giảm chi phí năng lượng *cần đạt* với ngân sách theo giả định; không phải mức tiết kiệm đã quan sát hoặc giá 2026.

## Kết quả chính

Validation chọn persistence cho cả DO và pH ngày kế tiếp: MAE test lần lượt 0.2128 trên thang DO nguồn (441 forecast) và 0.1945 pH (468 forecast). Ridge có pH test tốt hơn nhưng không được chọn từ validation; không đổi selector theo test. Bỏ lịch sử target làm cả hai kết quả chọn theo validation kém đi.

Với Vibrio, Field4, Field5 và Laboratory10 đều chọn training mean, MAE 0.9329 log units ở primary half-LOQ. Đây là giới hạn quan sát theo thiết kế thử này; không phải bằng chứng cảm biến nước thay được xét nghiệm hoặc một model chẩn đoán bệnh.

Chi phí vận hành trung vị sáu vụ mỗi năm là 28,85 triệu VND (2018) và 47,90 triệu VND (2019). Tỷ trọng năng lượng trung vị 9,7% và 14,3%; feed 38,9% và 61,8%. Không gán chênh lệch năm/nhóm cho AI. Với giả định 600.000 VND/năm và hai vụ, mức giảm chi phí năng lượng cần đạt có trung vị 6,8% trên 12 vụ; đó là ngưỡng yêu cầu trong thang giá lịch sử, chưa phải ROI thực tế.

## Chạy lại

Từ thư mục gốc dự án, giữ `DataVietNam/` cạnh `simulateCode-v4/`:

```powershell
python -m pip install -r simulateCode-v4/requirements.txt
python simulateCode-v4/run_all.py
python -m unittest discover -s simulateCode-v4 -p 'test_*.py'
```

Nếu đã có kết quả high-frequency và chỉ cần chạy Việt Nam rồi sinh lại bảng:

```powershell
python simulateCode-v4/run_all.py --only vietnam artifacts
```

LaTeX: vào `Paper2_FisheryAIoT_V4_Research` rồi chạy `pdflatex main.tex` hai lần. Các tệp `results/vietnam_*` có trial/prediction, tóm tắt và kinh tế; `vietnam_summary.json` giữ audit daily/weekly, sensitivity, model warnings và phương pháp chia tập. Không có phép đo board mới, thử can thiệp ao, xác nhận root-cause hỏng hoặc cam kết lợi nhuận từ phiên này.
