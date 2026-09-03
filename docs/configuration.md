# Configuration and workflow

Every dial this tool exposes lives in one place: `insider_access_drift/config.py`. `Config()` with no arguments reproduces the default behavior, so you only set what you want to change.

## Two things this tool does not decide

Before the dials, the boundary. Two columns drive almost everything, and neither is computed here. They are inputs you supply on every event:

- `resource_sensitivity` (0 to 3): whether a resource is public, confidential, restricted, or crown jewel. This tool never classifies anything. The value comes from your own data-classification program: sensitivity labels (for example Microsoft Purview), repository topics or tags, a CMDB asset tier, or a data owner's designation. Whatever stamps that number onto an event sits upstream of this tool.
- `peer_group`: the baseline a user is compared against. It comes from your HR or identity system (team, job family, role). Get this wrong and every score for that user is measured against the wrong yardstick. The limitations section of the README calls this the whole scheme's dependency, and it means it.

This tool assumes that classification-and-role program already exists and feeds it clean labels. It does not build one. If you have no sensitivity labels, that is the first project, not this one.

## The tunable surface

Four groups, all optional, all with working defaults.

### features (`FeatureConfig`)
How raw events become per-user features.

| Dial | Default | Meaning |
| --- | --- | --- |
| `action_weights` | view 0.2, download 1.0, clone 1.5, export 2.0, share 2.0, delete 2.5, permission_change 3.0 | how much each action counts before sensitivity weighting |
| `default_action_weight` | 0.5 | weight for an action not in the table above |
| `restricted_min` | 2 | sensitivity at or above this counts as "restricted" |
| `crown_jewel_min` | 3 | sensitivity at or above this counts as "crown jewel" |

### weights (`WeightConfig`)
One weight per scored feature. Higher means the feature pulls harder on the drift score. The rationale for each default is in the README's scoring table.

`distinct_resources` 0.8, `restricted_touches` 1.2, `crown_jewel_touches` 1.8, `weighted_sensitivity` 1.3, `mb_out` 1.2, `external_share_rate` 1.5, `after_hours_rate` 0.7, `sensitivity_trend` 1.0.

### drift (`DriftConfig`)
Tiering and baseline gates.

| Dial | Default | Meaning |
| --- | --- | --- |
| `high_threshold` | 8.0 | drift score at or above this is `high_review` |
| `moderate_threshold` | 4.0 | drift score at or above this is `moderate_review` |
| `min_peer_size` | 4 | a peer group smaller than this is `insufficient_baseline` |
| `min_peer_events` | 20 | a peer group with fewer events than this is `insufficient_baseline` |

### detections (`DetectionConfig`)
Thresholds for the four rules.

| Dial | Default | Rule |
| --- | --- | --- |
| `repo_drift_factor` | 3.0 | repository access drift: peer-median multiplier |
| `repo_drift_min_touches` | 3 | repository access drift: floor on restricted touches |
| `crownjewel_min_sensitivity` | 3 | crown-jewel burst: minimum sensitivity |
| `crownjewel_min_mb` | 100.0 | crown-jewel burst: minimum megabytes moved |
| `crownjewel_actions` | download, clone, export | crown-jewel burst: qualifying actions |
| `external_share_min_sensitivity` | 2 | external share after hours: minimum sensitivity |
| `contractor_min_sensitivity` | 2 | contractor blast radius: minimum sensitivity |
| `contractor_min_restricted_resources` | 3 | contractor blast radius: distinct-resource floor |
| `contractor_peer_group` | "contractor" | contractor blast radius: which peer group counts |

### The native rule files are not generated from this config

`detections/reference/*.py` reads these dials directly. The deployable `detections/kql/*.kql`, `detections/splunk/*.spl`, and `detections/sigma/*.yml` carry the same values as inline literals (for example `med * 3`, `restricted_touches >= 3`, `mb_out >= 100`, `resource_sensitivity|gte: 2`). If you change a detection dial, edit the matching rule file by hand so the deployed query and the reference stay in sync. The scheduled CI jobs assert both fire on the same synthetic events, which is how a drift between them gets caught.

## Setting the dials

As a JSON file, which is the operator interface:

```json
{
  "weights": { "crown_jewel_touches": 2.5, "after_hours_rate": 0.4 },
  "drift": { "high_threshold": 10.0, "min_peer_size": 6 },
  "features": { "restricted_min": 2, "default_action_weight": 0.3 },
  "detections": { "crownjewel_min_mb": 250.0 }
}
```

```
python -m insider_access_drift score --in events.csv --config my-config.json
```

Any key you omit keeps its default. An unknown key is rejected with an error rather than ignored, so a typo fails loudly instead of silently doing nothing.

From code, if you are importing the library:

```python
from insider_access_drift.config import Config
from insider_access_drift.features import add_trend_feature, user_features
from insider_access_drift.score import score

cfg = Config.from_json("my-config.json")   # or Config() for defaults
feats = add_trend_feature(events, user_features(events, cfg.features), config=cfg.features)
ranked = score(feats, cfg.drift)
```

## Workflow

### Trying it on synthetic data

```
pip install -e .
python -m insider_access_drift generate --out events.csv
python -m insider_access_drift score --in events.csv
```

`generate` writes a fixed-seed log with three benign peer groups and three seeded bad actors. `score` prints a ranked table. The three personas surface at the top as `high_review`; the benign users sit near zero. That is the whole loop, on data that touches no real person.

### Running it on your own logs

The step-by-step for a real deployment, with a flowchart of the full loop, is in `operational-workflow.md`.
