from __future__ import annotations

import pandas as pd

from insider_access_drift.config import DetectionConfig, FeatureConfig
from insider_access_drift.features import prepare


def flag(events: pd.DataFrame, config: DetectionConfig | None = None,
         feature_config: FeatureConfig | None = None) -> pd.DataFrame:
    cfg = config or DetectionConfig()
    df = prepare(events, feature_config)
    mask = (
        (df["resource_sensitivity"] >= cfg.external_share_min_sensitivity)
        & (df["external_share"] == 1)
        & (df["after_hours"] == 1)
    )
    return df.loc[mask, ["user_id", "resource_id", "resource_sensitivity", "event_time"]]
