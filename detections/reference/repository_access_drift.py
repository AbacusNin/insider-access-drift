from __future__ import annotations

import pandas as pd

from insider_access_drift.config import DetectionConfig, FeatureConfig
from insider_access_drift.features import user_features


def flag(events: pd.DataFrame, config: DetectionConfig | None = None,
         feature_config: FeatureConfig | None = None) -> pd.DataFrame:
    cfg = config or DetectionConfig()
    feats = user_features(events, feature_config)
    parts = []
    for _, g in feats.groupby("peer_group"):
        threshold = g["restricted_touches"].median() * cfg.repo_drift_factor
        hit = g[(g["restricted_touches"] > threshold)
                & (g["restricted_touches"] >= cfg.repo_drift_min_touches)]
        parts.append(hit)
    return pd.concat(parts, ignore_index=True)
