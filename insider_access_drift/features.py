from __future__ import annotations

import pandas as pd

from .schema import validate_events

ACTION_WEIGHTS: dict[str, float] = {
    "view": 0.2, "download": 1.0, "clone": 1.5, "export": 2.0,
    "share": 2.0, "delete": 2.5, "permission_change": 3.0,
}


def prepare(events: pd.DataFrame) -> pd.DataFrame:
    df = validate_events(events)
    df["action_weight"] = df["action"].map(ACTION_WEIGHTS).fillna(0.5)
    df["weighted_sensitivity"] = df["resource_sensitivity"].clip(0, 3) * df["action_weight"]
    df["mb_out"] = df["bytes_out"].fillna(0).clip(lower=0) / (1024 * 1024)
    return df


def user_features(events: pd.DataFrame) -> pd.DataFrame:
    df = prepare(events)
    g = df.groupby(["user_id", "peer_group"], as_index=False).agg(
        total_events=("resource_id", "count"),
        distinct_resources=("resource_id", "nunique"),
        restricted_touches=("resource_sensitivity", lambda x: int((x >= 2).sum())),
        crown_jewel_touches=("resource_sensitivity", lambda x: int((x >= 3).sum())),
        weighted_sensitivity=("weighted_sensitivity", "sum"),
        mb_out=("mb_out", "sum"),
        external_shares=("external_share", "sum"),
        after_hours_events=("after_hours", "sum"),
    )
    g["after_hours_rate"] = g["after_hours_events"] / g["total_events"].clip(lower=1)
    g["external_share_rate"] = g["external_shares"] / g["total_events"].clip(lower=1)
    return g
