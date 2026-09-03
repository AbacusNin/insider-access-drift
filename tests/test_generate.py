import pandas as pd
from insider_access_drift.generate import generate_events
from insider_access_drift.schema import validate_events, REQUIRED_COLUMNS


def test_output_is_schema_valid():
    df = generate_events()
    validate_events(df)  # must not raise
    assert REQUIRED_COLUMNS.issubset(df.columns)


def test_reproducible_by_seed():
    a = generate_events(seed=7)
    b = generate_events(seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_contains_all_personas():
    df = generate_events()
    assert set(df["persona"]) >= {
        "benign", "slow_roll", "after_hours_crownjewel", "broad_contractor"
    }


def test_malicious_users_are_distinct():
    df = generate_events()
    mal = df[df["persona"] != "benign"]["user_id"].unique()
    assert set(mal) == {"u900", "u901", "u902"}
