from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

FEATURE_COLUMNS: list[str] = [
    "distinct_resources", "restricted_touches", "crown_jewel_touches",
    "weighted_sensitivity", "mb_out", "external_share_rate",
    "after_hours_rate", "sensitivity_trend",
]


@dataclass
class WeightConfig:
    # each weight targets a role/observable from the source ladder; see README
    distinct_resources: float = 0.8    # analyst-style breadth of access
    restricted_touches: float = 1.2    # reaching restricted material
    crown_jewel_touches: float = 1.8   # clearest exfiltration signal
    weighted_sensitivity: float = 1.3  # sensitive-action volume overall
    mb_out: float = 1.2                # bulk movement
    external_share_rate: float = 1.5   # handler/contractor exfil surface
    after_hours_rate: float = 0.7      # weak corroborating signal
    sensitivity_trend: float = 1.0     # slow-roll accumulation

    def as_map(self) -> dict[str, float]:
        return {c: getattr(self, c) for c in FEATURE_COLUMNS}


@dataclass
class DriftConfig:
    min_peer_size: int = 4
    min_peer_events: int = 20
    high_threshold: float = 8.0
    moderate_threshold: float = 4.0
    weights: WeightConfig = field(default_factory=WeightConfig)


def robust_z(series: pd.Series) -> pd.Series:
    median = series.median()
    mad = (series - median).abs().median()
    if mad and not np.isnan(mad):
        return 0.6745 * (series - median) / mad
    std = series.std(ddof=0)
    if std and not np.isnan(std):
        return (series - median) / std
    return pd.Series(np.zeros(len(series)), index=series.index)
