# Detection validation

The four rules ship as real KQL/SPL/Sigma and are validated on synthetic data.
A pandas reference of each rule's logic runs in the fast CI gate; the
platform-native rules run against real engines in dedicated jobs.

## Splunk (SPL)

`crownjewel_download_burst.spl` runs against `splunk/splunk` under the Free
license. The `validate-splunk` workflow starts the container, copies the
container's CA cert out and pins it (TLS verification stays on, never
disabled), creates the `access_events` index, ingests synthetic events over
HEC, runs the search over the REST export endpoint, and asserts the flagged
users equal `{u901}`.

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
