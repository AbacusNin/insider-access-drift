from reference import (
    contractor_blast_radius,
    crownjewel_download_burst,
    external_share_after_hours,
    repository_access_drift,
)

from insider_access_drift.generate import generate_events


def test_repo_drift_flags_slow_roll_and_contractor():
    events = generate_events()
    flagged = set(repository_access_drift.flag(events)["user_id"])
    assert "u900" in flagged   # heavy restricted access
    assert "u902" in flagged   # broad contractor restricted access
    assert "u001" not in flagged


def test_crownjewel_burst_flags_only_crownjewel_persona():
    events = generate_events()
    flagged = set(crownjewel_download_burst.flag(events)["user_id"])
    assert flagged == {"u901"}


def test_external_share_after_hours_flags_crownjewel_persona():
    events = generate_events()
    flagged = set(external_share_after_hours.flag(events)["user_id"])
    assert flagged == {"u901"}


def test_contractor_blast_radius_flags_broad_contractor():
    events = generate_events()
    flagged = contractor_blast_radius.flag(events)
    assert "u902" in flagged.index
    assert flagged.loc["u902"] >= 3
