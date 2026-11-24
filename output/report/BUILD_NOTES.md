# Thông tin bản báo cáo bàn giao

Ngày tạo: 15/11/2026. Báo cáo gồm **37 trang**, trong đó nội dung sáu chương nằm ở trang 5–35 (31 trang). Các trang còn lại là bìa, tóm tắt, mục lục, tài liệu tham khảo và phụ lục.

- `Bao_cao_ECC_Chu_ky_so.docx`: bản chỉnh sửa được; mục lục tự động đã cập nhật.
- `Bao_cao_ECC_Chu_ky_so.pdf`: xuất từ chính bản Word, cùng phân trang.
- `figures/`: hình toán học, kiến trúc và sơ đồ chức năng giao diện.
- Điền trường, khoa, giảng viên, họ tên, mã sinh viên và lớp trên bìa trước khi nộp; điều chỉnh theo mẫu chính thức của khoa nếu có.

## Nguồn nội dung và số liệu

Nội dung nằm trong `docs/report_content.py` và `scripts/experiment_sections.py`. Phần thực nghiệm đọc `output/reference_run` và kết quả kiểm thử đọc `output/test-results.xml`. Bản này dùng 7.240 mẫu đo thực tế và kết quả 54 kiểm thử đạt. Các số đo không phải số liệu minh họa tự đặt.

Hình giao diện là **sơ đồ chức năng**, có ghi chú ngay dưới hình; không phải ảnh chụp trình duyệt. Giao diện đã kiểm thử bằng Streamlit AppTest và máy chủ đã trả HTTP 200 ở health endpoint. Chưa kiểm tra bố cục bằng trình duyệt thật vì công cụ trình duyệt không khả dụng và yêu cầu truy cập ứng dụng hết thời gian chờ.

## Tạo lại

Chạy từ thư mục gốc dự án trên Windows, có Times New Roman và Arial:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-report.txt
.\.venv\Scripts\python.exe -m scripts.make_figures
.\.venv\Scripts\python.exe -m scripts.build_report
.\scripts\export_word.ps1
```

Lệnh cuối cần Microsoft Word đã cài, cập nhật mục lục và thay PDF ReportLab bằng PDF xuất từ Word. Nếu sửa thông tin bìa trực tiếp trong Word, chỉ chạy lệnh cuối để giữ các sửa đổi. Chạy lại `build_report` sẽ tạo mới báo cáo từ mã nguồn.

Phiên tạo tài liệu này dùng Python 3.12.14 của bộ công cụ tài liệu, python-docx 1.2.0 và ReportLab 4.4.9. Ứng dụng/thực nghiệm dùng môi trường riêng Python 3.13.0. Không có LibreOffice nên trình render dùng LibreOffice không chạy được; đã dùng Word qua COM để xuất PDF, rồi Poppler để render ảnh từng trang.

Đã xem toàn bộ 37 trang ở dạng ảnh: kiểm tra tiếng Việt, công thức, bảng, hình, mục lục và phân trang. Đã sửa căn lề tài liệu tham khảo, giữ hàng bảng nguyên vẹn, bỏ viền tiêu đề không phù hợp. Sau lần sửa cuối, PDF vẫn 37 trang; trang thay đổi được render và kiểm tra lại. Bản PDF tạo trực tiếp bằng ReportLab có phân trang riêng, không phải bản PDF cuối bàn giao.

Để dùng số liệu đo khác, đổi đường dẫn nguồn trong `scripts/experiment_sections.py` và `scripts/build_report.py`, tạo lại tài liệu, cập nhật mục lục rồi kiểm tra lại các trang.
