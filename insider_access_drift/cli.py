from __future__ import annotations

import argparse

import pandas as pd

from .config import Config
from .features import add_trend_feature, user_features
from .generate import generate_events
from .score import score

_DISPLAY = ["user_id", "peer_group", "drift_score", "risk_tier"]


def _run_score(in_path: str, out_path: str | None, config_path: str | None) -> int:
    cfg = Config.from_json(config_path) if config_path else Config()
    events = pd.read_csv(in_path)
    feats = add_trend_feature(events, user_features(events, cfg.features), config=cfg.features)
    ranked = score(feats, cfg.drift)
    print(ranked[_DISPLAY].to_string(index=False))
    if out_path:
        ranked.to_csv(out_path, index=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="insider-access-drift")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write synthetic access events")
    gen.add_argument("--out", required=True)
    gen.add_argument("--seed", type=int, default=7)

    sc = sub.add_parser("score", help="score an events CSV for access drift")
    sc.add_argument("--in", dest="in_path", required=True)
    sc.add_argument("--out", dest="out_path", default=None)
    sc.add_argument("--config", dest="config_path", default=None,
                    help="JSON file overriding weights, thresholds, or feature dials")

    args = parser.parse_args(argv)
    if args.command == "generate":
        generate_events(seed=args.seed).to_csv(args.out, index=False)
        return 0
    return _run_score(args.in_path, args.out_path, args.config_path)
