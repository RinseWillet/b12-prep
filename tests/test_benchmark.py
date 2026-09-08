from datetime import date

from my_package.reporting.benchmark import _classify, run_benchmark

REPO_ROOT_GOLD = "benchmark/gold.json"


def test_classify_match_missing_mismatch_and_spurious():
    assert _classify("XS0876756452", "XS0876756452") == "match"
    assert _classify(750000000, 750000000.0) == "match"
    assert _classify("2038-01-18", date(2038, 1, 18)) == "match"
    assert _classify(None, None) == "match"
    assert _classify("Senior", None) == "missing"
    assert _classify(None, "Senior") == "spurious"
    assert _classify("fixed", "floating") == "mismatch"


def test_classify_lenient_mode_ignores_case_and_punctuation():
    assert _classify("Final Terms", "FINAL TERMS", mode="lenient") == "match"
    assert _classify("English law", "English law.", mode="lenient") == "match"
    assert _classify("BNP Paribas", "BNP Paribas SA", mode="lenient") == "match"
    assert _classify("Final Terms", "FINAL TERMS", mode="exact") == "mismatch"


def test_run_benchmark_scores_stub_and_writes_csv(tmp_path):
    out = tmp_path / "benchmark.csv"
    detail, summary = run_benchmark(REPO_ROOT_GOLD, str(out))
    assert out.exists()
    assert (tmp_path / "benchmark_summary.csv").exists()
    stub_row = summary[summary.extractor == "stub"].iloc[0]
    assert stub_row.total > 0
    assert 0.0 <= stub_row.accuracy <= 1.0
    assert set(detail["outcome"]).issubset({"match", "missing", "mismatch", "spurious"})
