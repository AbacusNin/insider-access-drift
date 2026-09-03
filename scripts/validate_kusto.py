"""Validate the KQL rules against the Kusto emulator (Kustainer).

Expects the emulator query endpoint in KUSTO_ENDPOINT (default
http://localhost:8080). Creates AccessEvents, ingests synthetic events,
runs both rules, and asserts the flagged user sets.
"""
from __future__ import annotations

import os
import sys

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

from insider_access_drift.generate import generate_events

ENDPOINT = os.environ.get("KUSTO_ENDPOINT", "http://localhost:8080")
DB = "NetDefaultDB"


def _client() -> KustoClient:
    return KustoClient(KustoConnectionStringBuilder.with_no_authentication(ENDPOINT))


def _ingest_inline(client, df):
    client.execute(DB, (
        ".create table AccessEvents (user_id:string, peer_group:string, "
        "resource_id:string, resource_sensitivity:int, action:string, "
        "bytes_out:long, external_share:int, after_hours:int, "
        "event_time:datetime, persona:string)"
    ))
    rows = []
    for r in df.to_dict("records"):
        rows.append(
            f'"{r["user_id"]}","{r["peer_group"]}","{r["resource_id"]}",'
            f'{int(r["resource_sensitivity"])},"{r["action"]}",{int(r["bytes_out"])},'
            f'{int(r["external_share"])},{int(r["after_hours"])},'
            f'datetime({r["event_time"]}),"{r["persona"]}"'
        )
    client.execute(DB, ".ingest inline into table AccessEvents <|\n" + "\n".join(rows))


def _users(client, path):
    with open(path) as f:
        kql = f.read()
    resp = client.execute(DB, kql)
    return {row["user_id"] for row in resp.primary_results[0]}


def main() -> int:
    client = _client()
    _ingest_inline(client, generate_events())
    drift = _users(client, "detections/kql/repository_access_drift.kql")
    blast = _users(client, "detections/kql/contractor_blast_radius.kql")
    ok = {"u900", "u902"}.issubset(drift) and blast == {"u902"} and "u001" not in drift
    if not ok:
        print(f"FAIL drift={drift} blast={blast}")
        return 1
    print("OK KQL rules fired on the seeded personas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
