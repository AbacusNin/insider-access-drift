from __future__ import annotations

import pandas as pd

from insider_access_drift.config import DetectionConfig, FeatureConfig
from insider_access_drift.features import prepare


def flag(events: pd.DataFrame, config: DetectionConfig | None = None,
         feature_config: FeatureConfig | None = None) -> pd.DataFrame:
    cfg = config or DetectionConfig()
    df = prepare(events, feature_config)
    mask = (
        (df["resource_sensitivity"] >= cfg.crownjewel_min_sensitivity)
        & (df["action"].isin(cfg.crownjewel_actions))
        & (df["mb_out"] >= cfg.crownjewel_min_mb)
    )
    return df.loc[mask, ["user_id", "resource_id", "mb_out", "event_time"]]
