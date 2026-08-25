"""Unit tests for the managed-file catalogue and security boundaries."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backend.app import create_app
from backend.config.settings import TestingConfig
from backend.models.agent import Agent
from backend.models.base import db
from backend.models.execution import Execution
from backend.models.generated_file import FileShare, FileVersion, GeneratedFile
from backend.services.file_service import (
    FileAccessDeniedError,
    FileConflictError,
    FileService,
    FileValidationError,
    ManagedFileNotFoundError,
    PreviewTooLargeError,
)
from backend.services.output_manager import OutputManager


@pytest.fixture
def file_context(tmp_path: Path):
    """Create an isolated database and storage root."""

    class FileTestingConfig(TestingConfig):
        OUTPUT_DIR = str(tmp_path / "outputs")
        FILE_CLEANUP_TOKEN = "cleanup-secret"

    app = create_app(FileTestingConfig)
    with app.app_context():
        db.create_all()
        agent = Agent.create(name="File service agent")
        service = FileService(
            output_manager=OutputManager(
                config_path=tmp_path / "preferences.json", environ={}, cwd=tmp_path
            ),
            output_dir=tmp_path / "outputs",
            cleanup_enabled=False,
            obsolete_ttl_days=1,
            temporary_ttl_hours=1,
            keep_latest_versions=1,
        )
        yield app, service, agent, tmp_path
        db.session.remove()
        db.drop_all()


def test_create_append_and_restore_are_append_only(file_context) -> None:
    _, service, agent, _ = file_context

    generated_file, management_token = service.create_file(
        agent_id=agent.id,
        logical_name="report",
        file_format="json",
        content={"version": 1, "message": "Élodie"},
    )
    first = generated_file.versions[0]
    first_path = service.download_file(generated_file.id, management_token, 1)[0]
    original = first_path.read_bytes()

    second = service.append_version(
        generated_file.id,
        {"version": 2},
        management_token=management_token,
    )
    restored = service.restore_version(generated_file.id, 1, management_token)

    assert [
        item.version
        for item in service.list_versions(generated_file.id, management_token)
    ] == [3, 2, 1]
    assert second.version == 2
    assert restored.version == 3
    assert restored.restored_from_version_id == first.id
    assert first_path.read_bytes() == original
    assert generated_file.current_version == 3
    assert generated_file.management_token_hash == service.hash_token(management_token)
    assert management_token not in str(generated_file.to_dict())
    assert "storage_root" not in generated_file.to_dict()
    assert "relative_path" not in first.to_dict()


def test_share_permissions_expiration_and_revocation(file_context) -> None:
    _, service, agent, _ = file_context
    current_time = datetime(2026, 8, 25, 12, 0, 0)
    service._clock = lambda: current_time
    generated_file, management_token = service.create_file(
        agent_id=agent.id,
        logical_name="notes",
        file_format="md",
        content="# One",
    )

    read_share, read_token = service.create_share(
        generated_file.id,
        management_token,
        permission="read",
        expires_in_seconds=60,
    )
    write_share, write_token = service.create_share(
        generated_file.id,
        management_token,
        permission="write",
        expires_in_seconds=60,
    )

    assert read_share.token_hash == service.hash_token(read_token)
    assert read_token not in str(read_share.to_dict())
    assert service.preview_share(read_token)["format"] == "md"
    with pytest.raises(FileAccessDeniedError, match="read-only"):
        service.append_version(generated_file.id, b"# Two", share_token=read_token)
    assert (
        service.append_version(
            generated_file.id, b"# Two", share_token=write_token
        ).version
        == 2
    )

    service.revoke_share(generated_file.id, read_share.id, management_token)
    with pytest.raises(ManagedFileNotFoundError):
        service.preview_share(read_token)
    current_time += timedelta(seconds=61)
    with pytest.raises(ManagedFileNotFoundError):
        service.preview_share(write_token)
    assert db.session.get(FileShare, write_share.id) is not None


def test_previews_escape_html_and_detect_tampering(file_context) -> None:
    _, service, agent, _ = file_context
    markdown_file, token = service.create_file(
        agent_id=agent.id,
        logical_name="unsafe",
        file_format="md",
        content=(
            "# Safe heading\n"
            "<script>alert(1)</script>\n"
            "<img src=x onerror=alert(2)>"
        ),
    )

    preview = service.preview_file(markdown_file.id, token)

    assert "<h1>Safe heading</h1>" in preview["html"]
    assert "<script>" not in preview["html"]
    assert "<img" not in preview["html"]
    assert "&lt;script&gt;" in preview["html"]

    path, _, version = service.download_file(markdown_file.id, token)
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(FileConflictError, match="integrity"):
        service.preview_file(markdown_file.id, token)

    outside = path.parent.parent.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    version.relative_path = "../outside.txt"
    db.session.commit()
    with pytest.raises(FileConflictError, match="unsafe"):
        service.preview_file(markdown_file.id, token)


def test_preview_size_limit_is_enforced_before_rendering(file_context) -> None:
    _, _, agent, tmp_path = file_context
    service = FileService(
        output_manager=OutputManager(
            config_path=tmp_path / "small-preview.json", environ={}, cwd=tmp_path
        ),
        output_dir=tmp_path / "small-preview-outputs",
        preview_max_bytes=4,
        write_max_bytes=32,
    )
    generated_file, token = service.create_file(
        agent_id=agent.id,
        logical_name="too-large-to-preview",
        file_format="txt",
        content="12345",
    )

    with pytest.raises(PreviewTooLargeError):
        service.preview_file(generated_file.id, token)


def test_preview_does_not_require_storage_write_access(
    file_context, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, service, agent, _ = file_context
    generated_file, token = service.create_file(
        agent_id=agent.id,
        logical_name="read-only-preview",
        file_format="txt",
        content="readable",
    )

    def reject_write_probe(directory: Path) -> None:
        raise AssertionError(f"unexpected write probe for {directory}")

    monkeypatch.setattr(
        service.output_manager, "_validate_writable_directory", reject_write_probe
    )

    assert service.preview_file(generated_file.id, token)["content"] == "readable"


def test_cleanup_is_dry_run_first_and_catalogue_only(file_context) -> None:
    _, service, agent, tmp_path = file_context
    generated_file, management_token = service.create_file(
        agent_id=agent.id,
        logical_name="versions",
        file_format="txt",
        content="one",
    )
    service.append_version(generated_file.id, "two", management_token=management_token)
    service.append_version(
        generated_file.id, "three", management_token=management_token
    )
    old = datetime.utcnow() - timedelta(days=10)
    for version in generated_file.versions:
        version.created_at = old
    db.session.commit()
    foreign = tmp_path / "outputs" / "not-catalogued.tmp"
    foreign.write_text("keep me", encoding="utf-8")

    dry_run = service.cleanup(dry_run=True)

    assert dry_run["candidates"] == 2
    assert dry_run["deleted"] == 0
    assert FileVersion.query.filter_by(generated_file_id=generated_file.id).count() == 3
    assert foreign.read_text(encoding="utf-8") == "keep me"

    report = service.cleanup(dry_run=False)

    assert report["deleted"] == 2
    assert [item.version for item in generated_file.versions] == [3]
    assert foreign.exists()


def test_run_if_due_obeys_policy_and_interval(file_context) -> None:
    _, service, _, _ = file_context
    now = datetime(2026, 8, 25, 12, 0, 0)

    assert service.run_if_due(now) == {"ran": False, "reason": "disabled"}
    policy = service.update_cleanup_policy(
        {"enabled": True, "interval_seconds": 60, "keep_latest_versions": 2}
    )
    assert policy["enabled"] is True
    assert service.run_if_due(now)["ran"] is True
    assert service.run_if_due(now + timedelta(seconds=30)) == {
        "ran": False,
        "reason": "not_due",
    }
    assert service.run_if_due(now + timedelta(seconds=60))["ran"] is True


def test_cleanup_removes_multiple_expired_temporary_file_records(file_context) -> None:
    _, service, agent, _ = file_context
    old = datetime.utcnow() - timedelta(days=2)
    created_ids = []
    for name in ("temporary-one", "temporary-two"):
        generated_file, _ = service.create_file(
            agent_id=agent.id,
            logical_name=name,
            file_format="txt",
            content=name,
            is_temporary=True,
        )
        generated_file.created_at = old
        created_ids.append(generated_file.id)
    db.session.commit()

    report = service.cleanup(dry_run=False)

    assert report["deleted"] == 2
    assert all(
        db.session.get(GeneratedFile, file_id) is None for file_id in created_ids
    )


def test_management_token_is_required(file_context) -> None:
    _, service, agent, _ = file_context
    generated_file, _ = service.create_file(
        agent_id=agent.id,
        logical_name="private",
        file_format="txt",
        content="private",
    )

    with pytest.raises(FileAccessDeniedError):
        service.preview_file(generated_file.id, "wrong-token")


def test_download_stream_is_an_integrity_checked_snapshot(file_context) -> None:
    _, service, agent, _ = file_context
    generated_file, token = service.create_file(
        agent_id=agent.id,
        logical_name="stable-download",
        file_format="txt",
        content="trusted",
    )

    stream, _, version = service.download_file_stream(generated_file.id, token)
    path = service.download_file(generated_file.id, token)[0]
    path.write_text("changed after verification", encoding="utf-8")

    assert stream.getvalue() == b"trusted"
    assert version.sha256 == service.hash_token("trusted")


def test_cleanup_policy_update_is_atomic_and_persists_between_services(
    file_context,
) -> None:
    _, service, _, tmp_path = file_context
    now = datetime(2026, 8, 25, 12, 0, 0)

    with pytest.raises(FileValidationError):
        service.update_cleanup_policy({"enabled": True, "interval_seconds": 0})
    assert service.cleanup_policy()["enabled"] is False

    service.update_cleanup_policy({"enabled": True, "interval_seconds": 60})
    assert service.run_if_due(now)["ran"] is True
    reloaded = FileService(
        output_manager=OutputManager(
            config_path=tmp_path / "reloaded-preferences.json",
            environ={},
            cwd=tmp_path,
        ),
        output_dir=tmp_path / "outputs",
        cleanup_enabled=False,
    )

    assert reloaded.cleanup_policy()["enabled"] is True
    assert reloaded.run_if_due(now + timedelta(seconds=30)) == {
        "ran": False,
        "reason": "not_due",
    }


def test_cleanup_restores_staged_files_when_database_commit_fails(
    file_context, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, service, agent, _ = file_context
    generated_file, _ = service.create_file(
        agent_id=agent.id,
        logical_name="compensated",
        file_format="txt",
        content="keep",
        is_temporary=True,
    )
    generated_file.created_at = datetime.utcnow() - timedelta(days=2)
    db.session.commit()
    # The token is irrelevant to the physical assertion below; retrieve
    # the path through the immutable catalogue helper instead.
    version_path = service._download(generated_file, None)[0]

    def fail_commit() -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.cleanup(dry_run=False)

    assert version_path.exists()
    assert (Path(generated_file.storage_root) / "compensated.txt").exists()
    assert db.session.get(GeneratedFile, generated_file.id) is not None


def test_save_execution_output_upserts_and_publishes_current_copy(
    file_context,
) -> None:
    _, service, agent, tmp_path = file_context
    first_execution = Execution.create(agent_id=agent.id, input_data={"run": 1})
    second_execution = Execution.create(agent_id=agent.id, input_data={"run": 2})

    generated_file, first_token = service.save_execution_output(
        agent_id=agent.id,
        execution_id=first_execution.id,
        logical_name="cli-result.txt",
        file_format="txt",
        content="one",
        output_layout="runs/{agent_id}",
    )
    same_file, second_token = service.save_execution_output(
        agent_id=agent.id,
        execution_id=second_execution.id,
        logical_name="cli-result.txt",
        file_format="txt",
        content="two",
        output_layout="runs/{agent_id}",
    )

    current = tmp_path / "outputs" / "runs" / str(agent.id) / "cli-result.txt"
    assert first_token is not None
    assert second_token is None
    assert same_file.id == generated_file.id
    assert current.read_text(encoding="utf-8") == "two"
    assert [
        item.version
        for item in service.list_versions_trusted(agent.id, "cli-result.txt")
    ] == [2, 1]

    restored = service.restore_version_trusted(agent.id, "cli-result.txt", 1)
    assert restored.version == 3
    assert current.read_text(encoding="utf-8") == "one"
