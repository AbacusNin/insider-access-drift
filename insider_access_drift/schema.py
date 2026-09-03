from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "user_id", "peer_group", "resource_id", "resource_sensitivity",
    "action", "bytes_out", "external_share", "after_hours", "event_time",
}

SENSITIVITY_LEVELS = {0, 1, 2, 3}


class SchemaError(ValueError):
    """Raised when an event frame violates the access-log contract."""


def validate_events(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise SchemaError(f"missing required columns: {sorted(missing)}")

    parsed = pd.to_datetime(df["event_time"], errors="coerce")
    if parsed.isna().any():
        raise SchemaError(f"{int(parsed.isna().sum())} rows have unparseable event_time")

    sens = set(pd.to_numeric(df["resource_sensitivity"], errors="coerce").dropna().unique())
    if not sens.issubset(SENSITIVITY_LEVELS):
        raise SchemaError("resource_sensitivity must be one of 0, 1, 2, 3")

    for col in ("external_share", "after_hours"):
        vals = set(pd.to_numeric(df[col], errors="coerce").dropna().unique())
        if not vals.issubset({0, 1}):
            raise SchemaError(f"{col} must be 0 or 1")

    out = df.copy()
    out["event_time"] = parsed
    return out
