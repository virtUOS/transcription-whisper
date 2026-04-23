def test_userinfo_is_admin_default_false():
    from app.models import UserInfo
    u = UserInfo(id="u1", email="u1@example.com")
    assert u.is_admin is False


def test_invitation_create_model_accepts_email():
    from app.models import InvitationCreate
    m = InvitationCreate(email="x@example.com")
    assert m.email == "x@example.com"


def test_invitation_list_item_fields():
    from app.models import InvitationListItem
    m = InvitationListItem(
        id="i1", email="x@example.com", status="pending",
        created_at="2026-04-23 10:00:00", expires_at="2026-04-30 10:00:00",
        created_by="admin@example.com", accepted_at=None,
    )
    assert m.status == "pending"
