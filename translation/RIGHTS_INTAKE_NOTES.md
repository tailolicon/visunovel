# Quy trình nguồn và quyền — Role 1

## Định vị truyện
- Novel ưu tiên **chương 137 trở đi**. Không trộn số chương novel và manhwa.
- Các mốc 154–156 là **ứng viên** hoàn tất chân/di chuyển; chưa xác minh chương bước đi đầu tiên.
- Đến chương 160 đã có bằng chứng hồi cố về việc tháp đổi vị trí và ẩn dưới biển.
- Xem `translation/reading_queue.json`, `translation/ARC_137.md` và `translation/source_registry.json`. Không lưu nguyên chương hoặc bản dịch từ website vào repository.

## Nhập nguồn đọc cá nhân (chỉ metadata)
Chỉ dùng tệp TXT/Markdown do người dùng chủ động chuẩn bị **ngoài thư mục Git**:

```sh
python3 tools/local_intake.py ~/Books/chapter-137.txt --chapter 137 --dry-run
python3 tools/local_intake.py ~/Books/chapter-137.txt --chapter 137
```

Công cụ chỉ đọc file để tính SHA-256 và tạo manifest tại `~/.local/share/visunovel-private/intake/`; **không** sao chép văn bản, không truy cập Internet, không gọi mô hình, không upload GitHub. Chỉ nhận chương >= 137 trong đợt ưu tiên này, file <= 1 MiB, không tự ghi đè khi hash thay đổi. Nếu muốn dịch bản nháp tại máy, đó là công cụ riêng `tools/personal_translate.py` và yêu cầu người dùng tự chủ động cấu hình API (văn bản sẽ được gửi tới nhà cung cấp API).

## Điều kiện xuất bản công khai
Đọc cá nhân, phi thương mại hoặc có URL truy cập **không** đồng nghĩa có quyền đăng bản dịch lên GitHub Pages. Trước khi chuyển `pending` sang `cleared`, cần có tài liệu quyền cho **chuyển ngữ và phân phối web**, tên bên cấp quyền, lãnh thổ, thời hạn, bản nguồn pin SHA-256 và kiểm duyệt biên tập. Hiện chưa có bằng chứng cấp phép, nên mọi cờ quyền công khai phải giữ `false`.

## Kiểm thử
```sh
python3 scripts/check_source_queue.py
python3 -m unittest discover -s tests -p 'test_source_queue.py' -v
python3 -m unittest discover -s tests -p 'test_local_intake.py' -v
python3 scripts/check.py
```

Workflow `.github/workflows/source-intake.yml` kiểm tra metadata, quyền, tệp đầu vào riêng tư và cổng xuất bản. `.github/workflows/pages.yml` không bị sửa; bản nháp riêng tư không thuộc Pages artifact.
