"""Generate clearly labeled diagrams, not fabricated UI screenshots."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from ecc_lab.toy_curve import P, A, B

out = Path("output/report/figures")
out.mkdir(parents=True, exist_ok=True)
points = [(x,y) for x in range(P) for y in range(P) if (y*y-x*x*x-A*x-B) % P == 0]
fig, ax = plt.subplots(figsize=(7, 3.5), layout="constrained")
ax.scatter(*zip(*points), color="#087F8C", s=45)
for x,y,label in [(5,1,"G"),(6,3,"2G"),(10,6,"3G"),(0,6,"7G")]:
    ax.annotate(label, (x,y), xytext=(6,7), textcoords="offset points", fontsize=10)
ax.set(xlim=(-1,17), ylim=(-1,17), xlabel="x trong F17", ylabel="y trong F17", title="Các điểm của y² = x³ + 2x + 2 trên F17")
ax.set_xticks(range(0,17,2)); ax.set_yticks(range(0,17,2)); ax.grid(alpha=.2)
fig.savefig(out / "toy_curve.png", dpi=180); plt.close(fig)


def diagram(name, title, boxes, arrows, footer):
    fig, ax = plt.subplots(figsize=(9,4.2))
    ax.set(xlim=(0,10), ylim=(0,5)); ax.axis("off")
    ax.text(.2,4.7,title,fontsize=14,fontweight="bold",color="#172B4D")
    for x,y,w,h,text in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.08",facecolor="#EDF5F5",edgecolor="#087F8C"))
        ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=11,color="#172B4D",linespacing=1.6)
    for start,end in arrows:
        ax.annotate("",xy=end,xytext=start,arrowprops=dict(arrowstyle="->",color="#587080",lw=1.6))
    ax.text(.2,.1,footer,fontsize=9,color="#586779")
    fig.savefig(out/name,dpi=180,bbox_inches="tight"); plt.close(fig)


diagram("architecture.png","Kiến trúc ứng dụng",[(.3,2.5,2.6,1.3,"Giao diện Streamlit\nVăn bản · Tệp · Khóa"),(3.6,2.5,2.7,1.3,"Dịch vụ mật mã\ncryptography / OpenSSL"),(7,2.5,2.6,1.3,"Đầu ra\nChữ ký JSON · PEM"),(3.6,.7,2.7,1.1,"Benchmark + Tests\nCSV · PNG · JUnit")],[((3,3.1),(3.5,3.1)),((6.4,3.1),(6.9,3.1)),((4.9,1.9),(4.9,2.4))],"Nguồn: thiết kế của đề tài. Mọi xử lý ứng dụng diễn ra trên localhost.")
diagram("ui_hash.png","Sơ đồ chức năng màn hình Khám phá SHA",[(.3,2.8,2.6,1.2,"Văn bản UTF-8\nhoặc tệp byte"),(3.6,2.8,2.7,1.2,"SHA-256\n32 byte · 64 hex"),(7,2.8,2.6,1.2,"SHA-512\n64 byte · 128 hex"),(3.6,.8,6,1.1,"Nội dung đã sửa → digest mới\nĐếm số bit khác nhau")],[((3,3.4),(3.5,3.4)),((6.4,3.4),(6.9,3.4)),((4.9,2.7),(4.9,2))],"Sơ đồ mô tả giao diện; không phải ảnh chụp trình duyệt.")
diagram("ui_signature.png","Sơ đồ chức năng màn hình Ký và xác minh",[(.3,2.8,2.6,1.2,"Dữ liệu + khóa bí mật\nChọn SHA → Ký"),(3.6,2.8,2.7,1.2,"Tải chữ ký JSON\nDữ liệu + PEM công khai"),(7,2.8,2.6,1.2,"Phiên xác minh\nKhông cần khóa bí mật"),(.3,.8,4.2,1.1,"Dữ liệu gốc + khóa đúng\nKết quả hợp lệ"),(5.3,.8,4.3,1.1,"Đổi byte hoặc sai khóa\nKết quả không hợp lệ")],[((3,3.4),(3.5,3.4)),((6.4,3.4),(6.9,3.4)),((8.3,2.7),(7.5,2))],"Sơ đồ mô tả giao diện; các kết quả được kiểm tra bằng lời gọi mật mã thật.")
print("Generated four diagrams")
