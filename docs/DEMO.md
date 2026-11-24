# Kịch bản trình bày trong 5 đến 7 phút

Chuẩn bị: chạy `python -m streamlit run app.py`, mở http://127.0.0.1:8501. Chuẩn bị thư mục `samples` và kết quả `output/reference_run`. Không cần Internet sau khi đã cài thư viện.

1. **0:00–0:40 — Bài toán.** Dữ liệu có thể bị sửa khi trao đổi. Chữ ký số cho phép kiểm tra tính toàn vẹn và quan hệ với khóa công khai. SHA tạo digest; ECDSA/RSA-PSS ký thông qua digest.
2. **0:40–1:30 — Tạo khóa.** Vào Quản lý khóa, tạo ECDSA P-256. Chỉ ra khóa công khai, fingerprint và chức năng lưu khóa bí mật có mật khẩu.
3. **1:30–2:30 — Ký.** Nhập văn bản tiếng Việt, chọn SHA-256, ký rồi kiểm tra chữ ký vừa tạo. Tải dữ liệu đã ký, chữ ký JSON và khóa công khai.
4. **2:30–3:10 — Phát hiện sửa đổi.** Chọn Sửa một byte và xác minh lại. Giải thích vì sao chữ ký cũ không xác minh được dữ liệu mới.
5. **3:10–4:10 — Xác minh độc lập.** Mở tab Xác minh chữ ký. Nạp `samples/message.txt`, `samples/ecdsa_public.pem`, `samples/ecdsa_sha-256.json`: hợp lệ. Thay dữ liệu bằng `message_tampered.txt`: thất bại. Luồng này không cần khóa bí mật.
6. **4:10–4:50 — SHA.** Vào Khám phá SHA, nhập `abc`, chỉ ra digest 32/64 byte và sự thay đổi khi đổi đầu vào.
7. **4:50–6:20 — So sánh.** Mở kết quả thực nghiệm đi kèm. Chỉ ra mức an toàn tương đương của P-256/RSA-3072; xem tạo khóa, ký digest, xác minh digest, băm + ký. Nêu máy và số lần đo.
8. **6:20–7:00 — Kết luận.** Nêu kết quả thực đo, giới hạn một máy/một lần chạy và vai trò chứng thư số khi xác nhận danh tính.

## Câu hỏi ôn tập

- **Vì sao không so P-256 với RSA-256?** Cùng số bit khóa không có nghĩa cùng mức an toàn. Mốc so sánh là an toàn cổ điển khoảng 128 bit.
- **SHA có mã hóa thông điệp không?** Không; hàm băm tạo digest cố định, không có thao tác giải mã.
- **Vì sao dùng Prehashed?** Digest đã được tính riêng để hiển thị và đo; Prehashed báo cho thư viện rằng đầu vào đã được băm.
- **Vì sao hai chữ ký cùng thông điệp có thể khác nhau?** ECDSA dùng nonce và RSA-PSS dùng salt; cả hai vẫn có thể hợp lệ.
- **Ai sở hữu khóa công khai?** Demo không xác thực danh tính ngoài đời. Cần phân phối khóa qua kênh tin cậy hoặc chứng thư số.
- **SHA-512 có làm P-256 đạt 512 bit an toàn không?** Không; mức an toàn phụ thuộc các thành phần và cách kết hợp.
- **Ký PDF có hiển thị trong Adobe Reader không?** Demo ký byte bằng chữ ký tách rời, không tạo chữ ký PAdES nhúng.

Nếu benchmark mất thời gian, dùng kết quả đi kèm và nêu rõ metadata. Nếu mất khóa phiên, nhập lại khóa đã lưu hoặc tạo khóa mới và ký lại; khóa mới không xác minh được chữ ký của khóa cũ.
