"""Unit tests for secure output-directory configuration and JSON writes."""

from __future__ import annotations

import json
import os
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
