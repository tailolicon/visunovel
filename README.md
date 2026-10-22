# visuNovel

Trang đọc tiểu thuyết tiếng Việt tĩnh, thiết kế mobile-first, chuẩn bị cho GitHub Pages.

## Quyền nội dung
Truyện demo trên website được sáng tác riêng cho bản thử nghiệm. *The Demon King Overrun by Heroes* (마왕인데 용사가 너무 많음) chỉ được giới thiệu bằng metadata; **không đăng bản dịch hay nguyên văn của tác phẩm nếu chưa có quyền chuyển ngữ và phân phối**.

## Chạy tại máy
```sh
python3 -m http.server 8000
```
Mở http://localhost:8000.

## GitHub Pages
Chọn **Settings → Pages → Build and deployment → Source: GitHub Actions**. Workflow `.github/workflows/pages.yml` tự triển khai trên push vào `main`. Với GitHub Free, repo cần public; GitHub Pro/Team có thể dùng Pages trên repo private.

## Cấu trúc
- `index.html` + `assets/`: UI, thư viện, đọc chương.
- `data/library.json` + `data/chapters/`: metadata và chương được duyệt.
- `translation/canon.json`: hồ sơ nhân vật, quan hệ hai chiều theo giai đoạn, thuật ngữ locked, trạng thái nguồn và quyền.
- `translation/PROTOCOL.md`: luật dịch cứng kế thừa các nguyên tắc hachimi-tl-vi.
- `translation/WORKER_START.md`: điều phối lượt thực thi stateless.
- `scripts/check.py` + `.github/workflows/check.yml`: kiểm thử và cổng xuất bản.

## Luật xuất bản
1. Chỉ dịch/đăng nội dung được cấp quyền hoặc thuộc phạm vi công cộng; không lấy bản dịch không được phép làm corpus.
2. Bằng chứng cảnh > ma trận xưng hô theo giai đoạn > thuật ngữ đã khóa > hướng dẫn văn phong. Tình tiết thay đổi quan hệ cần ghi nhận trước khi đổi cách gọi.
3. Tách discovery, draft, QA và publish; không tự động nâng ứng viên thuật ngữ thành luật.
4. Mỗi chương: quyền hợp lệ + nguồn đã pin + biên tập/QA đạt + kết quả khớp glossary mới cho phép xuất bản.
