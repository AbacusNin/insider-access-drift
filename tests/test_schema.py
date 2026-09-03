import pandas as pd
import pytest
from insider_access_drift.schema import validate_events, SchemaError, REQUIRED_COLUMNS


def _row(**kw):
    base = dict(user_id="u1", peer_group="engineer", resource_id="repo-a",
                resource_sensitivity=1, action="view", bytes_out=1000,
                external_share=0, after_hours=0, event_time="2026-07-01 10:00")
    base.update(kw)
    return base


def test_valid_frame_parses_timestamps():
    df = pd.DataFrame([_row()])
    out = validate_events(df)
    assert pd.api.types.is_datetime64_any_dtype(out["event_time"])


def test_missing_column_raises():
    df = pd.DataFrame([_row()]).drop(columns=["bytes_out"])
    with pytest.raises(SchemaError):
        validate_events(df)


def test_bad_timestamp_raises():
    df = pd.DataFrame([_row(event_time="not-a-date")])
    with pytest.raises(SchemaError):
        validate_events(df)


def test_out_of_range_sensitivity_raises():
    df = pd.DataFrame([_row(resource_sensitivity=9)])
    with pytest.raises(SchemaError):
        validate_events(df)


def test_non_numeric_sensitivity_raises():
    df = pd.DataFrame([_row(resource_sensitivity="high")])
    with pytest.raises(SchemaError):
        validate_events(df)


def test_non_numeric_flag_raises():
    df = pd.DataFrame([_row(external_share="yes")])
    with pytest.raises(SchemaError):
        validate_events(df)


def test_missing_flag_value_raises():
    df = pd.DataFrame([_row(after_hours=None)])
    with pytest.raises(SchemaError):
        validate_events(df)
