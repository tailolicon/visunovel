# Chế độ dịch cá nhân

Công cụ này **không tự lấy chương từ website**. Bạn chủ động chuẩn bị một chương văn bản `.txt`/`.md` mà mình có quyền truy cập, và lựa chọn nhà cung cấp mô hình. Văn bản sẽ được gửi đến API mà **bạn cấu hình** để tạo bản dịch nháp, nên hãy xem điều khoản và chính sách dữ liệu của nhà cung cấp.

Tập tin riêng tư chỉ được lưu ở máy tính, mặc định `~/.local/share/visunovel-private/`. Trên Windows đường dẫn dựa vào thư mục home của Python. Không commit, không chạy như server công khai.

## Sử dụng
```sh
python3 tools/personal_translate.py /path/to/chapter-137.txt --chapter 137 --dry-run
# Đặt biến môi trường VISU_API_KEY, VISU_API_URL (OpenAI-compatible), VISU_MODEL
python3 tools/personal_translate.py /path/to/chapter-137.txt --chapter 137
```

Muốn gợi ý ngữ cảnh xưng hô cho chương, tạo tệp cá nhân `context-137.txt` gồm tên người nói, người nghe, quan hệ và cách xưng hô **đã được xác minh**, rồi chạy với `--context /path/to/context-137.txt`.

Bản nháp được đánh dấu `needs_review` mặc định. Nghi vấn xưng hô sẽ hiện `[CẦN_XƯNG_HÔ]`. Dữ liệu nguyên tác/bản dịch không được đưa vào GitHub Pages. Mở [personal.html](../personal.html) và chọn file `.vi.txt` để đọc trong trình duyệt.

Không tự ý thay `needs_review` thành `passed`: việc biên tập cần so với văn bản nguồn, nhiều chương liền kề và sổ quan hệ của nhân vật.
