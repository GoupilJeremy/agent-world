"""Integration tests for authenticated, recipient-constrained file shares."""

from pathlib import Path
from typing import Generator

import pytest
from flask.testing import FlaskClient

from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.agent import Agent
from backend.models.base import db
from backend.models.user import User


@pytest.fixture
def share_auth_api(
    tmp_path: Path,
) -> Generator[tuple[FlaskClient, Agent, User, User], None, None]:
    """Return an isolated API with a share recipient and another user."""

    class ShareAuthConfig(TestingConfig):
        OUTPUT_DIR = str(tmp_path / "auth-outputs")
        SECRET_KEY = "share-auth-test-secret"
        AUTH_ACCESS_TOKEN_TTL_SECONDS = 300

    app = create_app(ShareAuthConfig)
    with app.app_context():
        recipient = User.create(
            email="recipient@example.test",
            username="recipient",
            password="correct horse battery staple",
        )
        outsider = User.create(
            email="outsider@example.test",
            username="outsider",
            password="another correct password",
        )
        agent = Agent.create(name="Authenticated share agent", created_by=recipient.id)
        yield app.test_client(), agent, recipient, outsider
        db.session.remove()
        db.drop_all()


def _login(client: FlaskClient, identifier: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def _create_file(client: FlaskClient, agent_id: int) -> dict:
    response = client.post(
        "/api/files",
        json={
            "agent_id": agent_id,
            "name": "private-report",
            "format": "txt",
            "content": "private content",
        },
    )
    assert response.status_code == 201
    return response.get_json()


def _create_share(
    client: FlaskClient,
    created_file: dict,
    *,
    recipient_user_id: int | None,
    permission: str = "read",
) -> dict:
    response = client.post(
        f"/api/files/{created_file['id']}/shares",
        headers={"X-Management-Token": created_file["management_token"]},
        json={
            "permission": permission,
            "recipient_user_id": recipient_user_id,
            "expires_in_seconds": 300,
        },
    )
    assert response.status_code == 201
    return response.get_json()


def test_login_and_current_user_use_existing_password_hashes(share_auth_api) -> None:
    client, _, recipient, _ = share_auth_api

    malformed = client.post("/api/auth/login", data="not-json")
    wrong_password = client.post(
        "/api/auth/login",
        json={"identifier": recipient.username, "password": "wrong"},
    )
    unknown_user = client.post(
        "/api/auth/login",
        json={"identifier": "unknown", "password": "wrong"},
    )
    access_token = _login(client, recipient.email, "correct horse battery staple")
    current = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert malformed.status_code == 400
    assert malformed.get_json()["code"] == "invalid_request"
    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.get_json() == unknown_user.get_json()
    assert wrong_password.headers["WWW-Authenticate"] == "Bearer"
    assert current.status_code == 200
    assert current.get_json()["id"] == recipient.id
    assert current.get_json()["username"] == recipient.username
    assert "password_hash" not in current.get_json()
    assert "WWW-Authenticate" not in current.headers
    assert current.headers["Cache-Control"].startswith("no-store")


def test_recipient_share_requires_matching_active_user(share_auth_api) -> None:
    client, agent, recipient, outsider = share_auth_api
    created_file = _create_file(client, agent.id)
    private_share = _create_share(client, created_file, recipient_user_id=recipient.id)
    recipient_token = _login(client, recipient.username, "correct horse battery staple")
    outsider_token = _login(client, outsider.username, "another correct password")

    anonymous = client.get(private_share["preview_url"])
    malformed = client.get(
        private_share["preview_url"], headers={"Authorization": "Bearer invalid"}
    )
    wrong_user = client.get(
        private_share["preview_url"],
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    allowed = client.get(
        private_share["preview_url"],
        headers={"Authorization": f"Bearer {recipient_token}"},
    )

    assert anonymous.status_code == 401
    assert anonymous.get_json()["code"] == "authentication_required"
    assert anonymous.headers["WWW-Authenticate"] == "Bearer"
    assert malformed.status_code == 401
    assert malformed.get_json()["code"] == "invalid_access_token"
    assert wrong_user.status_code == 403
    assert wrong_user.get_json()["code"] == "forbidden"
    assert allowed.status_code == 200
    assert allowed.get_json()["content"] == "private content"

    recipient.is_active = False
    db.session.commit()
    disabled = client.get(
        private_share["preview_url"],
        headers={"Authorization": f"Bearer {recipient_token}"},
    )
    assert disabled.status_code == 401
    assert disabled.get_json()["code"] == "invalid_access_token"


def test_public_bearer_share_remains_anonymous(share_auth_api) -> None:
    client, agent, _, _ = share_auth_api
    created_file = _create_file(client, agent.id)
    public_share = _create_share(client, created_file, recipient_user_id=None)

    anonymous = client.get(public_share["download_url"])
    ignored_invalid_bearer = client.get(
        public_share["preview_url"], headers={"Authorization": "Bearer invalid"}
    )

    assert anonymous.status_code == 200
    assert anonymous.data == b"private content"
    assert ignored_invalid_bearer.status_code == 200


def test_recipient_write_share_keeps_permission_enforcement(share_auth_api) -> None:
    client, agent, recipient, _ = share_auth_api
    created_file = _create_file(client, agent.id)
    read_share = _create_share(client, created_file, recipient_user_id=recipient.id)
    write_share = _create_share(
        client,
        created_file,
        recipient_user_id=recipient.id,
        permission="write",
    )
    access_token = _login(client, recipient.username, "correct horse battery staple")
    auth_header = {"Authorization": f"Bearer {access_token}"}

    denied = client.put(read_share["content_url"], headers=auth_header, data="denied")
    allowed = client.put(
        write_share["content_url"], headers=auth_header, data="updated"
    )

    assert denied.status_code == 403
    assert allowed.status_code == 201
    assert allowed.get_json()["version"] == 2
