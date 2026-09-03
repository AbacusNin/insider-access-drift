import pandas as pd

from insider_access_drift.features import add_trend_feature, user_features
from insider_access_drift.generate import generate_events
from insider_access_drift.score import FEATURE_COLUMNS, DriftConfig, WeightConfig, robust_z, score


def test_robust_z_flags_outlier():
    s = pd.Series([1, 1, 1, 1, 10])
    z = robust_z(s)
    assert z.iloc[-1] > z.iloc[0]


def test_robust_z_all_equal_returns_zeros():
    s = pd.Series([5, 5, 5, 5])
    assert (robust_z(s) == 0).all()


def test_robust_z_mad_zero_uses_std():
    # median-centered MAD is 0 (majority identical) but std is not
    s = pd.Series([2, 2, 2, 2, 2, 2, 9])
    z = robust_z(s)
    assert z.iloc[-1] > 0


def test_weight_map_covers_all_features():
    assert set(WeightConfig().as_map()) == set(FEATURE_COLUMNS)


def test_default_thresholds():
    c = DriftConfig()
    assert c.high_threshold == 8.0 and c.moderate_threshold == 4.0


def _scored():
    events = generate_events()
    feats = add_trend_feature(events, user_features(events))
    return score(feats).set_index("user_id")


def test_malicious_personas_flag_high():
    s = _scored()
    for user in ("u900", "u901", "u902"):
        assert s.loc[user, "risk_tier"] == "high_review", user


def test_benign_users_stay_baseline():
    s = _scored()
    assert s.loc["u001", "risk_tier"] == "baseline"


def test_small_group_marked_insufficient():
    events = generate_events(benign_per_group=1, benign_events=3)
    feats = add_trend_feature(events, user_features(events))
    s = score(feats)
    assert (s["risk_tier"] == "insufficient_baseline").any()


def test_sorted_descending():
    s = score(add_trend_feature(generate_events(), user_features(generate_events())))
    assert s["drift_score"].is_monotonic_decreasing
