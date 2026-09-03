from __future__ import annotations

import pandas as pd

from insider_access_drift.features import prepare


def flag(events: pd.DataFrame, min_restricted_resources: int = 3) -> pd.Series:
    df = prepare(events)
    contractors = df[(df["peer_group"] == "contractor") & (df["resource_sensitivity"] >= 2)]
    counts = contractors.groupby("user_id")["resource_id"].nunique()
    return counts[counts >= min_restricted_resources]
