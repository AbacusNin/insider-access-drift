from __future__ import annotations

import pandas as pd

from insider_access_drift.features import user_features


def flag(events: pd.DataFrame, factor: float = 3.0, min_touches: int = 3) -> pd.DataFrame:
    feats = user_features(events)
    parts = []
    for _, g in feats.groupby("peer_group"):
        threshold = g["restricted_touches"].median() * factor
        hit = g[(g["restricted_touches"] > threshold) & (g["restricted_touches"] >= min_touches)]
        parts.append(hit)
    return pd.concat(parts, ignore_index=True)
