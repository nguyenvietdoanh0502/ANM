"""Strict, small teaching profile: P-256 / RSA-3072 with SHA-2.

All real cryptographic arithmetic and randomness belong to cryptography/OpenSSL.
This module never writes private keys, passwords or document contents to disk.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, utils

MAX_BYTES = 10 * 1024 * 1024
MAX_KEY_BYTES = 64 * 1024
MAX_SIGNATURE_JSON = 16 * 1024
ALGORITHMS = ("ECDSA", "RSA-PSS")
HASHES = ("SHA-256", "SHA-512")
PrivateKey = ec.EllipticCurvePrivateKey | rsa.RSAPrivateKey
PublicKey = ec.EllipticCurvePublicKey | rsa.RSAPublicKey


class InputError(ValueError):
    """An expected input error safe to show in the UI."""


def hash_algorithm(name: str) -> hashes.HashAlgorithm:
    if name not in HASHES:
        raise InputError("Chỉ hỗ trợ SHA-256 và SHA-512.")
    return hashes.SHA256() if name == "SHA-256" else hashes.SHA512()


def validate_data(data: bytes) -> None:
    if not isinstance(data, bytes):
        raise InputError("Dữ liệu phải là chuỗi byte.")
    if len(data) > MAX_BYTES:
        raise InputError("Tệp vượt giới hạn 10 MiB.")


def digest(data: bytes, hash_name: str) -> bytes:
    validate_data(data)
    h = hashes.Hash(hash_algorithm(hash_name))
    h.update(data)
    return h.finalize()


def generate_key(algorithm: str) -> PrivateKey:
    if algorithm == "ECDSA":
        return ec.generate_private_key(ec.SECP256R1())
    if algorithm == "RSA-PSS":
        return rsa.generate_private_key(public_exponent=65537, key_size=3072)
    raise InputError("Thuật toán chữ ký không được hỗ trợ.")


def key_algorithm(key: PrivateKey | PublicKey) -> str:
    if isinstance(key, (ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey)):
        if not isinstance(key.curve, ec.SECP256R1):
            raise InputError("Demo chỉ nhận khóa EC trên đường cong P-256.")
        return "ECDSA"
    if isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
        public = key.public_key() if isinstance(key, rsa.RSAPrivateKey) else key
        if key.key_size != 3072 or public.public_numbers().e != 65537:
            raise InputError("Demo chỉ nhận RSA-3072 với số mũ công khai 65537.")
        return "RSA-PSS"
    raise InputError("Loại khóa không được hỗ trợ.")


def public_der(key: PublicKey) -> bytes:
    key_algorithm(key)
    return key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def fingerprint(key: PublicKey) -> str:
    return hashlib.sha256(public_der(key)).hexdigest()


def export_public(key: PublicKey) -> bytes:
    key_algorithm(key)
    return key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def export_private(key: PrivateKey, password: str) -> bytes:
    key_algorithm(key)
    if not isinstance(password, str) or not password:
        raise InputError("Cần mật khẩu để xuất khóa bí mật.")
    return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.BestAvailableEncryption(password.encode("utf-8")))


def _check_pem(pem: bytes) -> None:
    if not isinstance(pem, bytes) or not pem or len(pem) > MAX_KEY_BYTES:
        raise InputError("Tệp khóa rỗng hoặc vượt 64 KiB.")


def load_private(pem: bytes, password: str) -> PrivateKey:
    _check_pem(pem)
    if not pem.startswith(b"-----BEGIN ENCRYPTED PRIVATE KEY-----"):
        raise InputError("Cần khóa bí mật PKCS8 PEM đã mã hóa bằng mật khẩu.")
    try:
        key = serialization.load_pem_private_key(pem, password.encode("utf-8") or None)
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise InputError("Không đọc được khóa bí mật hoặc mật khẩu không đúng.") from exc
    key_algorithm(key)
    return key


def load_public(pem: bytes) -> PublicKey:
    _check_pem(pem)
    try:
        key = serialization.load_pem_public_key(pem)
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise InputError("Không đọc được khóa công khai PEM.") from exc
    key_algorithm(key)
    return key


def pss(hash_name: str) -> padding.PSS:
    h = hash_algorithm(hash_name)
    return padding.PSS(mgf=padding.MGF1(h), salt_length=h.digest_size)


def sign_digest(key: PrivateKey, hashed: bytes, hash_name: str) -> bytes:
    algorithm = key_algorithm(key)
    h = hash_algorithm(hash_name)
    if len(hashed) != h.digest_size:
        raise InputError("Độ dài digest không khớp hàm băm.")
    if algorithm == "ECDSA":
        return key.sign(hashed, ec.ECDSA(utils.Prehashed(h)))
    return key.sign(hashed, pss(hash_name), utils.Prehashed(h))


def verify_digest(key: PublicKey, signature: bytes, hashed: bytes, hash_name: str) -> bool:
    algorithm = key_algorithm(key)
    h = hash_algorithm(hash_name)
    if len(hashed) != h.digest_size:
        raise InputError("Độ dài digest không khớp hàm băm.")
    try:
        if algorithm == "ECDSA":
            key.verify(signature, hashed, ec.ECDSA(utils.Prehashed(h)))
        else:
            key.verify(signature, hashed, pss(hash_name), utils.Prehashed(h))
    except (InvalidSignature, ValueError):
        return False
    return True


@dataclass(frozen=True)
class SignatureEnvelope:
    algorithm: str
    hash_name: str
    signature: bytes

    def to_bytes(self) -> bytes:
        profile = "P-256" if self.algorithm == "ECDSA" else "RSA-3072-e65537"
        obj = {"version": 1, "algorithm": self.algorithm, "hash": self.hash_name,
               "key_profile": profile,
               "signature_base64": base64.b64encode(self.signature).decode("ascii")}
        return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InputError("JSON có trường trùng lặp.")
        obj[key] = value
    return obj


def parse_envelope(payload: bytes) -> SignatureEnvelope:
    if not isinstance(payload, bytes) or len(payload) > MAX_SIGNATURE_JSON:
        raise InputError("Tệp chữ ký phải nhỏ hơn hoặc bằng 16 KiB.")
    try:
        obj = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_pairs)
        fields = {"version", "algorithm", "hash", "key_profile", "signature_base64"}
        if not isinstance(obj, dict) or set(obj) != fields:
            raise ValueError()
        if type(obj["version"]) is not int or obj["version"] != 1:
            raise ValueError()
        if obj["algorithm"] not in ALGORITHMS or obj["hash"] not in HASHES:
            raise ValueError()
        expected = "P-256" if obj["algorithm"] == "ECDSA" else "RSA-3072-e65537"
        if obj["key_profile"] != expected or not isinstance(obj["signature_base64"], str):
            raise ValueError()
        signature = base64.b64decode(obj["signature_base64"], validate=True)
        if obj["algorithm"] == "ECDSA":
            # DER must represent a positive pair in the P-256 group range.
            r, s = utils.decode_dss_signature(signature)
            order = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
            if not (0 < r < order and 0 < s < order):
                raise ValueError()
        elif len(signature) != 384:
            raise ValueError()
        return SignatureEnvelope(obj["algorithm"], obj["hash"], signature)
    except (ValueError, TypeError, UnicodeError, binascii.Error, RecursionError) as exc:
        raise InputError("Tệp chữ ký JSON, tham số hoặc Base64 không hợp lệ.") from exc


def sign(data: bytes, key: PrivateKey, hash_name: str) -> SignatureEnvelope:
    return SignatureEnvelope(key_algorithm(key), hash_name, sign_digest(key, digest(data, hash_name), hash_name))


def verify(data: bytes, key: PublicKey, envelope: SignatureEnvelope) -> bool:
    if key_algorithm(key) != envelope.algorithm:
        raise InputError("Loại khóa công khai không khớp thuật toán trong chữ ký.")
    return verify_digest(key, envelope.signature, digest(data, envelope.hash_name), envelope.hash_name)

