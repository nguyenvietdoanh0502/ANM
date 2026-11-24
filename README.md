# ECC Signature Lab

Demo tiếng Việt cho đề tài **Nghiên cứu hệ mật đường cong elliptic và ứng dụng tạo chữ ký số**, có ECDSA P-256, RSA-PSS 3072 bit, SHA-256/SHA-512, thực nghiệm và báo cáo Word/PDF.

## Chạy trên Windows

Yêu cầu Python 3.12 trở lên do phiên bản NumPy/ContourPy trong bộ thư viện đã khóa. Đã kiểm chứng với Python 3.13 trên Windows. Môi trường Python 3.11 dự kiến trong kế hoạch không khởi chạy được trên máy hiện tại.

```powershell
cd E:\ANM
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở **http://127.0.0.1:8501**. Sau khi cài thư viện có thể chạy `./run.ps1`. Ứng dụng chỉ lắng nghe localhost, không cần Internet khi sử dụng. Trên Linux/macOS thay đường dẫn Python bằng `.venv/bin/python`.

## Thực hành

1. **Quản lý khóa:** tạo ECDSA hoặc RSA; tải khóa công khai, lưu khóa bí mật với mật khẩu.
2. **Ký và xác minh:** nhập văn bản/tệp, chọn hàm băm, ký và tải JSON. Người nhận dùng dữ liệu gốc, chữ ký và khóa công khai để xác minh.
3. **Sửa một byte và xác minh lại:** minh họa dữ liệu bị thay đổi làm chữ ký không hợp lệ.
4. **Khám phá SHA:** hiển thị hai digest và số bit thay đổi.
5. **Thực nghiệm:** chạy phép đo hoặc mở kết quả đi kèm; xuất CSV và PNG.

Văn bản dùng UTF-8, giữ nguyên khoảng trắng/xuống dòng. Tệp xử lý theo byte gốc, tối đa 10 MiB. Có thể ký PDF/ảnh/tệp bất kỳ, nhưng đây là chữ ký tách rời. Kết quả hợp lệ gắn với khóa công khai, chưa xác nhận danh tính chủ khóa qua CA.

## Kiểm thử và thực nghiệm

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=output/test-results.xml
.\.venv\Scripts\python.exe -m ecc_lab.benchmark --output output/experiments
```

Thêm `--quick` để kiểm tra công cụ với ít vòng hơn. Lần đầy đủ dùng 10 vòng khởi động, 100 lần đo/phép; tạo khóa 20 lần/thuật toán. Dữ liệu: 1 KiB, 100 KiB, 1 MiB, 10 MiB, sinh cố định trước khi đo. Khóa/nonce/salt vẫn do thư viện sinh ngẫu nhiên an toàn.

Đầu ra: `raw.csv`, `summary.csv` (count/median/mean/std, ms), `sizes.csv`, `metadata.json`, sáu biểu đồ PNG. Tách thời gian băm, ký digest, xác minh digest, băm + ký, băm + xác minh, tạo khóa. IO, tuần tự hóa khóa và giao diện nằm ngoài khoảng đo. Độ lệch chuẩn dùng mẫu (ddof=1).

`output/reference_run` là lần đo dùng trong báo cáo. Dùng `output/experiments` cho lần chạy mới. Kết quả trên một máy/thứ tự cố định có thể chịu ảnh hưởng tải nền, nhiệt độ và chế độ nguồn; không mặc định ECC nhanh hơn RSA ở mọi thao tác.

## Cấu trúc

