from __future__ import annotations

import pandas as pd

from insider_access_drift.features import prepare


def flag(events: pd.DataFrame, min_mb: float = 100.0,
         actions=("download", "clone", "export")) -> pd.DataFrame:
    df = prepare(events)
    mask = (
        (df["resource_sensitivity"] >= 3)
        & (df["action"].isin(actions))
        & (df["mb_out"] >= min_mb)
    )
    return df.loc[mask, ["user_id", "resource_id", "mb_out", "event_time"]]
