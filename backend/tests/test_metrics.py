def test_invitation_metrics_defined():
    from app.metrics import (
        invitations_created_total,
        invitations_accepted_total,
        invitations_expired_total,
        invitations_revoked_total,
    )
    # If metrics are disabled (no prometheus_client), these will be None — both states are acceptable.
    for m in (invitations_created_total, invitations_accepted_total,
              invitations_expired_total, invitations_revoked_total):
        assert m is None or hasattr(m, "inc")
