from __future__ import annotations

import pandas as pd

from insider_access_drift.features import prepare


def flag(events: pd.DataFrame) -> pd.DataFrame:
    df = prepare(events)
    mask = (
        (df["resource_sensitivity"] >= 2)
        & (df["external_share"] == 1)
        & (df["after_hours"] == 1)
    )
    return df.loc[mask, ["user_id", "resource_id", "resource_sensitivity", "event_time"]]
