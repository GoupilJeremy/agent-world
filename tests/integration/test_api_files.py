"""Integration tests for generated-file API resources."""

from pathlib import Path

import pytest

from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.agent import Agent
from backend.models.base import db
from backend.models.generated_file import FileShare, GeneratedFile


@pytest.fixture
def file_api(tmp_path: Path):
    """Return a client backed by isolated storage and database state."""

    class FileApiConfig(TestingConfig):
        OUTPUT_DIR = str(tmp_path / "api-outputs")
        FILE_CLEANUP_TOKEN = "cleanup-secret"
        FILE_KEEP_LATEST_VERSIONS = 1
        FILE_OBSOLETE_TTL_DAYS = 1

    app = create_app(FileApiConfig)
    with app.app_context():
        db.create_all()
        agent = Agent.create(name="File API agent")
        yield app.test_client(), agent, tmp_path
        db.session.remove()
        db.drop_all()


def create_file(client, agent_id: int, **overrides):
    payload = {
        "agent_id": agent_id,
        "name": "result",
        "format": "json",
        "content": {"answer": 42},
    }
    payload.update(overrides)
    response = client.post("/api/files", json=payload)
    assert response.status_code == 201
    return response.get_json()


def management_headers(created: dict) -> dict[str, str]:
    return {"X-Management-Token": created["management_token"]}


def test_create_preview_append_restore_and_download(file_api) -> None:
    client, agent, _ = file_api
    created = create_file(client, agent.id)
    file_id = created["id"]
    headers = management_headers(created)

    denied = client.get(f"/api/files/{file_id}/preview")
    denied_metadata = client.get(f"/api/files/{file_id}")
    preview = client.get(f"/api/files/{file_id}/preview", headers=headers)
    appended = client.post(
        f"/api/files/{file_id}/versions",
        headers=headers,
        json={"content": {"answer": 43}},
    )
    restored = client.post(f"/api/files/{file_id}/versions/1/restore", headers=headers)
    versions = client.get(f"/api/files/{file_id}/versions", headers=headers)
    download = client.get(f"/api/files/{file_id}/download", headers=headers)

    assert denied.status_code == 403
    assert denied_metadata.status_code == 403
    assert preview.status_code == 200
    assert preview.get_json()["content"] == {"answer": 42}
    assert preview.headers["Cache-Control"].startswith("no-store")
    assert appended.get_json()["version"] == 2
    assert restored.get_json()["version"] == 3
    assert [item["version"] for item in versions.get_json()] == [3, 2, 1]
    assert download.status_code == 200
    assert download.headers["X-Content-Type-Options"] == "nosniff"
    assert b'"answer": 42' in download.data
    assert "storage_root" not in str(preview.get_json())
    assert "relative_path" not in str(versions.get_json())


def test_read_and_write_share_endpoints_and_revocation(file_api) -> None:
    client, agent, _ = file_api
    created = create_file(
        client,
        agent.id,
        name="shared-notes",
        format="md",
        content="# Initial",
    )
    file_id = created["id"]
    headers = management_headers(created)
    read_response = client.post(
        f"/api/files/{file_id}/shares",
        headers=headers,
        json={"permission": "read", "expires_in_seconds": 300},
    )
    write_response = client.post(
        f"/api/files/{file_id}/shares",
        headers=headers,
        json={"permission": "write", "expires_in_seconds": 300},
    )
    read_share = read_response.get_json()
    write_share = write_response.get_json()

    preview = client.get(read_share["preview_url"])
    preview_page = client.get(read_share["preview_page_url"])
    denied_write = client.put(read_share["content_url"], data="# denied")
    allowed_write = client.put(write_share["content_url"], data="# Updated")
    revoked = client.delete(
        f"/api/files/{file_id}/shares/{read_share['id']}", headers=headers
    )
    after_revoke = client.get(read_share["preview_url"])
    listed = client.get(f"/api/files/{file_id}/shares", headers=headers)

    assert read_response.status_code == 201
    assert write_response.status_code == 201
    assert preview.status_code == 200
    assert preview.get_json()["html"] == "<h1>Initial</h1>"
    assert preview_page.status_code == 200
    assert preview_page.mimetype == "text/html"
    assert b"<script" not in preview_page.data
    assert b"<h1>Initial</h1>" in preview_page.data
    assert preview_page.headers["Content-Security-Policy"].startswith(
        "default-src 'none'"
    )
    assert denied_write.status_code == 403
    assert allowed_write.status_code == 201
    assert allowed_write.get_json()["version"] == 2
    assert revoked.status_code == 204
    assert after_revoke.status_code == 404
    assert all("token" not in item for item in listed.get_json())
    assert all("token_hash" not in item for item in listed.get_json())


