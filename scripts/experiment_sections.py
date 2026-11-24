"""Build report sections from the actual benchmark and JUnit output."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd


def measured_sections(root: Path):
    directory = root / "output/reference_run"
    summary = pd.read_csv(directory / "summary.csv", keep_default_na=False)
    sizes = pd.read_csv(directory / "sizes.csv")
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    suite = ET.parse(root / "output/test-results.xml").getroot().find("testsuite")
    tests, failures = int(suite.get("tests")), int(suite.get("failures")) + int(suite.get("errors"))
    sections = []

    def add(title, paragraphs, table=None, figure=None, chapter="5 Thực nghiệm và đánh giá"):
        sections.append(dict(chapter=chapter, title=title, paragraphs=paragraphs, table=table,
                             figure=figure, equations=None, code=None))

    def value(algorithm, hash_name, operation, size=1024):
        return float(summary[(summary.algorithm == algorithm) & (summary.hash == hash_name) &
            (summary.operation == operation) & (summary.size_bytes == size)].iloc[0].median_ms)

    def rows_for(operation, size=1024):
        rows = summary[(summary.operation == operation) & (summary.size_bytes == size)]
        return [[r.algorithm, r.hash, f"{r.median_ms:.5f}", f"{r.mean_ms:.5f}", f"{r.std_ms:.5f}"] for r in rows.itertuples()]

    add("5.1 Môi trường và dữ liệu thực nghiệm", [
        "Thực nghiệm được thực hiện bằng chính mô-đun dùng trong giao diện. Thời điểm dưới đây được ghi theo UTC để tránh nhầm múi giờ; thời gian Việt Nam bằng UTC cộng 7 giờ. Các phiên bản được lấy từ môi trường đang chạy, không điền theo phiên bản dự kiến của kế hoạch. Dữ liệu gốc và thông tin môi trường được lưu trong output/reference_run.",
        "Bốn tệp byte có kích thước 1 KiB, 100 KiB, 1 MiB và 10 MiB. Mỗi tệp được tạo bằng cách lặp dãy byte 0 đến 255 rồi cắt đúng độ dài. Cách sinh cố định giúp các thuật toán nhận cùng đầu vào và tái lập được dữ liệu. Đây không phải nguồn ngẫu nhiên để tạo khóa hoặc nonce; mọi giá trị bí mật vẫn do thư viện sinh.",
        "Giới hạn 10 MiB cũng là giới hạn của giao diện. Bộ đo tạo toàn bộ dữ liệu trước khi bắt đầu đồng hồ. Do đó kết quả không bao gồm thời gian tải tệp qua trình duyệt, truy cập ổ đĩa hay sao chép nội dung từ widget. Phép đo thể hiện chi phí xử lý byte đã ở trong bộ nhớ.",
        "Máy đồng thời chạy hệ điều hành và các tiến trình người dùng. Thực nghiệm không khóa tần số CPU hoặc cô lập lõi xử lý. Bảng môi trường giúp người đọc đánh giá phạm vi kết quả, nhưng không loại bỏ được tất cả nguyên nhân nhiễu. Các số liệu sau đây nên được xem là một lần chạy tham chiếu có thể tái lập quy trình, không phải chuẩn tốc độ phổ quát."
    ], (["Thông số", "Giá trị thực đo"], [["Thời điểm UTC", metadata["recorded_at_utc"]],
        ["Hệ điều hành", metadata["os"]], ["CPU", metadata["cpu"]], ["CPU logic / RAM", f"{metadata['logical_cpus']} / {metadata['ram_gib']} GiB"],
        ["Python / cryptography", f"{metadata['python']} / {metadata['cryptography']}"], ["OpenSSL", metadata["openssl"]]]))

    add("5.2 Phương pháp đo và thống kê", [
        "Mỗi nhóm băm, ký hoặc xác minh có 10 vòng khởi động và 100 mẫu được ghi nhận. Nhóm tạo khóa có 10 vòng khởi động và 20 khóa mới được đo cho mỗi thuật toán. Các mẫu khởi động bị loại bỏ khỏi CSV. Đồng hồ time.perf_counter_ns đo chênh lệch theo nano giây; chương trình chuyển kết quả sang mili giây trước khi lưu. [9]",
        "Các nhóm gồm băm, ký digest, xác minh digest, băm cộng ký và băm cộng xác minh. Tạo khóa được đo riêng và không lặp lại theo hàm băm vì sinh khóa không phụ thuộc SHA-256 hay SHA-512 trong giao diện cấu hình này. Tổng số mẫu là 2×4×100 cho băm, 2×2×4×4×100 cho ký/xác minh và 2×20 cho tạo khóa, bằng 7.240 mẫu.",
        "Bảng tổng hợp ghi trung vị, trung bình và độ lệch chuẩn mẫu. Trung vị giảm độ nhạy với một số lượt bị gián đoạn lâu; trung bình phản ánh tổng chi phí chia số lượt; độ lệch chuẩn cho biết mức phân tán trong nhóm. Chúng bổ sung cho nhau, không thay thế dữ liệu gốc. Chương trình giữ từng thời gian trong raw.csv để có thể kiểm tra lại.",
        "Phép ký digest dùng digest đã tính trước. Phép xác minh digest dùng một chữ ký hợp lệ đã chuẩn bị trước và kiểm tra kết quả đúng sau mỗi lượt. Phép băm cộng xác minh băm lại thông điệp trong khoảng đồng hồ. Các chi phí kiểm tra kiểu khóa và lời gọi Python thuộc hàm ứng dụng nên vẫn nằm trong phép đo; đây không phải đo riêng lõi OpenSSL.",
        "Thứ tự chạy là cố định, SHA trước rồi ECDSA và RSA. Thiết kế này dễ tái lập nhưng có nguy cơ bị ảnh hưởng bởi thay đổi tải hoặc tần số giữa các nhóm. Một nghiên cứu rộng hơn nên lặp cả bộ nhiều lần và đảo thứ tự cấu hình; báo cáo hiện tại không tính khoảng tin cậy giữa các phiên độc lập."
    ], (["Nhóm", "Số cấu hình", "Lần đo", "Số mẫu"], [["Băm", "2 SHA × 4 cỡ", "100", "800"], ["Ký/xác minh", "2 × 2 × 4 × 4", "100", "6.400"], ["Tạo khóa", "2 thuật toán", "20", "40"], ["Tổng", "", "", "7.240"]]))

    key_rows = rows_for("keygen", 0)
    size_rows = [[r.algorithm, r.hash, str(r.public_spki_der_bytes), f"{r.signature_min_bytes}–{r.signature_max_bytes}"] for r in sizes.itertuples()]
    add("5.3 Tạo khóa và kích thước biểu diễn", [
        f"Trung vị tạo khóa trong lần chạy này là {value('ECDSA','N/A','keygen',0):.5f} ms cho ECDSA và {value('RSA-PSS','N/A','keygen',0):.5f} ms cho RSA. Phép đo sinh khóa mới ở mỗi lần, không lấy lại khóa đã cache. Chi phí RSA chịu ảnh hưởng quá trình sinh và kiểm tra số nguyên tố, nên các lần sinh có thể phân tán đáng kể.",
        "Kích thước khóa công khai được đo sau khi tuần tự hóa theo cùng định dạng SPKI DER. Khóa P-256 có 91 byte, RSA-3072 có 422 byte trong môi trường này. Đây là kích thước biểu diễn, không phải tuyên bố số bit an toàn hay độ dài khóa bí mật. Bảng tách thuật toán băm để thể hiện rằng cùng loại khóa không thay đổi kích thước chỉ vì chọn SHA khác.",
        "Độ dài chữ ký được khảo sát qua 100 chữ ký mới cho mỗi cấu hình, ở ngoài phép đo thời gian. ECDSA DER có độ dài biến thiên do cách mã hóa số nguyên: đôi khi cần byte 0 ở đầu để giữ số dương, đôi khi một số có ít byte hơn. RSA luôn có 384 byte với modulus 3072 bit. Không cộng phần Base64 hoặc JSON vào cột này.",
        "Kết quả dung lượng có ý nghĩa khi truyền và lưu nhiều chữ ký. Tuy nhiên tổng chi phí một giao thức còn có thể chứa chứng thư, metadata và thông điệp. Lợi ích quan sát trên một chữ ký không tự chuyển thành cùng tỷ lệ tiết kiệm ở mọi hệ thống."
    ], (["Thuật toán", "SHA", "SPKI DER byte", "Chữ ký byte"], size_rows), "keygen.png")

    hash_rows = [[f"{int(r.size_bytes/1024)} KiB", r.hash, f"{r.median_ms:.5f}", f"{r.std_ms:.5f}"]
                 for r in summary[summary.operation == "hash"].itertuples()]
    add("5.4 Kết quả băm SHA256 và SHA512", [
        f"Với dữ liệu 1 KiB, trung vị SHA-256 là {value('SHA-2','SHA-256','hash'):.5f} ms, SHA-512 là {value('SHA-2','SHA-512','hash'):.5f} ms. Bảng bao gồm bốn kích thước để phân biệt chi phí cố định của lời gọi với chi phí xử lý thông điệp dài.",
        "Khi số byte tăng, toàn bộ nội dung phải đi qua hàm băm. Biểu đồ dùng trục kích thước log để hiển thị từ 1 KiB đến 10 MiB trong cùng một hình, và trục thời gian log để tránh nhóm nhỏ bị ép sát đáy. Người đọc cần xem đơn vị và thang đo trước khi so sánh độ dốc.",
        "Sự khác nhau giữa hai hàm trong môi trường này chịu ảnh hưởng cả cấu trúc thuật toán và đường tối ưu của OpenSSL trên CPU. Một số CPU có tập lệnh chuyên dụng cho một số hàm băm. Dữ liệu hiện có chưa cô lập những yếu tố này, nên không quy mọi chênh lệch cho độ dài đầu ra 256 hay 512 bit.",
        "Kết quả băm là thành phần quan trọng khi giải thích thời gian xử lý tệp lớn. Dù ký digest tương đối nhanh, băm tệp nhiều MiB vẫn có thể chiếm phần lớn thời gian đầu cuối. Vì vậy một ứng dụng không nên ước lượng thời gian ký tệp chỉ bằng phép đo sign_digest."
    ], (["Dữ liệu", "Hàm băm", "Trung vị ms", "Độ lệch chuẩn ms"], hash_rows), "hash.png")

    add("5.5 Ký và xác minh trên digest", [
        "Bảng dưới so sánh digest của thông điệp 1 KiB, nhưng bản thân phép ký chỉ nhận digest đã chuẩn bị. Theo nguyên lý, tăng tệp gốc không làm tăng độ dài digest của cùng hàm SHA. Nếu biểu đồ ký digest vẫn dao động giữa các kích thước, cần xem đó là biến thiên khi đo hoặc đặc tính chạy, không mặc định thuật toán ký đang xử lý toàn bộ tệp.",
        f"Với SHA-256 và thông điệp 1 KiB, trung vị ký ECDSA là {value('ECDSA','SHA-256','sign_digest'):.5f} ms, RSA-PSS là {value('RSA-PSS','SHA-256','sign_digest'):.5f} ms. Tương ứng, xác minh ECDSA là {value('ECDSA','SHA-256','verify_digest'):.5f} ms và RSA-PSS là {value('RSA-PSS','SHA-256','verify_digest'):.5f} ms. Các con số này là kết quả một nhóm cụ thể, không được áp dụng thay cho tất cả nhóm khác.",
        f"Ở nhóm SHA-512, xác minh ECDSA có trung vị {value('ECDSA','SHA-512','verify_digest'):.5f} ms trong khi RSA-PSS có {value('RSA-PSS','SHA-512','verify_digest'):.5f} ms. Sự thay đổi quan hệ giữa các nhóm nhắc rằng thứ tự cố định và môi trường không cô lập có thể tạo nhiễu. Cần chạy nhiều phiên độc lập trước khi quy chênh lệch nhỏ cho bản thân hàm băm.",
        "Độ lệch chuẩn và trung bình được lưu cùng trung vị trong CSV. Khi phát biểu kết luận, ưu tiên nhận xét có phạm vi rõ: ECDSA ký nhanh hơn RSA-PSS trong các nhóm đã đo, còn xác minh cần đọc từng cấu hình và quan sát độ ổn định. Không ghép thời gian ký và xác minh thành một con số duy nhất nếu chưa xác định tỷ lệ thao tác của ứng dụng."
    ], (["Thuật toán", "SHA", "Ký ms", "Xác minh ms"], [[a,h,f"{value(a,h,'sign_digest'):.5f}",f"{value(a,h,'verify_digest'):.5f}"] for a in ("ECDSA","RSA-PSS") for h in ("SHA-256","SHA-512")]), "sign_digest.png")

    combined = []
    for size in (1024, 10485760):
        for a in ("ECDSA", "RSA-PSS"):
            for h in ("SHA-256", "SHA-512"):
                combined.append([f"{size//1024} KiB", a, h, f"{value(a,h,'hash_sign',size):.5f}", f"{value(a,h,'hash_verify',size):.5f}"])
    add("5.6 Thời gian băm cộng ký và xác minh", [
        "Phép đo đầu cuối trong chương trình bắt đầu khi byte đã sẵn trong RAM và kết thúc sau thao tác ký hoặc xác minh. Nó chưa bao gồm tải tệp, lưu chữ ký, mạng hoặc tương tác người dùng. Bảng chọn hai đầu mút 1 KiB và 10 MiB; CSV giữ đầy đủ cả bốn kích thước.",
        "Thời gian băm cộng ký được đo trực tiếp, không lấy trung vị băm cộng trung vị ký của các nhóm chạy khác thời điểm. Tổng hai trung vị nói chung không bằng trung vị của tổng, và tải máy có thể khác giữa các nhóm. Nếu một số liệu tổng trông không khớp phép cộng từ hai bảng riêng, cần kiểm tra dữ liệu gốc trước khi kết luận công thức bị sai.",
        "Với tệp lớn, mức tăng chi phí băm có thể thu hẹp tỷ lệ chênh lệch tổng thời gian giữa ECDSA và RSA. Kết quả này cho thấy lựa chọn thuật toán chữ ký chỉ là một phần của hiệu năng xử lý tài liệu. Nếu mục tiêu là giảm độ trễ tải tệp, tối ưu IO hoặc xử lý theo luồng có thể cần thiết dù phép ký digest đã rất nhanh.",
        "Demo giữ tệp tối đa 10 MiB trong bộ nhớ để đơn giản hóa giao diện. Phiên bản xử lý tệp lớn hơn có thể băm theo khối rồi ký digest, nhưng cần thiết kế lại giới hạn tài nguyên và hiển thị tiến độ. Cách thay đổi đó không làm đổi byte thông điệp hay quy tắc ECDSA/PSS; nó thay đổi cách đưa dữ liệu tới hàm băm."
    ], (["Dữ liệu", "Thuật toán", "SHA", "Băm + ký ms", "Băm + XM ms"], combined), "hash_sign.png")

    add("5.7 Kiểm thử chức năng và giới hạn", [
        f"Kết quả JUnit ghi nhận {tests} trường hợp kiểm thử, {failures} trường hợp lỗi hoặc thất bại. Bộ kiểm thử bao gồm các cấu hình ECDSA/RSA-PSS kết hợp SHA-256/SHA-512; thông điệp rỗng, tiếng Việt, byte nhị phân và dữ liệu đúng giới hạn 10 MiB. Thông điệp vượt giới hạn bị từ chối.",
        "Vector SHA cho chuỗi abc được đối chiếu với giá trị kỳ vọng. Chữ ký tạo từ digest được xác minh bằng lời gọi thư viện trên thông điệp gốc; chiều ngược lại cũng được kiểm tra. Các trường hợp đổi byte, sửa chữ ký, sai khóa và sai hàm băm phải thất bại. JSON lỗi, Base64 lỗi, trường trùng và khóa ngoài cấu hình phải trả lỗi đầu vào.",
        "Kiểm thử Streamlit AppTest đi qua tạo khóa, ký, xác minh, thử sửa byte, thay đầu vào, chuyển khu vực và xóa phiên. Kiểm thử RSA dùng SHA-512 để kiểm tra đường cấu hình khác mặc định. AppTest xác nhận logic widget và thông báo; nó không thay cho việc xem bố cục trên mọi kích thước trình duyệt. Các hình giao diện trong báo cáo là sơ đồ chức năng, không phải ảnh chụp một phiên đã kiểm tra bằng mắt.",
        "Kết quả chức năng và hiệu năng trả lời hai câu hỏi khác nhau. Kiểm thử đạt không chứng minh chương trình không có mọi lỗi bảo mật. Thực nghiệm trên một máy không chứng minh một thuật toán nhanh hơn trong mọi môi trường. Báo cáo cũng chưa kiểm thử liên vận với một ứng dụng bên ngoài dùng định dạng riêng; đường kiểm tra chéo hiện vẫn dùng cùng thư viện mật mã.",
        "Các hạn chế cần khắc phục khi mở rộng gồm chạy lại trên nhiều máy, đảo thứ tự cấu hình, kiểm tra giao diện trên trình duyệt thực và bổ sung phân phối khóa tin cậy. Không sử dụng demo như dịch vụ ký công khai khi chưa thiết kế lại bảo vệ khóa, xác thực và giới hạn tài nguyên."
    ], (["Nhóm kiểm tra", "Kết quả yêu cầu"], [["Dữ liệu gốc + khóa đúng", "Hợp lệ"], ["Đổi byte / khóa / hash", "Không hợp lệ"], ["Khóa / JSON hỏng", "Lỗi rõ ràng"], ["Xuất rồi nhập lại", "Giữ khả năng ký/xác minh"], ["Thay đầu vào UI", "Bỏ kết quả cũ"]]))

    add("6.1 Kết quả đạt được", [
        "Đề tài đã kết nối được cơ sở toán học của ECC với một ứng dụng ký và xác minh dữ liệu. Các công thức cộng điểm, nhân đôi và nhân vô hướng được minh họa trên trường nhỏ; ví dụ ECDSA tính được chữ ký và khôi phục điều kiện kiểm tra bằng số cụ thể. Trong ứng dụng, toàn bộ mật mã thực tế sử dụng thư viện cryptography thay vì số học minh họa.",
        "Demo cung cấp bốn khu vực: quản lý khóa, khám phá SHA, ký/xác minh và thực nghiệm. Người dùng có thể tạo hoặc nhập khóa, ký byte văn bản/tệp, tải chữ ký tách rời và xác minh trong phiên không có khóa bí mật. Thử nghiệm đổi byte cho thấy kết quả xác minh thay đổi khi thông điệp không còn đúng với chữ ký ban đầu.",
        "Việc triển khai cả SHA-256 và SHA-512 làm rõ sự khác nhau giữa digest, lược đồ chữ ký và mức an toàn của đường cong. Cấu hình so sánh P-256 với RSA-3072 tránh nhầm lẫn so sánh bằng số bit khóa. Các phép đo tách thời gian băm khỏi ký/xác minh giúp giải thích ảnh hưởng của kích thước tệp.",
        "Trong lần đo tham chiếu, ECDSA có khóa công khai và chữ ký nhỏ hơn RSA-PSS. Chi phí ký cũng thấp hơn trong các nhóm khảo sát. Kết quả xác minh biến động theo cấu hình, nên không đưa ra kết luận ECC luôn nhanh hơn RSA. Số liệu gốc, metadata và biểu đồ cho phép kiểm tra lại từng phát biểu thay vì chỉ dựa vào hình tổng hợp.",
        f"Bộ {tests} kiểm thử cùng các mẫu công khai là bằng chứng cho các yêu cầu chức năng đã đặt ra. Mã nguồn và nội dung báo cáo có thể chỉnh sửa, chạy lại và mở rộng. Thành quả chính của bài tập là một chuỗi lập luận từ toán học đến cách dùng API, từ hành vi ứng dụng đến dữ liệu đánh giá có nguồn gốc rõ ràng."
    ], chapter="6 Kết luận và hướng phát triển")

    add("6.2 Hướng phát triển", [
        "Hướng cải thiện đầu tiên là phương pháp thực nghiệm. Chạy toàn bộ thí nghiệm nhiều lần, đảo thứ tự cấu hình và ghi nhận chế độ nguồn sẽ giúp đánh giá độ ổn định. Có thể thêm máy có kiến trúc khác và báo cáo khoảng tin cậy giữa các phiên độc lập. Việc mở rộng cần giữ nguyên định nghĩa thao tác và đơn vị đo để các bảng có thể so sánh.",
        "Hướng thứ hai là liên vận. Hiện JSON là định dạng của demo; một bên thứ ba cần hiểu đúng version, DER, PSS, MGF1 và salt. Có thể bổ sung kiểm thử với OpenSSL CLI hoặc định dạng chữ ký chuẩn phù hợp một ứng dụng cụ thể. Khi muốn ký PDF nhúng, cần nghiên cứu cấu trúc PDF và các chuẩn liên quan thay vì chỉ chèn chuỗi Base64 vào tệp.",
        "Hướng thứ ba là quản lý danh tính và khóa. Một ứng dụng thật cần xác minh chủ khóa, cấp phát hoặc kiểm tra chứng thư, xử lý thu hồi và dấu thời gian nếu có yêu cầu. Khóa bí mật có thể chuyển sang thiết bị bảo vệ hoặc kho khóa hệ điều hành. Cần mô hình đe dọa và quy trình vận hành rõ trước khi biến demo cá nhân thành dịch vụ nhiều người dùng.",
        "Về học thuật, có thể thêm mô phỏng cộng điểm và nhân vô hướng trực quan trên trường nhỏ, hoặc khảo sát đường cong khác ở mức an toàn tương ứng. Các mô phỏng phải tách khỏi đường ký thật để tránh người dùng coi tham số nhỏ là một lựa chọn bảo mật. Chủ đề chữ ký hậu lượng tử cũng là một hướng nghiên cứu độc lập với phép so sánh cổ điển hiện tại.",
        "Khi tiếp tục phát triển, tiêu chí giữ lại là tính đúng, khả năng giải thích và khả năng tái lập. Mỗi chức năng thêm cần có đầu vào/đầu ra rõ ràng; mỗi kết luận hiệu năng cần dữ liệu gốc và điều kiện đo. Cách làm đó giúp sản phẩm phục vụ việc học và tránh các khẳng định vượt quá bằng chứng đã thu thập."
    ], chapter="6 Kết luận và hướng phát triển")
    return sections, metadata, tests
