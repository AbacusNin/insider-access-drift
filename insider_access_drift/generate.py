from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNS = [
    "user_id", "peer_group", "resource_id", "resource_sensitivity",
    "action", "bytes_out", "external_share", "after_hours", "event_time", "persona",
]

_GROUPS = {
    "engineer": [f"repo-{i}" for i in range(1, 8)],
    "sales": [f"crm-{i}" for i in range(1, 6)],
    "contractor": [f"proj-{i}" for i in range(1, 6)],
}

_START = pd.Timestamp("2026-07-01")


def _mb(x: float) -> int:
    return int(x * 1024 * 1024)


def _benign(rng, group, resources, user, n):
    rows = []
    for _ in range(n):
        res = resources[int(rng.integers(0, len(resources)))]
        sens = int(rng.choice([0, 1], p=[0.7, 0.3]))
        action = "view" if rng.random() < 0.8 else "download"
        ts = _START + pd.Timedelta(days=int(rng.integers(0, 14)),
                                   hours=int(rng.integers(9, 18)),
                                   minutes=int(rng.integers(0, 60)))
        rows.append([user, group, res, sens, action,
                     _mb(rng.uniform(0.01, 2.0)), 0, 0, ts.isoformat(), "benign"])
    return rows


def _slow_roll(rng):
    rows = []
    for day in range(14):
        for t in range(1 + day // 2):  # rising cadence, no single spike
            res = f"repo-{1 + (day + t) % 7}"
            ts = _START + pd.Timedelta(days=day, hours=int(rng.integers(10, 17)),
                                       minutes=int(rng.integers(0, 60)))
            rows.append(["u900", "engineer", res, 2, "download",
                         _mb(rng.uniform(1.0, 5.0)), 0, 0, ts.isoformat(), "slow_roll"])
    return rows


def _after_hours_crownjewel(rng):
    rows = []
    for day in (3, 5, 9):
        res = f"repo-{1 + day % 7}"
        ts = _START + pd.Timedelta(days=day, hours=23, minutes=int(rng.integers(0, 60)))
        rows.append(["u901", "engineer", res, 3, "clone",
                     _mb(rng.uniform(400, 900)), 1, 1, ts.isoformat(),
                     "after_hours_crownjewel"])
    return rows


def _broad_contractor(rng):
    rows = []
    for i in range(1, 6):
        ts = _START + pd.Timedelta(days=int(rng.integers(0, 14)),
                                   hours=int(rng.integers(9, 18)))
        rows.append(["u902", "contractor", f"proj-{i}", 2, "export",
                     _mb(rng.uniform(50, 200)), 1, 0, ts.isoformat(), "broad_contractor"])
    return rows


def generate_events(seed: int = 7, benign_per_group: int = 4,
                    benign_events: int = 25) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    uid = 0
    for group, resources in _GROUPS.items():
        for _ in range(benign_per_group):
            uid += 1
            rows += _benign(rng, group, resources, f"u{uid:03d}", benign_events)
    rows += _slow_roll(rng)
    rows += _after_hours_crownjewel(rng)
    rows += _broad_contractor(rng)
    return pd.DataFrame(rows, columns=COLUMNS)
