"""Generate public fixtures. Private keys are deliberately not saved."""
from pathlib import Path
from ecc_lab.crypto import ALGORITHMS, HASHES, export_public, generate_key, sign

out = Path("samples")
out.mkdir(exist_ok=True)
data = "Tôi xác nhận nội dung bài tập lớn An ninh mạng.\nĐề tài: ECC và chữ ký số.\n".encode("utf-8")
(out / "message.txt").write_bytes(data)
(out / "message_tampered.txt").write_bytes(data.replace(b"ECC", b"RSA"))
for algorithm in ALGORITHMS:
    key = generate_key(algorithm)
    prefix = "ecdsa" if algorithm == "ECDSA" else "rsa"
    (out / f"{prefix}_public.pem").write_bytes(export_public(key.public_key()))
    for hash_name in HASHES:
        (out / f"{prefix}_{hash_name.lower()}.json").write_bytes(sign(data, key, hash_name).to_bytes())
print("Generated public fixtures in samples/")
