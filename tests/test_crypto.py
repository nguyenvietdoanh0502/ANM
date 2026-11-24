import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from ecc_lab import crypto as c
from ecc_lab.toy_curve import G, N, add, multiply, worked_example


@pytest.fixture(scope="module", params=c.ALGORITHMS)
def key(request):
    return c.generate_key(request.param)


@pytest.mark.parametrize("hash_name", c.HASHES)
@pytest.mark.parametrize("data", [b"", "Nghiên cứu đường cong elliptic\r\n  ".encode(), bytes(range(256)), b"x" * c.MAX_BYTES], ids=["empty", "unicode", "binary", "10MiB"])
def test_round_trip_and_direct_verification(key, hash_name, data):
    envelope = c.sign(data, key, hash_name)
    assert c.verify(data, key.public_key(), c.parse_envelope(envelope.to_bytes()))
    # Different call path: OpenSSL hashes the raw message here, detecting double hashing.
    if envelope.algorithm == "ECDSA":
        key.public_key().verify(envelope.signature, data, ec.ECDSA(c.hash_algorithm(hash_name)))
        signature = key.sign(data, ec.ECDSA(c.hash_algorithm(hash_name)))
    else:
        key.public_key().verify(envelope.signature, data, c.pss(hash_name), c.hash_algorithm(hash_name))
        signature = key.sign(data, c.pss(hash_name), c.hash_algorithm(hash_name))
    assert c.verify_digest(key.public_key(), signature, c.digest(data, hash_name), hash_name)


@pytest.mark.parametrize("hash_name", c.HASHES)
def test_tamper_wrong_key_and_wrong_hash(key, hash_name):
    data = b"original message"
    envelope = c.sign(data, key, hash_name)
    assert not c.verify(b"Original message", key.public_key(), envelope)
    other = c.generate_key(c.key_algorithm(key))
    assert not c.verify(data, other.public_key(), envelope)
    corrupted = c.SignatureEnvelope(envelope.algorithm, hash_name, envelope.signature[:-1] + bytes([envelope.signature[-1] ^ 1]))
    assert not c.verify(data, key.public_key(), corrupted)
    wrong_hash = c.HASHES[1 - c.HASHES.index(hash_name)]
    assert not c.verify(data, key.public_key(), c.SignatureEnvelope(envelope.algorithm, wrong_hash, envelope.signature))


def test_export_import_and_password(key):
    password = "mật khẩu thử nghiệm"
    saved = c.export_private(key, password)
    assert b"ENCRYPTED PRIVATE KEY" in saved
    imported = c.load_private(saved, password)
    public = c.load_public(c.export_public(key.public_key()))
    assert c.fingerprint(public) == c.fingerprint(imported.public_key())
    assert c.verify(b"new session", public, c.sign(b"new session", imported, "SHA-256"))
    with pytest.raises(c.InputError):
        c.load_private(saved, "wrong")
    with pytest.raises(c.InputError):
        c.export_private(key, "")


@pytest.mark.parametrize("hash_name, expected", [
    ("SHA-256", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ("SHA-512", "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f")])
def test_sha_known_vector(hash_name, expected):
    assert c.digest(b"abc", hash_name).hex() == expected
    fn = hashlib.sha256 if hash_name == "SHA-256" else hashlib.sha512
    assert c.digest(b"", hash_name) == fn(b"").digest()


@pytest.mark.parametrize("payload", [b"", b"[]", b"null", b"{}", b"{", b"\xff", b"x" * (c.MAX_SIGNATURE_JSON + 1)], ids=["empty", "array", "null", "object", "truncated", "encoding", "oversize"])
def test_bad_json(payload):
    with pytest.raises(c.InputError):
        c.parse_envelope(payload)


@pytest.mark.parametrize("field,value", [("version", True), ("version", 2), ("algorithm", "DSA"),
    ("hash", "SHA-1"), ("key_profile", "P-384"), ("signature_base64", "@@"),
    ("signature_base64", ""), ("signature_base64", base64.b64encode(b"invalid DER").decode())])
def test_bad_envelope_fields(field, value):
    obj = json.loads(c.sign(b"abc", c.generate_key("ECDSA"), "SHA-256").to_bytes())
    obj[field] = value
    with pytest.raises(c.InputError):
        c.parse_envelope(json.dumps(obj).encode())


def test_duplicate_json_and_algorithm_mismatch():
    key = c.generate_key("ECDSA")
    env = c.sign(b"data", key, "SHA-256")
    payload = env.to_bytes().replace(b'"version": 1', b'"version": 1, "version": 1')
    with pytest.raises(c.InputError):
        c.parse_envelope(payload)
    wrong = c.SignatureEnvelope("RSA-PSS", env.hash_name, env.signature)
    with pytest.raises(c.InputError):
        c.verify(b"data", key.public_key(), wrong)


def test_unsupported_profiles_and_malformed_keys():
    for key in (ec.generate_private_key(ec.SECP384R1()), rsa.generate_private_key(public_exponent=65537, key_size=2048)):
        raw = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        with pytest.raises(c.InputError):
            c.load_public(raw)
    for raw in (b"", b"not a key", b"x" * (c.MAX_KEY_BYTES + 1)):
        with pytest.raises(c.InputError):
            c.load_public(raw)
        with pytest.raises(c.InputError):
            c.load_private(raw, "password")
    with pytest.raises(c.InputError):
        c.load_private(b"-----BEGIN PRIVATE KEY-----", "")


def test_size_and_digest_validation():
    with pytest.raises(c.InputError):
        c.digest(b"x" * (c.MAX_BYTES + 1), "SHA-256")
    with pytest.raises(c.InputError):
        c.digest(b"x", "MD5")
    key = c.generate_key("ECDSA")
    with pytest.raises(c.InputError):
        c.sign_digest(key, b"short", "SHA-256")


def test_small_curve_example():
    assert add(G, (5, 16)) is None
    assert multiply(2) == (6, 3)
    assert multiply(N) is None
    assert worked_example() == {"Q": (0, 6), "r": 10, "s": 15, "w": 14, "u1": 11, "u2": 7, "X": (10, 6)}
