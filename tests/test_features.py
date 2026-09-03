import pandas as pd

from insider_access_drift.features import user_features


def _events():
    rows = [
        ["u1", "eng", "r1", 1, "view", 1_000, 0, 0, "2026-07-01 10:00"],
        ["u1", "eng", "r2", 3, "download", 500_000_000, 1, 1, "2026-07-02 23:00"],
        ["u2", "eng", "r1", 1, "view", 1_000, 0, 0, "2026-07-01 11:00"],
    ]
    cols = ["user_id", "peer_group", "resource_id", "resource_sensitivity",
            "action", "bytes_out", "external_share", "after_hours", "event_time"]
    return pd.DataFrame(rows, columns=cols)


def test_counts_and_rates():
    feats = user_features(_events()).set_index("user_id")
    assert feats.loc["u1", "total_events"] == 2
    assert feats.loc["u1", "distinct_resources"] == 2
    assert feats.loc["u1", "restricted_touches"] == 1  # sens>=2
    assert feats.loc["u1", "crown_jewel_touches"] == 1  # sens>=3
    assert feats.loc["u1", "external_shares"] == 1
    assert feats.loc["u1", "after_hours_events"] == 1
    assert round(feats.loc["u1", "after_hours_rate"], 3) == 0.5
    assert feats.loc["u2", "restricted_touches"] == 0
