"""Reproducible experiment runner. File IO and plotting are outside timings."""
from __future__ import annotations

import argparse
import io
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import Callable

import cryptography
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import psutil
from cryptography.hazmat.backends.openssl.backend import backend

from ecc_lab.crypto import (ALGORITHMS, HASHES, MAX_BYTES, digest, generate_key,
                            public_der, sign_digest, verify_digest)

SIZES = (1024, 100 * 1024, 1024 * 1024, 10 * 1024 * 1024)
OPERATIONS = {"hash": "Băm", "sign_digest": "Ký digest", "verify_digest": "Xác minh digest",
              "hash_sign": "Băm + ký", "hash_verify": "Băm + xác minh", "keygen": "Tạo khóa"}


@dataclass(frozen=True)
class BenchmarkConfig:
    iterations: int = 100
    warmup: int = 10
    key_iterations: int = 20
    sizes: tuple[int, ...] = SIZES

    def validate(self):
        if not (2 <= self.iterations <= 1000 and 0 <= self.warmup <= 100 and 1 <= self.key_iterations <= 100):
            raise ValueError("Số vòng đo ngoài giới hạn.")
        if not self.sizes or any(not 1 <= size <= MAX_BYTES for size in self.sizes):
            raise ValueError("Kích thước dữ liệu ngoài giới hạn.")


def sample_data(size: int) -> bytes:
    """Fixed bytes for reproducibility; never used for cryptographic randomness."""
    block = bytes(range(256))
    return (block * ((size + 255) // 256))[:size]


def summarize(raw: pd.DataFrame) -> pd.DataFrame:
    return (raw.groupby(["algorithm", "hash", "size_bytes", "operation"], sort=False)["time_ms"]
            .agg(count="count", median_ms="median", mean_ms="mean", std_ms="std")
            .reset_index().fillna({"std_ms": 0.0}))


def run_benchmark(config: BenchmarkConfig = BenchmarkConfig(), progress: Callable | None = None):
    config.validate()
    records, lengths = [], []
    total = 2 + len(config.sizes) * 2 + 4 * len(config.sizes) * 4
    completed = 0

    def measure(fn, algorithm, hash_name, size, operation, iterations=None):
        nonlocal completed
        for _ in range(config.warmup):
            fn()
        for i in range(iterations or config.iterations):
            start = perf_counter_ns()
            result = fn()
            elapsed = perf_counter_ns() - start
            if operation in ("verify_digest", "hash_verify") and result is not True:
                raise RuntimeError("Phép xác minh trong benchmark thất bại.")
            records.append({"algorithm": algorithm, "hash": hash_name, "size_bytes": size,
                            "operation": operation, "iteration": i + 1, "time_ms": elapsed / 1e6})
        completed += 1
        if progress:
            progress(completed / total, f"{algorithm} / {hash_name} / {OPERATIONS[operation]}")

    # Payload generation and key serialization are intentionally not timed.
    data_by_size = {size: sample_data(size) for size in config.sizes}
    for hash_name in HASHES:
        for size, data in data_by_size.items():
            measure(lambda: digest(data, hash_name), "SHA-2", hash_name, size, "hash")
    for algorithm in ALGORITHMS:
        measure(lambda: generate_key(algorithm), algorithm, "N/A", 0, "keygen", config.key_iterations)
        key = generate_key(algorithm)
        public = key.public_key()
        for hash_name in HASHES:
            signature_sizes = []
            for size, data in data_by_size.items():
                hashed = digest(data, hash_name)
                signature = sign_digest(key, hashed, hash_name)
                assert verify_digest(public, signature, hashed, hash_name)
                measure(lambda: sign_digest(key, hashed, hash_name), algorithm, hash_name, size, "sign_digest")
                measure(lambda: verify_digest(public, signature, hashed, hash_name), algorithm, hash_name, size, "verify_digest")
                measure(lambda: sign_digest(key, digest(data, hash_name), hash_name), algorithm, hash_name, size, "hash_sign")
                measure(lambda: verify_digest(public, signature, digest(data, hash_name), hash_name), algorithm, hash_name, size, "hash_verify")
            for _ in range(config.iterations):
                signature_sizes.append(len(sign_digest(key, hashed, hash_name)))
            lengths.append({"algorithm": algorithm, "hash": hash_name,
                            "public_spki_der_bytes": len(public_der(public)),
                            "signature_min_bytes": min(signature_sizes),
                            "signature_max_bytes": max(signature_sizes),
                            "signature_mean_bytes": sum(signature_sizes) / len(signature_sizes)})
    raw = pd.DataFrame.from_records(records)
    metadata = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "os": platform.platform(), "cpu": platform.processor(), "logical_cpus": psutil.cpu_count(),
                "ram_gib": round(psutil.virtual_memory().total / 1024**3, 2),
                "python": platform.python_version(), "cryptography": cryptography.__version__,
                "openssl": backend.openssl_version_text(), "config": asdict(config),
                "dataset": "repeat bytes 0..255 then truncate; identical across algorithms",
                "clock": "time.perf_counter_ns", "units": "milliseconds",
                "notes": "Sequential execution; fixed algorithm order; warmup excluded; no disk/UI inside timing. Host background load is not controlled."}
    return {"raw": raw, "summary": summarize(raw), "sizes": pd.DataFrame(lengths), "metadata": metadata}


def chart_png(summary: pd.DataFrame, operation: str) -> bytes:
    data = summary[summary.operation == operation].copy()
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    colors = ["#087F8C", "#51B5A8", "#D87932", "#E8B35C"]
    if operation == "keygen":
        ax.bar(data.algorithm, data.median_ms, color=[colors[0], colors[2]])
    else:
        for i, ((algorithm, hash_name), rows) in enumerate(data.groupby(["algorithm", "hash"], sort=False)):
            rows = rows.sort_values("size_bytes")
            ax.plot(rows.size_bytes / 1024, rows.median_ms, "o-", color=colors[i % 4],
                    label=f"{algorithm} / {hash_name}", linewidth=2)
        ax.set_xscale("log")
        ax.set_xlabel("Kích thước dữ liệu (KiB, thang log)")
        ax.legend(fontsize=8)
    ax.set_ylabel("Trung vị (ms, thang log)")
    ax.set_yscale("log")
    ax.set_title(OPERATIONS[operation], loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=.2)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160)
    plt.close(fig)
    return buffer.getvalue()


def save_results(result: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("raw", "summary", "sizes"):
        result[name].to_csv(directory / f"{name}.csv", index=False, encoding="utf-8-sig")
    (directory / "metadata.json").write_text(json.dumps(result["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
    for operation in OPERATIONS:
        (directory / f"{operation}.png").write_bytes(chart_png(result["summary"], operation))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/experiments"))
    parser.add_argument("--quick", action="store_true", help="10 iterations, 2 warmups, 3 key generations; smoke test only")
    args = parser.parse_args()
    config = BenchmarkConfig(10, 2, 3) if args.quick else BenchmarkConfig()
    result = run_benchmark(config, lambda pct, label: print(f"{pct:.0%} {label}", flush=True))
    save_results(result, args.output)
    print(f"Saved {len(result['raw'])} measurements to {args.output}")


if __name__ == "__main__":
    main()

