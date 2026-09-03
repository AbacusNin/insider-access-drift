# insider-access-drift

![ci](https://github.com/AbacusNin/insider-access-drift/actions/workflows/ci.yml/badge.svg)

Defensive access-drift scoring and insider-risk detections on synthetic telemetry, for triage practice with no real data involved.

## Threat model

A public video breaks the corporate-espionage supply chain into a ladder of roles: recruiter, handler, the person who actually holds legitimate access, and the buyer on the other end. This tool only models the middle of that ladder, the employee or contractor who already has a badge and a login and either widens their own reach past what the job needs or starts moving material toward the door. Those are the roles that leave access telemetry behind. Recruitment and handling happen off the network and outside anything this tool can see.

Everything here runs against synthetic access events generated in-repo. There is no real user, no real company, and no claim that any of these scores identify an actual insider. The scorer and the detection rules produce triage output: a ranked list and a handful of flagged rows for a human analyst to review next. Nothing here adjudicates guilt, revokes access, or should get wired to an automated response. A high drift score is a reason to look closer, the same as any other alert, not a verdict.

## Telemetry schema

Access events are a flat table with nine required columns, checked by `insider_access_drift.schema.validate_events` before anything else touches them.

- `user_id`, `peer_group`: who did it, and which baseline group they get compared against.
- `resource_id`: what they touched.
- `resource_sensitivity`: 0 through 3, low to crown jewel. Anything outside that range fails validation.
- `action`: one of `view`, `download`, `clone`, `export`, `share`, `delete`, `permission_change`. An action outside that set still parses, it just scores as a weak, catch-all 0.5.
- `bytes_out`: bytes moved off the resource, used to compute megabytes out.
- `external_share`: 0 or 1, whether the action left the org boundary.
- `after_hours`: 0 or 1, whether it happened outside the working window the generator uses.
- `event_time`: a parseable timestamp.

`validate_events` raises `SchemaError` on any of this instead of coercing bad input quietly. Bad sensitivity values, bad flag values, or timestamps that won't parse stop scoring before it starts.

## Quick start

    pip install -e .
    python -m insider_access_drift generate --out events.csv
    python -m insider_access_drift score --in events.csv

`generate` writes a fixed-seed synthetic event log: three benign peer groups (engineer, sales, contractor) plus three seeded bad-actor personas, a slow-roll accumulator, an after-hours crown-jewel puller, and a contractor with unusually broad restricted-resource reach. `score` reads any events CSV matching the schema above, ranks users by drift score, and prints `user_id`, `peer_group`, `drift_score`, and `risk_tier`. Pass `--out ranked.csv` to also write the full scored table.

## How scoring works

![Data flow: the synthetic generator produces events, which feed features, then robust-z scoring with a trend feature and a small-peer-group baseline guard, producing ranked risk tiers. Events also feed the detection rules in parallel.](docs/diagram.svg)

Scoring runs in three stages. `features.user_features` aggregates each user's events into eight per-user features. `features.add_trend_feature` folds in a slow-roll signal. `score.score` turns those features into a peer-relative drift score.

Each feature is compared against the user's own peer group, not the whole population, using a robust z-score (`score.robust_z`): median-centered, scaled by the median absolute deviation, negative values clipped to zero since only unusually high activity matters here. If a peer group's MAD is zero, which happens in small groups with a lot of tied values, the score falls back to standard deviation. If both are zero, everyone in that group scores zero rather than dividing by nothing.

Peer groups need enough data to mean anything. `DriftConfig.min_peer_size` (default 4 users) and `min_peer_events` (default 20 events) gate this. A group under either threshold gets `risk_tier = insufficient_baseline` instead of a real comparison, no matter what the raw numbers look like. A drift score computed against three people isn't a baseline. It's noise, and this tool says so instead of pretending otherwise.

The trend feature, `sensitivity_trend`, splits each user's event history at its midpoint and takes the rise in weighted-sensitivity activity between the first half and the second, floored at zero. It exists to catch the slow-roll pattern: someone who never has one alarming day, but who touches more sensitive material every week than the week before.

The eight features feed a weighted sum, `WeightConfig`, one weight per feature, each picked for what the observable is supposed to catch:

| Feature | Weight | Why |
| --- | --- | --- |
| `distinct_resources` | 0.8 | breadth of access, the weakest signal alone since analysts touch a lot of resources by design |
| `restricted_touches` | 1.2 | reaching into restricted material, a narrower and stronger signal than total resource count |
| `crown_jewel_touches` | 1.8 | the clearest exfiltration signal in the set |
| `weighted_sensitivity` | 1.3 | overall volume of sensitive-action activity, action-weighted |
| `mb_out` | 1.2 | bulk data movement |
| `external_share_rate` | 1.5 | the handler or contractor exfil surface, sharing outside the org |
| `after_hours_rate` | 0.7 | a weak corroborating signal alone, since off-hours activity has plenty of legitimate causes |
| `sensitivity_trend` | 1.0 | the slow-roll accumulation pattern |

`drift_score` is the sum of each feature's robust z-score times its weight. Users above `high_threshold` (8.0) land in `high_review`, above `moderate_threshold` (4.0) in `moderate_review`, everyone else in `baseline`. Both thresholds and every weight live in `DriftConfig` and `WeightConfig`, and they are meant to get tuned per deployment, not treated as universal constants.

## Detections

Four rules, each shipped twice: once as a pandas reference under `detections/reference/`, once as the platform-native query it represents.

| Rule | Native file | ATT&CK | D3FEND |
| --- | --- | --- | --- |
| Repository access drift | `detections/kql/repository_access_drift.kql` | T1213 Data from Information Repositories, T1078 Valid Accounts | Resource Access Pattern Analysis |
| Contractor blast radius | `detections/kql/contractor_blast_radius.kql` | T1078 Valid Accounts | Resource Access Pattern Analysis |
| Crown-jewel download burst | `detections/splunk/crownjewel_download_burst.spl` | T1213, T1567 Exfiltration Over Web Service | User Behavior Analysis |
| External share after hours | `detections/sigma/external_share_after_hours.yml` | T1567 Exfiltration Over Web Service | User Behavior Analysis |

The pandas reference under each rule name is the fast-gate version. It runs on every push and pull request against the synthetic generator's seeded personas and asserts the right users get flagged. It exists so the detection logic gets checked on every commit without spinning up Splunk or a Kusto emulator each time.

The native files are the actual artifacts you would deploy, not restatements written for documentation. They run for real in two scheduled CI jobs: `validate-splunk` against a real `splunk/splunk` container over HEC and the REST search API, and `validate-kusto` against the Kustainer emulator, both against the same synthetic events and asserting the same expected hits as the reference tests. Setup, reproduction steps, and the known verify-at-build items (image tags, endpoint paths) live in `docs/validation.md`.

## Privacy guardrails

- Collect the nine schema columns and nothing else. No message bodies, no file contents, no anything past the access metadata this needs to work.
- Anyone whose access gets scored should know a system does this and roughly what it looks at. Silent behavioral scoring of employees is its own risk, separate from the one it is meant to catch.
- Every output here is triage for a human reviewer, not a decision on its own. `risk_tier` sorts who a person looks at first. It does not replace that person looking.
- A high drift score is not evidence of wrongdoing and should not enter any real process, HR, legal, or otherwise, as if it were. It is a statistical outlier against a peer baseline, and peer baselines get it wrong.

## Limitations and failure modes

Peer grouping is the whole scheme's dependency. `peer_group` here comes from three clean synthetic categories, but a real org's job-role data is messy, and a user assigned to the wrong peer group gets compared against a baseline that has nothing to do with their actual job. Someone doing legitimately broad cross-team work will drift high against a narrow peer group for reasons that have nothing to do with risk.

Small teams break the baseline outright, which is why `insufficient_baseline` exists as its own tier instead of a silent pass. A four-person group is thin enough that one person having an unusual week can look identical to a group-wide shift.

The scorer has no concept of a business cycle. A quarter-end close, a migration, an audit, anything that legitimately spikes normal access for a whole team reads the same as a coordinated insider push, unless the peer baseline itself moves with it. Nothing here tells "this team is busy" apart from "this team is compromised."

None of this is evidence. It is a ranked list built on synthetic-data assumptions that will not hold exactly in any real environment. It tells a human analyst where to look first. It does not tell them what they will find.

## Roadmap

An LLM-backed access narrative explainer is on the list, deliberately not built yet: something that takes a flagged user's event sequence and writes the plain-language version, download volume to a given repository roughly tripled over two weeks while staying just under the crown-jewel threshold, instead of leaving an analyst to read a bare drift score. It would run offline-first against local events, nothing sent anywhere the scorer does not already reach. A tool built to cut down on over-collection should not turn around and ship a flagged user's activity to a third-party API to get it summarized.

## License

MIT. See `LICENSE`.
