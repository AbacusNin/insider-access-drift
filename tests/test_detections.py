from reference import crownjewel_download_burst, repository_access_drift

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
