import pathlib

import pytest

sigma_collection = pytest.importorskip("sigma.collection")

RULE = pathlib.Path("detections/sigma/external_share_after_hours.yml")


def test_sigma_rule_parses():
    coll = sigma_collection.SigmaCollection.load_ruleset([RULE])
    assert len(coll.rules) == 1
    rule = coll.rules[0]
    assert rule.title == "Sensitive External Share After Hours"
    assert rule.logsource.service == "access_events"
