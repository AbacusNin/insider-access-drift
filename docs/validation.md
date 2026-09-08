# Detection validation

The four rules ship as real KQL, SPL, and Sigma. Both forms are validated on
synthetic data. The pandas reference of each rule runs in the fast CI gate; the
platform-native rules run against real engines in dedicated jobs.

## Splunk (SPL)

`crownjewel_download_burst.spl` runs against `splunk/splunk` under the Free
license. The `validate-splunk` workflow starts the container, copies out its CA
cert, and pins it, so TLS verification stays on. Then it creates the
`access_events` index. From there it ingests synthetic events over HEC, runs the
search over the REST export endpoint, and asserts the flagged users equal
`{u901}`.

Reproduce locally:

    docker run -d --name splunk -e SPLUNK_START_ARGS=--accept-license \
      -e SPLUNK_LICENSE_URI=Free -e SPLUNK_PASSWORD=Changed-me-2026 \
      -e SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000 \
      -p 8088:8088 -p 8089:8089 splunk/splunk:latest
    # wait for readiness, then pin the CA and create the index:
    docker cp splunk:/opt/splunk/etc/auth/cacert.pem splunk-ca.pem
    curl -s --cacert splunk-ca.pem -u admin:Changed-me-2026 -X POST \
      https://localhost:8089/services/data/indexes -d name=access_events
    SPLUNK_PASSWORD=Changed-me-2026 \
      SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000 \
      SPLUNK_CA=splunk-ca.pem \
      python scripts/validate_splunk.py

Verify at build: the exact `splunk/splunk` tag, the current Free-license
volume limit, and the `cacert.pem` path in the image. All can change.

## KQL (Kusto emulator)

`repository_access_drift.kql` and `contractor_blast_radius.kql` run against the
Kusto emulator (Kustainer). The `validate-kusto` workflow starts the emulator,
creates `AccessEvents`, and ingests synthetic events inline. It runs both rules
and checks the results: `{u900, u902}` among the drift hits, and `{u902}` for
the blast radius.

The emulator is ADX-dialect KQL. These rules stay within the shared core, so a
Sentinel deployment runs the same text. Each rule file notes that.

Reproduce locally:

    docker run -d --name kustainer -p 8080:8080 -e ACCEPT_EULA=Y \
      mcr.microsoft.com/azuredataexplorer/kustainer-linux:latest
    KUSTO_ENDPOINT=http://localhost:8080 python scripts/validate_kusto.py

The readiness check POSTs `.show version` with `curl --fail`. A plain `curl -s`
GET is not enough: it treats any response as ready, even a 404 or 405.

Verify at build: the emulator image tag, the exact readiness/query endpoint
paths, and whether `.show version` is the right mgmt probe for this emulator
build. Confirm against the current emulator docs.
