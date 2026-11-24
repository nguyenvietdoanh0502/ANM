from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_sign_tamper_and_clear_stale_results():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    button(app, "Tạo nhanh khóa ECDSA").click().run()
    button(app, "Ký dữ liệu").click().run()
    assert any(x.value == "Đã tạo chữ ký" for x in app.success)
    button(app, "Kiểm tra chữ ký vừa tạo").click().run()
    assert any("Hợp lệ" in x.value for x in app.success)
    button(app, "Sửa một byte và xác minh lại").click().run()
    assert any("dữ liệu đã bị thay đổi" in x.value for x in app.error)
    app.text_area(key="sign_text").set_value("Dữ liệu mới").run()
    assert "signed" not in app.session_state
    assert not app.exception


def test_navigation_and_hash_output():
    app = AppTest.from_file(APP, default_timeout=30).run()
    for page in ("Quản lý khóa", "Khám phá SHA", "Thực nghiệm", "Ký và xác minh"):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
    app.sidebar.radio[0].set_value("Khám phá SHA").run()
    app.text_area(key="hash_text").set_value("abc").run()
    assert any("ba7816bf" in x.value for x in app.code)


def test_rsa_sign_and_clear_session():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.sidebar.radio[0].set_value("Quản lý khóa").run()
    app.selectbox[0].set_value("RSA-PSS").run()
    button(app, "Tạo khóa mới").click().run()
    app.sidebar.radio[0].set_value("Ký và xác minh").run()
    app.selectbox[0].set_value("SHA-512").run()
    button(app, "Ký dữ liệu").click().run()
    button(app, "Kiểm tra chữ ký vừa tạo").click().run()
    assert any("Hợp lệ" in x.value for x in app.success)
    button(app, "Xóa phiên làm việc").click().run()
    assert "private_key" not in app.session_state
    assert "signed" not in app.session_state
    assert not app.exception
