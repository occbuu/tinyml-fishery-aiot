# ESP32 với PlatformIO + Wokwi

Dự án chạy Ridge, Mean, Persistence hoặc Tree4 trên cùng fixture pH ao, có kiểm tra kết quả, benchmark block và demo trạng thái đầu vào. Dùng ESP32 thông thường; không camera, GPU, cloud inference hay relay thật. Potentiometer chỉ là nguồn điện áp ảo, không mô phỏng điện hóa của đầu dò DO.

## Trạng thái đã kiểm chứng

- Đã build thành công cả năm môi trường bằng PlatformIO 6.2.0, `espressif32@6.10.0`, Arduino ESP32 2.0.17, GCC Xtensa 8.4.0, cấu hình 240 MHz.
- Đã đối chiếu C với Python trên host: 20 reference (năm model × bốn task), 5.440 dự báo, gồm missing-input overlays. Không dùng số đo host để thay latency của ESP32.
- `wokwi-cli lint` phiên bản 0.29.0 trả mã 0; có một thông tin về board-definition `board-esp32-devkit-c-v4`, không có lỗi nối chân.
- Chưa chạy Wokwi vì chưa cấu hình token; chưa có bo thật. Không có số latency/heap mô phỏng bị tạo giả. Có ELF/BIN thực do compiler sinh trong `.pio/build/`.

## Chạy trên máy khác

Từ thư mục gốc dự án:

```powershell
python -m pip install -r simulateCode-v4/requirements.txt
python -m pip install -r simulateCode-v4/requirements-embedded.txt
python simulateCode-v4/prepare_embedded.py
python -m platformio run -d simulateCode-v4/firmware/wokwi_platformio
python simulateCode-v4/collect_embedded.py
```

`collect_embedded.py` đọc ELF bằng pyelftools, ghi hash và kích thước section vào `results/esp32_build_summary.json`. Nó không suy diễn peak SRAM. Có thể đặt `PLATFORMIO_CORE_DIR` vào thư mục riêng trước build; phiên hiện tại dùng `.tooling/platformio-core/` ở thư mục gốc. Nếu build bằng môi trường riêng, dùng Python tương ứng; `--pyelftools-path` hỗ trợ đọc pyelftools từ môi trường đó.

## Wokwi trong VS Code

Mở thư mục dự án này bằng VS Code, cài/cấu hình Wokwi và PlatformIO theo tài liệu chính thức. Build trước rồi chạy **Wokwi: Start Simulator**. `wokwi.toml` mặc định trỏ tới môi trường Ridge `esp32dev`. Đổi hai đường dẫn `.pio/build/<env>/` sang `mean`, `persistence`, `tree` hoặc `baseline` để chạy ảnh khác.

Các liên kết chính thức: [Wokwi + PlatformIO](https://docs.wokwi.com/vscode/platformio), [Wokwi CLI](https://docs.wokwi.com/wokwi-ci/cli-usage), [ESP32 Dev Module](https://docs.platformio.org/en/stable/boards/espressif32/esp32dev.html).

## Wokwi CLI

Cài CLI từ [bản phát hành chính thức](https://github.com/wokwi/wokwi-cli/releases). Tạo token trong tài khoản Wokwi rồi cấu hình biến môi trường `WOKWI_CLI_TOKEN` cục bộ theo hướng dẫn của họ; không đưa token vào code, Git hoặc chat. Khi đã cấu hình:

```powershell
python simulateCode-v4/firmware/wokwi_platformio/run_simulation.py --env esp32dev
python simulateCode-v4/firmware/wokwi_platformio/run_simulation.py --env mean
python simulateCode-v4/firmware/wokwi_platformio/run_simulation.py --env persistence
python simulateCode-v4/firmware/wokwi_platformio/run_simulation.py --env tree
python simulateCode-v4/firmware/wokwi_platformio/run_simulation.py --env baseline
```

Có thể dùng `--cli` với đường dẫn tuyệt đối tới executable. Nếu thiếu token, script chỉ ghi trạng thái chưa chạy; không tạo dữ liệu đo. Khi chạy được, script lưu log và JSON dưới `simulateCode-v4/results/`, tách khỏi kết quả dự báo nước. Mỗi phiên có timeout 60 giây mô phỏng.

## Đọc log đúng phạm vi

- `REPLAY_PASS`: các dự báo trong fixture của model đang chọn khớp tolerance; không chứng nhận độ chính xác ao mới.
- `BLOCK`: 40 block × 1.000 lời gọi; UART nằm ngoài block. Chia elapsed cho calls để có thời gian *trong môi trường đã chạy*. Ghi rõ `Wokwi` nếu là giả lập, `physical board` nếu đo bo thật. Chạy baseline tương ứng; model constant có thể bị compiler tối ưu mạnh.
- `MEMORY`: free heap và minimum free heap của cả chương trình. Static data/BSS trong ELF, stack high-water và heap là các đại lượng khác nhau. `stack_high_water_raw` phải diễn giải theo đúng phiên bản framework; không tự gộp thành peak SRAM.
- `VIRTUAL_INPUT`: GPIO34 đọc potentiometer 0–10 trên thang demo; nút GPIO27 tạo INVALID/UNKNOWN. Yêu cầu bảo vệ thấp/invalid độc lập với dự báo pH. Không có đóng quạt thật hoặc nhãn “ao an toàn”.

Các array fixture/framework/logging nằm trong flash của firmware thử. Vì linker có thể bỏ code hoặc hằng không dùng, chênh flash so với baseline không phải kích thước model thuần. Kích thước image/section không phải dung lượng flash đã đo sau nạp; cần giữ firmware hash khi chạy thực.
