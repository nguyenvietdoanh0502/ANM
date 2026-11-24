# Kết quả kiểm chứng

Thực hiện ngày 15/11/2026 tại `E:\ANM`, Windows, Python 3.13.0; phiên bản mật mã và thông tin máy nằm trong `output/reference_run/metadata.json`.

| Hạng mục | Kết quả |
| --- | --- |
| pytest | 54 đạt, 0 thất bại, 0 lỗi |
| Mật mã | Bốn tổ hợp ECDSA/RSA-PSS × SHA-256/SHA-512; vector băm chuẩn; ký/xác minh chéo giữa API digest và API thông điệp |
| Dữ liệu | Rỗng, tiếng Việt, nhị phân, đúng giới hạn 10 MiB, vượt giới hạn |
| Trường hợp sai | Sửa byte/chữ ký, sai khóa/hash/mật khẩu, JSON/PEM/Base64 lỗi, trường trùng, khóa ngoài cấu hình |
| Giao diện | Streamlit AppTest: tạo khóa, ký, xác minh, đổi byte, đổi đầu vào, điều hướng, xóa phiên, RSA với SHA-512 |
| Mẫu công khai | Cả bốn chữ ký hợp lệ với thông điệp gốc và thất bại với thông điệp bị sửa |
| HTTP | `http://127.0.0.1:8501/_stcore/health` trả 200, nội dung `ok` |
| Benchmark đầy đủ | 7.240 dòng đo; CSV tổng hợp, kích thước, metadata và sáu biểu đồ |
| Báo cáo | DOCX/PDF 37 trang; mục lục cập nhật; đã kiểm tra ảnh từng trang |

Lệnh kiểm thử cuối:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short -p no:cacheprovider --basetemp=E:/ANM/tmp/pytest-final --junitxml=output/test-results.xml --disable-warnings
```

Khi chạy lại, có thể bỏ `--basetemp` nếu thư mục tạm hệ thống ghi được, hoặc chọn thư mục tạm mới trong workspace. Có 304 cảnh báo ngừng hỗ trợ từ các phụ thuộc vẽ biểu đồ; không có ca kiểm thử thất bại. Kết quả máy đọc được nằm trong `output/test-results.xml`.

Lệnh đo đầy đủ là `python -m ecc_lab.benchmark --output output/reference_run`; khi tái lập hãy dùng thư mục mới, ví dụ `output/experiments`, để giữ lần đo tham chiếu. Mẫu khởi động không nằm trong 7.240 dòng. Thứ tự cấu hình cố định, máy không cô lập tiến trình nền; kết quả chỉ đại diện cho lần chạy được ghi metadata.

Chưa kiểm tra bố cục bằng trình duyệt thật: trình duyệt tích hợp không khả dụng, truy cập ứng dụng Edge hết thời gian chờ phê duyệt. AppTest kiểm tra hành vi widget, không chứng minh bố cục trên mọi màn hình. Các hình giao diện trong báo cáo vì vậy được ghi rõ là sơ đồ chức năng.

Kiểm thử chéo dùng cùng thư viện cryptography/OpenSSL, chưa phải kiểm thử liên vận với hệ thống độc lập. Phạm vi sản phẩm là demo học tập trên localhost, chữ ký tách rời; chưa có CA, dấu thời gian hoặc chữ ký PDF nhúng.
