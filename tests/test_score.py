import pandas as pd

from insider_access_drift.score import FEATURE_COLUMNS, DriftConfig, WeightConfig, robust_z


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
