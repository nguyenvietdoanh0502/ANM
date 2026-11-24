"""Package explicit project directories, excluding environments and caches."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/ECC_Signature_Lab.zip"
FILES = (
    ".gitignore", ".streamlit/config.toml", "README.md", "app.py", "pyproject.toml",
    "requirements.txt", "requirements-report.txt", "run.ps1", "output/test-results.xml",
)
DIRECTORIES = ("ecc_lab", "tests", "scripts", "docs", "samples", "output/reference_run", "output/report")


def main():
    paths = {ROOT / name for name in FILES}
    for directory in DIRECTORIES:
        paths.update(p for p in (ROOT / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for path in paths:
        if path.suffix == ".pem" and not path.name.endswith("_public.pem"):
            raise ValueError(f"Unexpected key file: {path.name}")
        if path.suffix == ".pem" and not path.read_bytes().startswith(b"-----BEGIN PUBLIC KEY-----"):
            raise ValueError(f"Not a public key: {path.name}")
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, Path("ECC_Signature_Lab") / path.relative_to(ROOT))
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Archive integrity check failed")
    checksum = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix(".sha256").write_text(f"{checksum}  {OUTPUT.name}\n", encoding="ascii")
    print(f"Packaged {len(paths)} files; {OUTPUT.stat().st_size:,} bytes; ZIP integrity OK")


if __name__ == "__main__":
    main()
