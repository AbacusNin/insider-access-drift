from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path

from .score import DriftConfig, WeightConfig

# Default per-action weight applied before sensitivity weighting. An action not
# listed here scores as `FeatureConfig.default_action_weight`.
DEFAULT_ACTION_WEIGHTS: dict[str, float] = {
    "view": 0.2, "download": 1.0, "clone": 1.5, "export": 2.0,
    "share": 2.0, "delete": 2.5, "permission_change": 3.0,
}


@dataclass
class FeatureConfig:
    """Dials for how raw events become per-user features."""
    action_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_ACTION_WEIGHTS))
    default_action_weight: float = 0.5   # weight for an action not in action_weights
    restricted_min: int = 2              # sensitivity >= this counts as "restricted"
    crown_jewel_min: int = 3             # sensitivity >= this counts as "crown jewel"


@dataclass
class DetectionConfig:
    """Thresholds for the four reference detections. The native KQL/SPL/Sigma
    files carry the same literals and must be edited to match if these change."""
    repo_drift_factor: float = 3.0
    repo_drift_min_touches: int = 3
    crownjewel_min_sensitivity: int = 3
    crownjewel_min_mb: float = 100.0
    crownjewel_actions: tuple[str, ...] = ("download", "clone", "export")
    external_share_min_sensitivity: int = 2
    contractor_min_sensitivity: int = 2
    contractor_min_restricted_resources: int = 3
    contractor_peer_group: str = "contractor"


@dataclass
class Config:
    """The full tunable surface as one object. Every field has a working default,
    so `Config()` reproduces the tool's out-of-the-box behavior."""
    features: FeatureConfig = field(default_factory=FeatureConfig)
    weights: WeightConfig = field(default_factory=WeightConfig)
    drift: DriftConfig = field(default_factory=DriftConfig)
    detections: DetectionConfig = field(default_factory=DetectionConfig)

    def __post_init__(self) -> None:
        # score() reads its weights off DriftConfig; keep the two in sync.
        self.drift.weights = self.weights

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        cfg = cls()
        _apply(cfg.features, data.get("features", {}))
        _apply(cfg.weights, data.get("weights", {}))
        _apply(cfg.drift, {k: v for k, v in data.get("drift", {}).items() if k != "weights"})
        _apply(cfg.detections, data.get("detections", {}))
        cfg.drift.weights = cfg.weights
        return cfg

    @classmethod
    def from_json(cls, path: str) -> Config:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _apply(obj, overrides: dict) -> None:
    valid = {f.name for f in fields(obj)}
    for key, value in overrides.items():
        if key not in valid:
            raise ValueError(f"unknown config key '{key}' for {type(obj).__name__}")
        setattr(obj, key, value)
