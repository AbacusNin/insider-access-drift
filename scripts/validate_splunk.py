"""Validate crownjewel_download_burst.spl against a running Splunk.

Expects a Splunk instance reachable via env:
  SPLUNK_HOST (default localhost), SPLUNK_HEC_TOKEN, SPLUNK_PASSWORD,
  SPLUNK_CA (path to the container's CA cert; TLS verification stays on).
Ingests synthetic events via HEC, runs the search over the REST API,
and asserts the flagged users equal {u901}.
"""
from __future__ import annotations

import json
import os
import sys
import time

import requests

from insider_access_drift.generate import generate_events

HOST = os.environ.get("SPLUNK_HOST", "localhost")
HEC_TOKEN = os.environ["SPLUNK_HEC_TOKEN"]
PASSWORD = os.environ["SPLUNK_PASSWORD"]
# Pin the container's self-signed CA rather than disabling verification.
# Falls back to True (system trust) so this never silently becomes insecure.
VERIFY = os.environ.get("SPLUNK_CA") or True
HEC = f"https://{HOST}:8088/services/collector/event"
REST = f"https://{HOST}:8089/services/search/jobs/export"
EXPECTED = {"u901"}


def ingest(df):
    for row in df.to_dict("records"):
        # pandas hands back numpy scalars (int64, etc.) for numeric columns;
        # requests' json encoder chokes on those, so coerce to native types.
        row = {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
        payload = {"index": "access_events", "sourcetype": "_json", "event": row}
        r = requests.post(HEC, headers={"Authorization": f"Splunk {HEC_TOKEN}"},
                          json=payload, verify=VERIFY, timeout=30)
        r.raise_for_status()


def search():
    with open("detections/splunk/crownjewel_download_burst.spl") as f:
        spl = f.read()
    # strip the comment macro line for the export endpoint
    spl = "\n".join(line for line in spl.splitlines() if not line.strip().startswith("`comment"))
    r = requests.post(REST, auth=("admin", PASSWORD),
                      data={"search": f"search {spl}", "output_mode": "json"},
                      verify=VERIFY, timeout=120)
    r.raise_for_status()
    users = set()
    for line in r.text.splitlines():
        line = line.strip()
        if not line:
            continue
        result = json.loads(line).get("result")
        if result and "user_id" in result:
            users.add(result["user_id"])
    return users


def main() -> int:
    ingest(generate_events())
    time.sleep(15)  # allow indexing
    got = search()
    if got != EXPECTED:
        print(f"FAIL expected {EXPECTED} got {got}")
        return 1
    print("OK crownjewel_download_burst fired on the seeded persona only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
