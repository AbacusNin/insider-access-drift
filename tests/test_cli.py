import pandas as pd

from insider_access_drift.cli import main


def test_generate_then_score(tmp_path, capsys):
    events = tmp_path / "events.csv"
    assert main(["generate", "--out", str(events)]) == 0
    assert events.exists()

    ranked = tmp_path / "ranked.csv"
    assert main(["score", "--in", str(events), "--out", str(ranked)]) == 0

    out = pd.read_csv(ranked)
    assert "risk_tier" in out.columns
    assert (out["risk_tier"] == "high_review").any()
    printed = capsys.readouterr().out
    assert "drift_score" in printed
