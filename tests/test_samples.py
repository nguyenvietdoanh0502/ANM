from pathlib import Path
import pytest
from ecc_lab import crypto as c


@pytest.mark.parametrize("algorithm,prefix", [("ECDSA","ecdsa"),("RSA-PSS","rsa")])
@pytest.mark.parametrize("hash_name", c.HASHES)
def test_public_fixtures(algorithm, prefix, hash_name):
    samples = Path(__file__).resolve().parents[1] / "samples"
    public = c.load_public((samples / f"{prefix}_public.pem").read_bytes())
    envelope = c.parse_envelope((samples / f"{prefix}_{hash_name.lower()}.json").read_bytes())
    assert envelope.algorithm == algorithm
    assert envelope.hash_name == hash_name
    assert c.verify((samples / "message.txt").read_bytes(), public, envelope)
    assert not c.verify((samples / "message_tampered.txt").read_bytes(), public, envelope)
