"""Unit tests for secure output-directory configuration and JSON writes."""

from __future__ import annotations

import json
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from backend.services import output_manager as output_manager_module
from backend.services.output_manager import OutputConfigurationError, OutputManager


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Return an isolated user preference file."""

    return tmp_path / "config" / "preferences.json"


@pytest.fixture
def manager(tmp_path: Path, config_path: Path) -> OutputManager:
    """Create an output manager isolated from the process environment."""

    return OutputManager(config_path=config_path, environ={}, cwd=tmp_path)


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file used by an assertion."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_version_in_process(arguments: tuple[str, int]) -> int:
    """Append one version from an isolated process for lock regression tests."""

    working_directory, number = arguments
    root = Path(working_directory)
    manager = OutputManager(
        config_path=root / "process-preferences.json",
        environ={},
        cwd=root,
    )
    return manager.write_versioned_text(
        "multiprocess.txt",
        f"payload {number}",
        agent_id=10,
        agent_name="Processes",
    ).version


class TestOutputDirectorySelection:
    """Tests for selection priority and directory validation."""

    def test_default_directory_is_created_below_cwd(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        directory = manager.get_output_directory()

        assert directory == (tmp_path / "outputs").resolve()
        assert directory.is_dir()

    def test_output_dir_environment_overrides_default(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        expected = tmp_path / "from-environment"
        configured_manager = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_DIR": str(expected)},
            cwd=tmp_path,
        )

        assert configured_manager.get_output_directory() == expected.resolve()

    def test_relative_environment_directory_is_anchored_to_cwd(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        configured_manager = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_DIR": "relative-results"},
            cwd=tmp_path,
        )

        assert (
            configured_manager.get_output_directory()
            == (tmp_path / "relative-results").resolve()
        )

    def test_persisted_preference_overrides_environment(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        preferred = tmp_path / "preferred"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps({"output_directory": str(preferred)}), encoding="utf-8"
        )
        configured_manager = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_DIR": str(tmp_path / "environment")},
            cwd=tmp_path,
        )

        assert configured_manager.get_output_directory() == preferred.resolve()

    def test_one_shot_override_has_highest_priority(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        preferred = tmp_path / "preferred"
        override = tmp_path / "override"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps({"output_directory": str(preferred)}), encoding="utf-8"
        )
        configured_manager = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_DIR": str(tmp_path / "environment")},
            cwd=tmp_path,
        )

        assert configured_manager.get_output_directory(override) == override.resolve()
        assert configured_manager.get_output_directory() == preferred.resolve()

    def test_existing_file_cannot_be_used_as_directory(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        regular_file = tmp_path / "not-a-directory"
        regular_file.write_text("content", encoding="utf-8")

        with pytest.raises(OutputConfigurationError, match="Cannot create"):
            manager.get_output_directory(regular_file)

    def test_directory_must_be_writable(
        self,
        manager: OutputManager,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def deny_creation(*args: Any, **kwargs: Any) -> tuple[int, str]:
            raise PermissionError("read-only test directory")

        monkeypatch.setattr(output_manager_module.tempfile, "mkstemp", deny_creation)

        with pytest.raises(OutputConfigurationError, match="not writable"):
            manager.get_output_directory(tmp_path / "read-only")

    @pytest.mark.parametrize("value", ["", "   "])
    def test_empty_output_directory_is_invalid(
        self, manager: OutputManager, value: str
    ) -> None:
        with pytest.raises(OutputConfigurationError, match="non-empty path"):
            manager.get_output_directory(value)


class TestOutputPreferencePersistence:
    """Tests for the per-user JSON preference file."""

    def test_set_persists_absolute_path_and_preserves_other_keys(
        self, manager: OutputManager, config_path: Path, tmp_path: Path
    ) -> None:
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps({"theme": "sombre", "profil": "Élodie"}), encoding="utf-8"
        )

        selected = manager.set_output_directory("résultats")

        assert selected == (tmp_path / "résultats").resolve()
        assert read_json(config_path) == {
            "output_directory": str(selected),
            "profil": "Élodie",
            "theme": "sombre",
        }
        assert "Élodie" in config_path.read_text(encoding="utf-8")

    def test_preference_is_loaded_by_a_new_manager(
        self, manager: OutputManager, config_path: Path, tmp_path: Path
    ) -> None:
        selected = manager.set_output_directory(tmp_path / "persistent")

        reloaded = OutputManager(config_path=config_path, environ={}, cwd=tmp_path)

        assert reloaded.get_output_directory() == selected

    def test_reset_removes_only_output_preference_and_returns_environment(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        configured_manager = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_DIR": "environment-results"},
            cwd=tmp_path,
        )
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps(
                {
                    "output_directory": str(tmp_path / "preferred"),
                    "theme": "dark",
                }
            ),
            encoding="utf-8",
        )

        active = configured_manager.reset_output_directory()

        assert active == (tmp_path / "environment-results").resolve()
        assert read_json(config_path) == {"theme": "dark"}

    def test_reset_without_config_uses_default_without_creating_config(
        self, manager: OutputManager, config_path: Path, tmp_path: Path
    ) -> None:
        active = manager.reset_output_directory()

        assert active == (tmp_path / "outputs").resolve()
        assert not config_path.exists()

    def test_environment_can_override_user_config_file(self, tmp_path: Path) -> None:
        environment_config = tmp_path / "env-config" / "settings.json"
        configured_manager = OutputManager(
            environ={"AGENT_WORLD_CONFIG_FILE": str(environment_config)},
            cwd=tmp_path,
        )

        selected = configured_manager.set_output_directory("selected")

        assert environment_config.exists()
        assert read_json(environment_config)["output_directory"] == str(selected)

    def test_explicit_config_path_overrides_environment(self, tmp_path: Path) -> None:
        explicit = tmp_path / "explicit.json"
        environment_config = tmp_path / "environment.json"
        configured_manager = OutputManager(
            config_path=explicit,
            environ={"AGENT_WORLD_CONFIG_FILE": str(environment_config)},
            cwd=tmp_path,
        )

        configured_manager.set_output_directory("selected")

        assert explicit.exists()
        assert not environment_config.exists()

    @pytest.mark.parametrize(
        ("platform", "environment", "expected_parent"),
        [
            ("win32", {"APPDATA": "user-config"}, Path("user-config/Agent World")),
            (
                "darwin",
                {"HOME": "home"},
                Path("home/Library/Application Support/Agent World"),
            ),
            (
                "linux",
                {"XDG_CONFIG_HOME": "xdg-config"},
                Path("xdg-config/agent-world"),
            ),
        ],
    )
    def test_default_config_path_follows_platform_conventions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        environment: dict[str, str],
        expected_parent: Path,
    ) -> None:
        monkeypatch.setattr(output_manager_module.sys, "platform", platform)
        configured_manager = OutputManager(environ=environment, cwd=tmp_path)

        configured_manager.set_output_directory("selected")

        expected = (tmp_path / expected_parent / "config.json").resolve()
        assert expected.exists()

    @pytest.mark.parametrize(
        "content",
        ["{not valid json", "[]", '"text"', "42", "null"],
    )
    def test_corrupt_or_non_object_config_is_rejected(
        self,
        manager: OutputManager,
        config_path: Path,
        content: str,
    ) -> None:
        config_path.parent.mkdir(parents=True)
        config_path.write_text(content, encoding="utf-8")

        with pytest.raises(OutputConfigurationError, match="[Cc]onfiguration"):
            manager.get_output_directory()

    @pytest.mark.parametrize("preference", [None, 12, [], {}, ""])
    def test_invalid_persisted_directory_is_rejected(
        self,
        manager: OutputManager,
        config_path: Path,
        preference: Any,
    ) -> None:
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps({"output_directory": preference}), encoding="utf-8"
        )

        with pytest.raises(OutputConfigurationError, match="non-empty string"):
            manager.get_output_directory()

    def test_set_refuses_to_overwrite_corrupt_config(
        self, manager: OutputManager, config_path: Path, tmp_path: Path
    ) -> None:
        corrupt_content = "{broken"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(corrupt_content, encoding="utf-8")

        with pytest.raises(OutputConfigurationError):
            manager.set_output_directory(tmp_path / "new-output")

        assert config_path.read_text(encoding="utf-8") == corrupt_content
        assert not (tmp_path / "new-output").exists()


class TestSafeOutputPaths:
    """Tests for traversal and symlink confinement."""

    @pytest.mark.parametrize(
        "filename",
        ["../escape.json", "nested/../escape.json", r"..\escape.json"],
    )
    def test_path_traversal_is_rejected(
        self, manager: OutputManager, filename: str
    ) -> None:
        with pytest.raises(OutputConfigurationError, match="traversal"):
            manager.resolve_output_path(filename)

    @pytest.mark.parametrize("filename", ["/escape.json", r"C:\escape.json"])
    def test_absolute_paths_are_rejected(
        self, manager: OutputManager, filename: str
    ) -> None:
        with pytest.raises(OutputConfigurationError, match="Absolute"):
            manager.resolve_output_path(filename)

    @pytest.mark.parametrize(
        "filename",
        [
            ".versions./report.txt",
            "folder./report.txt",
            "folder /report.txt",
            "report.txt:stream",
            "CON",
            "aux.txt",
            "nested/LPT9.json",
        ],
    )
    def test_windows_aliases_and_reserved_names_are_rejected_portably(
        self, manager: OutputManager, filename: str
    ) -> None:
        with pytest.raises(OutputConfigurationError):
            manager.resolve_output_path(filename)

    def test_version_lock_uses_a_canonical_path_key(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        first = tmp_path / "outputs" / "nested" / ".." / "same.txt"
        second = tmp_path / "outputs" / "same.txt"

        assert manager._version_lock(first) is manager._version_lock(second)

    def test_symlink_cannot_escape_output_directory(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        output_directory = manager.get_output_directory()
        outside = tmp_path / "outside"
        outside.mkdir()
        link = output_directory / "redirect"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            pytest.skip(f"Symlinks are unavailable: {exc}")

        with pytest.raises(OutputConfigurationError, match="escapes"):
            manager.resolve_output_path("redirect/escaped.json")
        assert not (outside / "escaped.json").exists()

    def test_existing_directory_is_not_accepted_as_output_file(
        self, manager: OutputManager
    ) -> None:
        output_directory = manager.get_output_directory()
        (output_directory / "folder").mkdir()

        with pytest.raises(OutputConfigurationError, match="regular file"):
            manager.resolve_output_path("folder")


class TestJsonWriting:
    """Tests for UTF-8 and atomic JSON output."""

    def test_write_json_supports_unicode_and_nested_directories(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        data = {"message": "Bonjour Élodie 👋", "ville": "Orléans"}

        output_path = manager.write_json("nested/résultat.json", data)

        assert output_path == (tmp_path / "outputs/nested/résultat.json").resolve()
        assert read_json(output_path) == data
        assert "Élodie 👋" in output_path.read_text(encoding="utf-8")

    def test_one_shot_output_directory_is_supported(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        custom_directory = tmp_path / "custom"

        output_path = manager.write_json(
            "payload.json", {"ok": True}, output_dir=custom_directory
        )

        assert output_path == custom_directory / "payload.json"
        assert read_json(output_path) == {"ok": True}

    def test_write_uses_atomic_replace(
        self,
        manager: OutputManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        replacements: list[tuple[Path, Path]] = []
        original_replace = output_manager_module.os.replace

        def record_replace(source: os.PathLike[str], target: os.PathLike[str]) -> None:
            replacements.append((Path(source), Path(target)))
            original_replace(source, target)

        monkeypatch.setattr(output_manager_module.os, "replace", record_replace)

        output_path = manager.write_json("atomic.json", {"value": 1})

        assert replacements[-1][1] == output_path
        assert replacements[-1][0].suffix == ".tmp"
        assert not replacements[-1][0].exists()

    def test_failed_serialization_preserves_existing_file(
        self, manager: OutputManager
    ) -> None:
        output_path = manager.write_json("stable.json", {"version": 1})
        original_content = output_path.read_bytes()

        with pytest.raises(OutputConfigurationError, match="Cannot write output file"):
            manager.write_json("stable.json", {"not_json": {1, 2, 3}})

        assert output_path.read_bytes() == original_content
        assert not list(output_path.parent.glob(f".{output_path.name}.*.tmp"))


class TestAgentOutputLayout:
    """Tests for configurable and confined per-agent directories."""

    def test_default_layout_is_created_with_a_sanitized_agent_name(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        directory = manager.get_agent_output_directory(7, "../../Résumé Agent")

        assert directory == (tmp_path / "outputs/agents/7/outputs").resolve()
        assert directory.is_dir()

    def test_default_layout_is_stable_when_an_agent_is_renamed(
        self, manager: OutputManager
    ) -> None:
        before = manager.get_agent_output_directory(7, "Original name")
        after = manager.get_agent_output_directory(7, "Renamed agent")

        assert after == before

    def test_custom_layout_is_persisted_and_reset(
        self, manager: OutputManager, config_path: Path
    ) -> None:
        selected = "generated/{agent_name}/{agent_id}"

        assert manager.set_output_layout(selected) == selected
        assert manager.get_output_layout() == selected
        assert read_json(config_path)["output_layout"] == selected

        assert manager.reset_output_layout() == manager.DEFAULT_OUTPUT_LAYOUT
        assert "output_layout" not in read_json(config_path)

    def test_environment_layout_is_used_as_fallback(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        configured = OutputManager(
            config_path=config_path,
            environ={"OUTPUT_LAYOUT": "runs/{agent_id}/{agent_name}"},
            cwd=tmp_path,
        )

        assert configured.get_output_layout() == "runs/{agent_id}/{agent_name}"

    @pytest.mark.parametrize(
        "layout",
        [
            "../outside",
            "/absolute/{agent_id}",
            r"C:\absolute\{agent_id}",
            "agents/{unknown}",
            "shared",
            "agents/{agent_name}/outputs",
            "agents/{agent_name.__class__}",
            "agents/{agent_id!r}",
            "agents/{agent_id:04d}",
            "agents/.versions/{agent_id}",
        ],
    )
    def test_unsafe_or_unsupported_layouts_are_rejected(
        self, manager: OutputManager, layout: str
    ) -> None:
        with pytest.raises(OutputConfigurationError):
            manager.set_output_layout(layout)

    def test_layout_symlink_cannot_escape_output_root(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        root = manager.get_output_directory()
        outside = tmp_path / "outside-layout"
        outside.mkdir()
        link = root / "agents"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            pytest.skip(f"Symlinks are unavailable: {exc}")

        with pytest.raises(OutputConfigurationError, match="Cannot create agent"):
            manager.get_agent_output_directory(1, "Agent")

    def test_agent_context_rejects_traversal(self, manager: OutputManager) -> None:
        with pytest.raises(OutputConfigurationError, match="traversal"):
            manager.resolve_output_path(
                "../escape.json",
                agent_id=1,
                agent_name="Agent",
            )


class TestAtomicTextAndByteWriting:
    """Tests for the generic atomic output primitives."""

    def test_text_and_bytes_are_written_atomically(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        text_path = manager.write_text("notes/résumé.md", "Bonjour 👋\n")
        bytes_path = manager.write_bytes("payload.bin", b"\x00\x01")

        assert text_path == (tmp_path / "outputs/notes/résumé.md").resolve()
        assert text_path.read_text(encoding="utf-8") == "Bonjour 👋\n"
        assert bytes_path.read_bytes() == b"\x00\x01"

    def test_invalid_primitive_payload_types_are_rejected(
        self, manager: OutputManager
    ) -> None:
        with pytest.raises(OutputConfigurationError, match="string"):
            manager.write_text("result.txt", b"text")  # type: ignore[arg-type]
        with pytest.raises(OutputConfigurationError, match="bytes-like"):
            manager.write_bytes("result.txt", "text")  # type: ignore[arg-type]


class TestOutputVersioning:
    """Tests for append-only histories and non-destructive restoration."""

    def test_successive_writes_create_immutable_versions(
        self, manager: OutputManager
    ) -> None:
        first = manager.write_versioned_text(
            "report.txt", "version one", agent_id=3, agent_name="Writer"
        )
        second = manager.write_versioned_text(
            "report.txt", "version two", agent_id=3, agent_name="Writer"
        )

        assert first.version == 1
        assert second.version == 2
        assert first.snapshot_path.read_text(encoding="utf-8") == "version one"
        assert second.snapshot_path.read_text(encoding="utf-8") == "version two"
        assert second.path.read_text(encoding="utf-8") == "version two"
        assert [
            item.version
            for item in manager.list_versions(
                "report.txt", agent_id=3, agent_name="Writer"
            )
        ] == [1, 2]

    def test_serialized_version_metadata_does_not_expose_local_paths(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        version = manager.write_versioned_text(
            "private.txt", "content", agent_id=3, agent_name="Writer"
        )

        serialized = version.to_dict()

        assert "path" not in serialized
        assert "snapshot_path" not in serialized
        assert str(tmp_path) not in json.dumps(serialized)
        assert serialized["version"] == 1
        assert serialized["restored_from"] is None

    def test_existing_unversioned_file_is_imported_before_overwrite(
        self, manager: OutputManager
    ) -> None:
        manager.write_text(
            "legacy.txt",
            "legacy content",
            agent_id=4,
            agent_name="Legacy",
        )

        created = manager.write_versioned_text(
            "legacy.txt", "new content", agent_id=4, agent_name="Legacy"
        )
        history = manager.list_versions("legacy.txt", agent_id=4, agent_name="Legacy")

        assert created.version == 2
        assert history[0].snapshot_path.read_text(encoding="utf-8") == "legacy content"
        assert history[1].snapshot_path.read_text(encoding="utf-8") == "new content"

    def test_restore_creates_a_new_auditable_version(
        self, manager: OutputManager
    ) -> None:
        manager.write_versioned_json(
            "result.json", {"value": 1}, agent_id=5, agent_name="Restorer"
        )
        manager.write_versioned_json(
            "result.json", {"value": 2}, agent_id=5, agent_name="Restorer"
        )

        restored = manager.restore_version(
            "result.json", 1, agent_id=5, agent_name="Restorer"
        )
        history = manager.list_versions(
            "result.json", agent_id=5, agent_name="Restorer"
        )

        assert restored.version == 3
        assert restored.restored_from == 1
        assert read_json(restored.path) == {"value": 1}
        assert [item.version for item in history] == [1, 2, 3]
        assert history[-1].restored_from == 1

    def test_missing_version_is_rejected_without_changing_current_file(
        self, manager: OutputManager
    ) -> None:
        current = manager.write_versioned_text(
            "stable.txt", "stable", agent_id=6, agent_name="Stable"
        )

        with pytest.raises(OutputConfigurationError, match="does not exist"):
            manager.restore_version("stable.txt", 99, agent_id=6, agent_name="Stable")

        assert current.path.read_text(encoding="utf-8") == "stable"
        assert (
            len(manager.list_versions("stable.txt", agent_id=6, agent_name="Stable"))
            == 1
        )

    def test_tampered_snapshot_fails_integrity_validation(
        self, manager: OutputManager
    ) -> None:
        version = manager.write_versioned_text(
            "secure.txt", "trusted", agent_id=8, agent_name="Secure"
        )
        version.snapshot_path.write_text("tampered", encoding="utf-8")

        with pytest.raises(OutputConfigurationError, match="integrity"):
            manager.list_versions("secure.txt", agent_id=8, agent_name="Secure")

    def test_concurrent_writes_receive_unique_versions(
        self, manager: OutputManager
    ) -> None:
        def write(number: int) -> int:
            return manager.write_versioned_text(
                "parallel.txt",
                f"payload {number}",
                agent_id=9,
                agent_name="Parallel",
            ).version

        with ThreadPoolExecutor(max_workers=4) as executor:
            allocated = list(executor.map(write, range(8)))

        assert sorted(allocated) == list(range(1, 9))
        history = manager.list_versions(
            "parallel.txt", agent_id=9, agent_name="Parallel"
        )
        assert [item.version for item in history] == list(range(1, 9))

    def test_writes_from_separate_processes_receive_unique_versions(
        self, manager: OutputManager, tmp_path: Path
    ) -> None:
        context = multiprocessing.get_context("spawn")
        arguments = [(str(tmp_path), number) for number in range(6)]

        with ProcessPoolExecutor(max_workers=3, mp_context=context) as executor:
            allocated = list(executor.map(write_version_in_process, arguments))

        assert sorted(allocated) == list(range(1, 7))
        history = manager.list_versions(
            "multiprocess.txt", agent_id=10, agent_name="Processes"
        )
        assert [item.version for item in history] == list(range(1, 7))

    def test_legacy_incomplete_version_directory_is_recovered(
        self, manager: OutputManager
    ) -> None:
        directory = manager.get_agent_output_directory(11, "Recovery")
        target = manager.resolve_output_path(
            "recover.txt", agent_id=11, agent_name="Recovery"
        )
        incomplete = target.parent / ".versions" / target.name / "v000001"
        incomplete.mkdir(parents=True)
        (incomplete / "content.txt").write_text("partial", encoding="utf-8")

        created = manager.write_versioned_text(
            "recover.txt", "complete", agent_id=11, agent_name="Recovery"
        )

        assert created.version == 1
        assert created.snapshot_path.read_text(encoding="utf-8") == "complete"
        assert directory in created.snapshot_path.parents

    def test_complete_pending_snapshot_is_published_during_recovery(
        self, manager: OutputManager
    ) -> None:
        directory = manager.get_agent_output_directory(12, "Recovery")
        target = manager.resolve_output_path(
            "pending.txt", agent_id=12, agent_name="Recovery"
        )
        staged = manager._stage_version_snapshot(
            target,
            directory,
            b"committed before crash",
            1,
        )
        manager._write_bytes_atomically(
            target,
            b"committed before crash",
            "simulated interrupted output",
        )

        history = manager.list_versions(
            "pending.txt", agent_id=12, agent_name="Recovery"
        )

        assert [item.version for item in history] == [1]
        assert history[0].snapshot_path.read_bytes() == b"committed before crash"
        assert not staged.staging_directory.exists()
        assert staged.final_directory.is_dir()

    def test_failed_snapshot_build_never_exposes_a_version_directory(
        self,
        manager: OutputManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        original_writer = OutputManager._write_json_atomically.__func__

        def fail_metadata(
            cls: type[OutputManager],
            path: Path,
            data: Any,
            description: str,
        ) -> None:
            if description == "version metadata":
                raise OutputConfigurationError("simulated metadata failure")
            original_writer(cls, path, data, description)

        monkeypatch.setattr(
            OutputManager,
            "_write_json_atomically",
            classmethod(fail_metadata),
        )

        with pytest.raises(OutputConfigurationError, match="metadata failure"):
            manager.write_versioned_text(
                "atomic-history.txt",
                "content",
                agent_id=13,
                agent_name="Atomic",
            )

        directory = manager.get_agent_output_directory(13, "Atomic")
        root = directory / ".versions" / "atomic-history.txt"
        assert not list(root.glob("v[0-9]*"))
        assert not list(root.glob("*.pending"))
