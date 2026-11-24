import pandas as pd
import pytest
from ecc_lab.benchmark import BenchmarkConfig, OPERATIONS, run_benchmark, save_results


def test_benchmark_measurements_and_exports(tmp_path):
    progress = []
    result = run_benchmark(BenchmarkConfig(2, 0, 1, (1024,)), lambda pct, label: progress.append(pct))
    # 2 keygen + 2 hash groups * 2 + 4 profiles * 4 operations * 2.
    assert len(result["raw"]) == 38
    assert set(result["summary"].operation) == set(OPERATIONS)
    assert (result["raw"].time_ms > 0).all()
    assert progress[-1] == 1
    assert len(result["sizes"]) == 4
    save_results(result, tmp_path)
    assert len(pd.read_csv(tmp_path / "raw.csv")) == 38
    assert all((tmp_path / f"{name}.png").stat().st_size > 1000 for name in OPERATIONS)


@pytest.mark.parametrize("config", [BenchmarkConfig(0), BenchmarkConfig(sizes=(0,)), BenchmarkConfig(key_iterations=0)])
def test_invalid_benchmark(config):
    with pytest.raises(ValueError):
        config.validate()
