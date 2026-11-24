"""Run with: python -m streamlit run app.py"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ecc_lab import crypto as c
from ecc_lab.benchmark import BenchmarkConfig, OPERATIONS, chart_png, run_benchmark

st.set_page_config(page_title="ECC Signature Lab", page_icon="🔐", layout="wide")
st.markdown("""<style>
.block-container {max-width:1200px; padding-top:2rem;}
h1 {letter-spacing:-.035em;} h2 {letter-spacing:-.02em;}
[data-testid=stMetric] {background:#fff; border:1px solid #e3e9f1; border-radius:12px; padding:14px 18px;}
.eyebrow {font-size:.78rem; letter-spacing:.18em; color:#087f8c; font-weight:700; margin-bottom:.4rem;}
.flow {padding:16px 20px; background:#e6f3f2; border-radius:12px; color:#175b61; margin:12px 0 24px; line-height:1.8;}
[data-testid=stSidebar] {border-right:1px solid #e3e9f1;}
</style>""", unsafe_allow_html=True)


def invalidate():
    for name in ("signed", "signed_context", "verified", "changed_verification"):
        st.session_state.pop(name, None)


def set_key(key):
    st.session_state.private_key = key
    invalidate()


def input_bytes(prefix, default="Tôi xác nhận nội dung bài tập lớn An ninh mạng."):
    mode = st.radio("Nguồn dữ liệu", ["Văn bản", "Tệp"], horizontal=True, key=prefix + "_mode", on_change=invalidate)
    if mode == "Văn bản":
        value = st.text_area("Nội dung UTF-8", default, key=prefix + "_text", height=130, on_change=invalidate)
        data = value.encode("utf-8")
    else:
        uploaded = st.file_uploader("Chọn tệp bất kỳ · tối đa 10 MiB", key=prefix + "_file", on_change=invalidate)
        if uploaded is None:
            return None
        data = uploaded.getvalue()
    c.validate_data(data)
    st.caption(f"{len(data):,} byte · giữ nguyên nội dung, khoảng trắng và xuống dòng")
    return data


with st.sidebar:
    st.markdown("## 🔐 ECC Lab")
    st.caption("AN NINH MẠNG · CHỮ KÝ SỐ")
    page = st.radio("Không gian thực hành", ["Ký và xác minh", "Quản lý khóa", "Khám phá SHA", "Thực nghiệm"], label_visibility="collapsed")
    st.divider()
    key = st.session_state.get("private_key")
    if key:
        st.success(f"Đã nạp khóa {c.key_algorithm(key)}")
        st.caption("Fingerprint SHA-256")
        st.code(c.fingerprint(key.public_key())[:24] + "…", language=None)
    else:
        st.info("Tạo hoặc nhập khóa để bắt đầu ký.")
    st.caption("P-256 / RSA-3072\n\nSHA-256 / SHA-512\n\nChạy trên máy cá nhân")
    if st.button("Xóa phiên làm việc", use_container_width=True):
        for state_key in list(st.session_state):
            del st.session_state[state_key]
        st.rerun()

st.markdown('<div class="eyebrow">ELLIPTIC CURVE CRYPTOGRAPHY</div>', unsafe_allow_html=True)
st.title(page)


def key_page():
    st.write("Tạo cặp khóa để ký. Chia sẻ khóa công khai để người khác xác minh.")
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.subheader("Tạo cặp khóa")
        algorithm = st.selectbox("Thuật toán", c.ALGORITHMS)
        st.caption("P-256" if algorithm == "ECDSA" else "RSA-3072 · e = 65537")
        if st.button("Tạo khóa mới", type="primary"):
            with st.spinner("Đang tạo khóa…"):
                set_key(c.generate_key(algorithm))
            st.rerun()
    with right, st.container(border=True):
        st.subheader("Nhập khóa đã lưu")
        uploaded = st.file_uploader("Khóa bí mật PEM đã mã hóa", type=["pem"], key="private_upload")
        password = st.text_input("Mật khẩu nhập khóa", type="password")
        if st.button("Nhập khóa", disabled=uploaded is None):
            set_key(c.load_private(uploaded.getvalue(), password))
            st.rerun()
    key = st.session_state.get("private_key")
    if key:
        public = key.public_key()
        st.subheader("Khóa đang dùng")
        a, b, d = st.columns(3)
        a.metric("Thuật toán", c.key_algorithm(key))
        b.metric("Kích thước khóa", f"{key.key_size} bit")
        d.metric("Khóa công khai DER", f"{len(c.public_der(public))} byte")
        st.code(c.export_public(public).decode(), language=None)
        st.caption("Fingerprint SHA-256: " + c.fingerprint(public))
        st.download_button("Tải khóa công khai", c.export_public(public), "public_key.pem")
        with st.expander("Lưu khóa bí mật có mật khẩu"):
            st.write("Mật khẩu dùng để mã hóa tệp PKCS8. Cần cả tệp và mật khẩu để nhập lại khóa.")
            password = st.text_input("Mật khẩu xuất khóa", type="password", key="export_password")
            if password:
                st.download_button("Tải khóa bí mật đã mã hóa", c.export_private(key, password), "private_key.pem")


def hash_page():
    st.write("Quan sát dấu vân tay của dữ liệu và sự thay đổi khi sửa nội dung.")
    data = input_bytes("hash")
    if data is None:
        return
    a, b = st.columns(2)
    for column, name in zip((a, b), c.HASHES):
        with column, st.container(border=True):
            st.subheader(name)
            hashed = c.digest(data, name)
            st.caption(f"{len(hashed)} byte · {len(hashed) * 8} bit · {len(hashed) * 2} ký tự hex")
            st.code(hashed.hex(), language=None, wrap_lines=True)
    with st.expander("So sánh khi thay đổi dữ liệu", expanded=True):
        changed = st.text_area("Nội dung mới để so sánh (UTF-8)", "Tôi xác nhận nội dung bài tập lớn An ninh mạng!", key="hash_changed")
        changed_bytes = changed.encode("utf-8")
        for name in c.HASHES:
            first, second = c.digest(data, name), c.digest(changed_bytes, name)
            bits = sum((x ^ y).bit_count() for x, y in zip(first, second))
            st.write(f"**{name}:** {bits}/{len(first) * 8} bit khác nhau ({bits / (len(first) * 8):.1%}).")
            st.code(second.hex(), language=None, wrap_lines=True)
        st.caption("Một phép thử minh họa hiệu ứng khuếch tán; không phải bằng chứng toán học về chống va chạm.")


def signature_page():
    st.write("Ký bằng khóa bí mật. Xác minh bằng dữ liệu gốc, chữ ký và khóa công khai.")
    st.markdown('<div class="flow">01 · Dữ liệu gốc &nbsp; → &nbsp; 02 · SHA-256 / SHA-512 &nbsp; → &nbsp; 03 · Chữ ký số &nbsp; → &nbsp; 04 · Xác minh</div>', unsafe_allow_html=True)
    sign_tab, verify_tab = st.tabs(["Tạo chữ ký", "Xác minh chữ ký"])
    with sign_tab:
        key = st.session_state.get("private_key")
        if not key:
            st.info("Chưa có khóa. Có thể tạo nhanh ECDSA P-256 hoặc vào Quản lý khóa để chọn RSA.")
            if st.button("Tạo nhanh khóa ECDSA", type="primary"):
                set_key(c.generate_key("ECDSA"))
                st.rerun()
        else:
            st.caption(f"Khóa đang dùng: {c.key_algorithm(key)} · {key.key_size} bit")
        data = input_bytes("sign")
        hash_name = st.selectbox("Hàm băm khi ký", c.HASHES, on_change=invalidate)
        context = (c.digest(data, "SHA-256"), hash_name, c.fingerprint(key.public_key())) if data is not None and key else None
        if st.session_state.get("signed_context") != context:
            invalidate()
        if st.button("Ký dữ liệu", type="primary", disabled=key is None or data is None):
            st.session_state.signed = c.sign(data, key, hash_name)
            st.session_state.signed_context = context
        envelope = st.session_state.get("signed")
        if envelope is not None:
            st.success("Đã tạo chữ ký")
            a, b = st.columns(2)
            a.metric("Chữ ký trước Base64", f"{len(envelope.signature)} byte")
            b.metric("Hàm băm", envelope.hash_name)
            st.code(c.digest(data, envelope.hash_name).hex(), language=None, wrap_lines=True)
            st.download_button("Tải chữ ký JSON", envelope.to_bytes(), "signature.json", "application/json")
            st.download_button("Tải dữ liệu đã ký", data, "signed_data.bin", "application/octet-stream")
            st.download_button("Tải khóa công khai xác minh", c.export_public(key.public_key()), "public_key.pem")
            if st.button("Kiểm tra chữ ký vừa tạo"):
                st.session_state.verified = c.verify(data, key.public_key(), envelope)
            if st.session_state.get("verified") is True:
                st.success("Hợp lệ: chữ ký khớp dữ liệu và khóa công khai.")
            st.markdown("**Thử thay đổi dữ liệu**")
            st.caption("Đảo một bit đầu tiên; nếu dữ liệu rỗng thì thêm một byte. Chữ ký gốc được giữ nguyên.")
            if st.button("Sửa một byte và xác minh lại"):
                changed = bytes([data[0] ^ 1]) + data[1:] if data else b"\x01"
                st.session_state.changed_verification = c.verify(changed, key.public_key(), envelope)
            if st.session_state.get("changed_verification") is False:
                st.error("Không hợp lệ: dữ liệu đã bị thay đổi.")
    with verify_tab:
        st.caption("Có thể xác minh trong phiên mới; không cần khóa bí mật.")
        data = input_bytes("verify")
        public_file = st.file_uploader("Khóa công khai PEM", type=["pem"], key="verify_public", on_change=invalidate)
        sig_file = st.file_uploader("Chữ ký JSON", type=["json"], key="verify_signature", on_change=invalidate)
        if st.button("Xác minh tệp chữ ký", type="primary", disabled=data is None or public_file is None or sig_file is None):
            public = c.load_public(public_file.getvalue())
            envelope = c.parse_envelope(sig_file.getvalue())
            valid = c.verify(data, public, envelope)
            if valid:
                st.success("Chữ ký hợp lệ với dữ liệu và khóa công khai đã cung cấp.")
            else:
                st.error("Chữ ký không hợp lệ: dữ liệu, khóa hoặc chữ ký không khớp.")
            st.caption(f"{envelope.algorithm} / {envelope.hash_name} · fingerprint {c.fingerprint(public)}")
    with st.expander("Cách diễn giải kết quả"):
        st.write("Chữ ký hợp lệ chứng minh dữ liệu khớp với chữ ký tạo bằng khóa bí mật tương ứng. Danh tính chủ khóa cần được xác nhận qua một kênh tin cậy hoặc chứng thư số. Chữ ký không che giấu nội dung dữ liệu.")


def benchmark_page():
    st.write("So sánh P-256 và RSA-3072 ở mức an toàn cổ điển xấp xỉ 128 bit.")
    st.caption("Cùng dữ liệu 1 KiB, 100 KiB, 1 MiB và 10 MiB · thời gian đọc tệp và vẽ biểu đồ nằm ngoài phép đo.")
    mode = st.radio("Chế độ đo", ["Đầy đủ · dùng cho báo cáo", "Nhanh · kiểm tra chương trình"], horizontal=True)
    st.write("**Đầy đủ:** 100 lần đo, 10 lần khởi động; tạo khóa 20 lần. **Nhanh:** 10 lần đo, 2 lần khởi động; tạo khóa 3 lần.")
    if st.button("Chạy thực nghiệm", type="primary"):
        progress = st.progress(0., text="Chuẩn bị dữ liệu…")
        config = BenchmarkConfig() if mode.startswith("Đầy đủ") else BenchmarkConfig(10, 2, 3)
        st.session_state.benchmark = run_benchmark(config, lambda pct, label: progress.progress(pct, text=label))
        progress.empty()
    saved = Path(__file__).parent / "output" / "reference_run"
    if saved.exists() and st.button("Mở kết quả thực nghiệm đi kèm"):
        st.session_state.benchmark = {name: pd.read_csv(saved / f"{name}.csv") for name in ("raw", "summary", "sizes")}
        st.session_state.benchmark["metadata"] = json.loads((saved / "metadata.json").read_text(encoding="utf-8"))
    result = st.session_state.get("benchmark")
    if result:
        meta = result["metadata"]
        st.info(f"Kết quả {meta['recorded_at_utc']} · {meta['config']['iterations']} lần đo · Python {meta['python']}")
        operation = st.selectbox("Phép đo hiển thị", list(OPERATIONS), format_func=OPERATIONS.get)
        png = chart_png(result["summary"], operation)
        st.image(png)
        st.dataframe(result["summary"][result["summary"].operation == operation], hide_index=True, use_container_width=True)
        st.subheader("Kích thước khóa và chữ ký")
        st.dataframe(result["sizes"], hide_index=True, use_container_width=True)
        for name, label in (("raw", "Dữ liệu từng lần đo"), ("summary", "Bảng tổng hợp"), ("sizes", "Kích thước")):
            st.download_button(f"Tải CSV · {label}", result[name].to_csv(index=False).encode("utf-8-sig"), f"{name}.csv", "text/csv")
        st.download_button("Tải biểu đồ PNG", png, f"{operation}.png", "image/png")
        st.download_button("Tải thông tin môi trường", json.dumps(meta, ensure_ascii=False, indent=2), "metadata.json")
        with st.expander("Môi trường và phương pháp đo"):
            st.json(meta)
            st.write("Các phép đo chạy tuần tự. Tiến trình nền và chế độ nguồn có thể ảnh hưởng kết quả. Hãy so sánh trên cùng máy và dùng nhiều lần chạy trước khi khái quát hóa.")


try:
    {"Quản lý khóa": key_page, "Khám phá SHA": hash_page,
     "Ký và xác minh": signature_page, "Thực nghiệm": benchmark_page}[page]()
except c.InputError as exc:
    st.error(str(exc))

st.divider()
st.caption("ECC SIGNATURE LAB · Bài tập lớn An ninh mạng · ECDSA / RSA-PSS / SHA-2")
