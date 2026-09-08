# Detection validation

The four rules ship as real KQL, SPL, and Sigma. Both forms are validated on
synthetic data. The pandas reference of each rule runs in the fast CI gate; the
platform-native rules run against real engines in dedicated jobs.

## Splunk (SPL)

`crownjewel_download_burst.spl` runs against `splunk/splunk` on the enterprise
trial license. The Free license disables authenticated remote login, so the REST
API rejects every credential. The trial provides real auth. Its 500 MB/day cap
sits far above the synthetic volume here.

The `validate-splunk` workflow generates a throwaway CA and a server cert that
names `localhost`. It hands both to Splunk through a mounted `default.yml` and
verifies against that CA. Splunk's own default cert is named
`SplunkServerDefaultCert`. That name never matches `localhost`, so pinning the
presented cert fails the hostname check; a generated cert passes. Verification
stays on for both the management port and HEC. The workflow then creates the
`access_events` index, ingests synthetic events over HEC, runs the search over
the REST export endpoint, and asserts the flagged users equal `{u901}`.

Reproduce locally:

    # generate a CA and a localhost server cert
    mkdir -p certs
    openssl req -x509 -newkey rsa:2048 -nodes -days 3 \
      -keyout certs/ca.key -out certs/ca.pem -subj "/CN=local-test-ca"
    openssl req -newkey rsa:2048 -nodes \
      -keyout certs/server.key -out certs/server.csr -subj "/CN=localhost"
    openssl x509 -req -in certs/server.csr -days 3 \
      -CA certs/ca.pem -CAkey certs/ca.key -CAcreateserial \
      -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1") \
      -out certs/server.crt
    cat certs/server.key certs/server.crt certs/ca.pem > certs/server-combined.pem
    chmod 0644 certs/*.pem
    # point Splunk at the generated cert
    cat > splunk-defaults.yml <<'YML'
    splunk:
      password: Changed-me-2026
      ssl:
        enable: true
        cert: /tmp/certs/server-combined.pem
        ca: /tmp/certs/ca.pem
      hec:
        cert: /tmp/certs/server-combined.pem
    YML
    docker run -d --name splunk \
      -e SPLUNK_GENERAL_TERMS=--accept-sgt-current-at-splunk-com \
      -e SPLUNK_START_ARGS=--accept-license \
      -e SPLUNK_PASSWORD=Changed-me-2026 \
      -e SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000 \
      -v "$PWD/certs":/tmp/certs:ro \
      -v "$PWD/splunk-defaults.yml":/tmp/defaults/default.yml:ro \
      -p 8088:8088 -p 8089:8089 splunk/splunk:latest
    # once the mgmt API answers 200, create the index and validate:
    curl -s --cacert certs/ca.pem -u admin:Changed-me-2026 -X POST \
      https://localhost:8089/services/data/indexes -d name=access_events
    SPLUNK_PASSWORD=Changed-me-2026 \
      SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000 \
      SPLUNK_CA=certs/ca.pem \
      python scripts/validate_splunk.py

Verify at build: the exact `splunk/splunk` tag, the `default.yml` SSL keys, and
the current trial-license volume limit. All three can change.

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