| Đường dẫn | Vai trò |
| --- | --- |
| `app.py` | Bốn khu vực Streamlit |
| `ecc_lab/crypto.py` | Mật mã và định dạng chữ ký |
| `ecc_lab/benchmark.py` | Phép đo và xuất CSV/PNG |
| `ecc_lab/toy_curve.py` | Ví dụ toán học nhỏ, không dùng để ký thực tế |
| `tests/` | Kiểm thử mật mã, benchmark và giao diện |
| `samples/` | Dữ liệu, chữ ký mẫu và khóa công khai |
| `docs/DEMO.md` | Kịch bản trình bày và ôn tập |
| `docs/report_content.py` | Nội dung nguồn báo cáo |
| `scripts/build_report.py` | Tạo lại báo cáo từ nội dung và số liệu |
| `output/report/` | Báo cáo Word/PDF |

## Quy ước mật mã

- ECDSA: SECP256R1 (P-256), chữ ký ASN.1 DER gồm `(r,s)`; nonce để thư viện xử lý.
- RSA-PSS: modulus 3072 bit, e=65537; MGF1 cùng hàm băm; salt dài 32/64 byte bằng digest.
- Tính digest một lần và ký bằng `Prehashed`. Xác minh băm lại dữ liệu gốc.
- Khóa công khai PEM/SPKI; khóa bí mật PKCS8 PEM dùng `BestAvailableEncryption` với mật khẩu UTF-8. Không lưu khóa bí mật tự động hoặc cache giữa các phiên.
- Fingerprint là SHA-256 của SPKI DER, dùng để đối chiếu, không tự xác nhận danh tính.

Chữ ký JSON v1 có đúng năm trường, từ chối trường trùng hoặc cấu hình không hỗ trợ:

```json
{
  "version": 1,
  "algorithm": "ECDSA",
  "hash": "SHA-256",
  "key_profile": "P-256",
  "signature_base64": "<Base64 của chữ ký DER>"
}
```

RSA dùng `RSA-PSS` và `RSA-3072-e65537`, chữ ký gốc 384 byte. Metadata mô tả cách xác minh; không chứa danh tính/thời điểm đã được chứng thực. Dữ liệu được ký là byte gốc, không phải JSON. JSON tối đa 16 KiB, khóa tối đa 64 KiB.

## Báo cáo và mẫu

Điền trường, giảng viên và sinh viên ở bìa trước khi nộp. Kết quả trong báo cáo lấy từ lần đo thật. Xem `output/report/BUILD_NOTES.md` về cách tạo và kiểm chứng tài liệu.

Bản bàn giao gồm báo cáo 37 trang, 54 kiểm thử đạt và 7.240 mẫu đo. Chi tiết và giới hạn kiểm chứng ở [docs/VALIDATION.md](docs/VALIDATION.md). Gói `output/ECC_Signature_Lab.zip` chứa mã nguồn, mẫu công khai, dữ liệu và báo cáo; không chứa môi trường `.venv`. Có thể tạo lại bằng `python -m scripts.package_release`.

Tạo lại mẫu công khai (tạo khóa/chữ ký mới, không lưu khóa bí mật):

```powershell
.\.venv\Scripts\python.exe -m scripts.make_samples
```

Nguồn chính: [FIPS 186-5](https://csrc.nist.gov/pubs/fips/186-5/final), [FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final), [SP 800-186](https://csrc.nist.gov/pubs/sp/800/186/final), [SP 800-57](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final), [RFC 8017](https://www.rfc-editor.org/rfc/rfc8017.html).

Tạo lại báo cáo trên Windows (cần các phông Times New Roman và Arial):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-report.txt
.\.venv\Scripts\python.exe -m scripts.make_figures
.\.venv\Scripts\python.exe -m scripts.build_report
# Khi có Microsoft Word: cập nhật mục lục và xuất PDF khớp chính xác Word
.\scripts\export_word.ps1
```

Trình dựng mặc định đọc `output/reference_run`. Để dùng lần đo khác, cập nhật thư mục dữ liệu trong `scripts/experiment_sections.py` và `scripts/build_report.py`. PDF trực tiếp từ ReportLab có cùng nội dung nhưng phân trang khác; PDF bàn giao được xuất từ Word và khớp DOCX.
