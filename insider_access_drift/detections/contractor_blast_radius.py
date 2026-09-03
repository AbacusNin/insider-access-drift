from __future__ import annotations

import pandas as pd

from insider_access_drift.config import DetectionConfig, FeatureConfig
from insider_access_drift.features import prepare


def flag(events: pd.DataFrame, config: DetectionConfig | None = None,
         feature_config: FeatureConfig | None = None) -> pd.Series:
    cfg = config or DetectionConfig()
    df = prepare(events, feature_config)
    contractors = df[(df["peer_group"] == cfg.contractor_peer_group)
                     & (df["resource_sensitivity"] >= cfg.contractor_min_sensitivity)]
    counts = contractors.groupby("user_id")["resource_id"].nunique()
    return counts[counts >= cfg.contractor_min_restricted_resources]