def test_markdown_xss_and_invalid_requests_are_safe(file_api) -> None:
    client, agent, _ = file_api
    created = create_file(
        client,
        agent.id,
        name="unsafe",
        format="md",
        content="# Title\n<script>alert(1)</script>\n<img src=x onerror=alert(2)>",
    )
    headers = management_headers(created)
    response = client.get(f"/api/files/{created['id']}/preview", headers=headers)
    preview_html = response.get_json()["html"]

    assert response.status_code == 200
    assert "<script>" not in preview_html
    assert "<img" not in preview_html
    assert "&lt;script&gt;" in preview_html
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert client.post("/api/files", json={}).status_code == 400
    assert client.get("/api/shares/not-a-valid-token/preview").status_code == 404


def test_json_browser_preview_escapes_embedded_html(file_api) -> None:
    client, agent, _ = file_api
    created = create_file(
        client,
        agent.id,
        name="browser-json",
        content={"unsafe": "</pre><script>alert(1)</script>"},
    )

    response = client.get(
        f"/api/files/{created['id']}/preview?view=html",
        headers=management_headers(created),
    )

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"<script" not in response.data
    assert b"&lt;/pre&gt;&lt;script&gt;" in response.data


def test_oversized_request_keeps_flasks_413_response(file_api) -> None:
    client, agent, _ = file_api
    payload = {
        "agent_id": agent.id,
        "name": "too-large",
        "format": "txt",
        "content": "x" * (1024 * 1024),
    }

    response = client.post("/api/files", json=payload)

    assert response.status_code == 413


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent_id": []},
        {"agent_id": True},
        {"execution_id": []},
        {"execution_id": False},
    ],
)
def test_malformed_entity_ids_return_validation_errors(file_api, overrides) -> None:
    client, agent, _ = file_api
    payload = {
        "agent_id": agent.id,
        "name": "invalid-identifiers",
        "format": "txt",
        "content": "content",
        **overrides,
    }

    response = client.post("/api/files", json=payload)

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_file"


def test_malformed_share_recipient_returns_validation_error(file_api) -> None:
    client, agent, _ = file_api
    created = create_file(client, agent.id, name="invalid-recipient")

    response = client.post(
        f"/api/files/{created['id']}/shares",
        headers=management_headers(created),
        json={"recipient_user_id": []},
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_file"


@pytest.mark.parametrize("name", ["line\nbreak", "carriage\rreturn", "tab\tname"])
def test_control_characters_are_rejected_in_download_names(file_api, name) -> None:
    client, agent, _ = file_api

    response = client.post(
        "/api/files",
        json={
            "agent_id": agent.id,
            "name": name,
            "format": "txt",
            "content": "content",
        },
    )

    assert response.status_code == 400


def test_cleanup_endpoints_require_authority_and_default_to_dry_run(file_api) -> None:
    client, agent, _ = file_api
    create_file(client, agent.id, name="cleanup", format="txt", content="one")

    denied = client.post("/api/files/cleanup", json={"dry_run": True})
    dry_run = client.post(
        "/api/files/cleanup",
        headers={"X-Cleanup-Token": "cleanup-secret"},
        json={},
    )
    policy = client.put(
        "/api/files/cleanup-policy",
        headers={"X-Cleanup-Token": "cleanup-secret"},
        json={"enabled": True, "interval_seconds": 60},
    )

    assert denied.status_code == 403
    assert dry_run.status_code == 200
    assert dry_run.get_json()["dry_run"] is True
    assert policy.status_code == 200
    assert policy.get_json()["enabled"] is True
    assert FileShare.query.count() == 0
    assert GeneratedFile.query.count() == 1
