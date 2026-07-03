"""Invitation guard logic (pure) — RBAC ranks, role whitelist, expiry, email body."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from metavita_api.deps import ROLE_RANK
from metavita_api.routes.invites import VALID_ROLES, _invite_email_html, _is_expired


class _Inv:
    def __init__(self, expires_at):
        self.expires_at = expires_at


def test_role_rank_is_ordered():
    assert ROLE_RANK["owner"] > ROLE_RANK["admin"] > ROLE_RANK["editor"] > ROLE_RANK["viewer"]


def test_cannot_invite_as_owner():
    # Ownership isn't grantable by invite; only admin/editor/viewer.
    assert VALID_ROLES == {"admin", "editor", "viewer"}


def test_is_expired():
    assert _is_expired(_Inv(datetime.now(UTC) - timedelta(days=1))) is True
    assert _is_expired(_Inv(datetime.now(UTC) + timedelta(days=1))) is False
    assert _is_expired(_Inv(None)) is False  # no expiry set → never expired


def test_email_body_contains_link_and_context():
    html = _invite_email_html(
        workspace="Acme", role="editor", url="https://app/invite/tok123", inviter="Sam"
    )
    assert "https://app/invite/tok123" in html
    assert "Acme" in html and "editor" in html and "Sam" in html
