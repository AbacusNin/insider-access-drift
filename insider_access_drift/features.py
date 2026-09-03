from __future__ import annotations

import pandas as pd

from .config import DEFAULT_ACTION_WEIGHTS, FeatureConfig
from .schema import validate_events

# Back-compat alias for callers that imported the default table directly.
ACTION_WEIGHTS = DEFAULT_ACTION_WEIGHTS


def prepare(events: pd.DataFrame, config: FeatureConfig | None = None) -> pd.DataFrame:
    cfg = config or FeatureConfig()
    df = validate_events(events)
    df["action_weight"] = df["action"].map(cfg.action_weights).fillna(cfg.default_action_weight)
    df["weighted_sensitivity"] = df["resource_sensitivity"].clip(0, 3) * df["action_weight"]
    df["mb_out"] = df["bytes_out"].fillna(0).clip(lower=0) / (1024 * 1024)
    return df


def user_features(events: pd.DataFrame, config: FeatureConfig | None = None) -> pd.DataFrame:
    cfg = config or FeatureConfig()
    df = prepare(events, cfg)
    g = df.groupby(["user_id", "peer_group"], as_index=False).agg(
        total_events=("resource_id", "count"),
        distinct_resources=("resource_id", "nunique"),
        restricted_touches=("resource_sensitivity", lambda x: int((x >= cfg.restricted_min).sum())),
        crown_jewel_touches=("resource_sensitivity", lambda x: int((x >= cfg.crown_jewel_min).sum())),
        weighted_sensitivity=("weighted_sensitivity", "sum"),
        mb_out=("mb_out", "sum"),
        external_shares=("external_share", "sum"),
        after_hours_events=("after_hours", "sum"),
    )
    g["after_hours_rate"] = g["after_hours_events"] / g["total_events"].clip(lower=1)
    g["external_share_rate"] = g["external_shares"] / g["total_events"].clip(lower=1)
    return g


def add_trend_feature(events: pd.DataFrame, features: pd.DataFrame,
                      split=None, config: FeatureConfig | None = None) -> pd.DataFrame:
    df = prepare(events, config)
    if split is None:
        span = df["event_time"].max() - df["event_time"].min()
        split = df["event_time"].min() + span / 2
    recent = df[df["event_time"] >= split].groupby("user_id")["weighted_sensitivity"].sum()
    prior = df[df["event_time"] < split].groupby("user_id")["weighted_sensitivity"].sum()
    trend = recent.subtract(prior, fill_value=0).clip(lower=0)
    out = features.copy()
    out["sensitivity_trend"] = out["user_id"].map(trend).fillna(0.0)
    return out
