import json

import pandas as pd
import pytest
from reference import crownjewel_download_burst as cj

from insider_access_drift.cli import main
from insider_access_drift.config import Config, DetectionConfig, FeatureConfig
from insider_access_drift.features import add_trend_feature, user_features
from insider_access_drift.generate import generate_events
from insider_access_drift.score import score


def _feats():
    e = generate_events()
    return e, add_trend_feature(e, user_features(e))


def test_from_dict_rejects_unknown_key():
    with pytest.raises(ValueError):
        Config.from_dict({"drift": {"nope": 1}})


def test_weight_override_lowers_score():
    _, feats = _feats()
    base = score(feats).set_index("user_id").loc["u901", "drift_score"]
    cfg = Config.from_dict({"weights": {"crown_jewel_touches": 0.0}})
    lowered = score(feats, cfg.drift).set_index("user_id").loc["u901", "drift_score"]
    assert lowered < base


def test_high_threshold_override_removes_high_review():
    _, feats = _feats()
    cfg = Config.from_dict({"drift": {"high_threshold": 100000, "moderate_threshold": 100000}})
    assert "high_review" not in set(score(feats, cfg.drift)["risk_tier"])


def test_restricted_min_override_changes_touch_counts():
    e = generate_events()
    base = user_features(e).set_index("user_id").loc["u900", "restricted_touches"]
    strict = user_features(e, FeatureConfig(restricted_min=3)).set_index("user_id")
    assert strict.loc["u900", "restricted_touches"] < base


def test_detection_threshold_override_changes_flags():
    e = generate_events()
    assert set(cj.flag(e)["user_id"]) == {"u901"}
    assert cj.flag(e, DetectionConfig(crownjewel_min_mb=10000.0)).empty


def test_cli_config_applied(tmp_path):
    events = tmp_path / "e.csv"
    main(["generate", "--out", str(events)])
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps(
        {"drift": {"high_threshold": 100000, "moderate_threshold": 100000}}))
    ranked = tmp_path / "r.csv"
    assert main(["score", "--in", str(events), "--out", str(ranked),
                 "--config", str(cfg)]) == 0
    out = pd.read_csv(ranked)
    assert "high_review" not in set(out["risk_tier"])
