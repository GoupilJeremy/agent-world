"""Tests for the CLI output-directory integration."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import pytest

from backend.cli.main import AgentWorldCLI, create_parser
from backend.services.agent_service import AgentService
from backend.services.output_manager import OutputManager


class FakeAgentService:
    """Small test double that records executions without touching the database."""

    def __init__(self, failure: Optional[Exception] = None) -> None:
        self.failure = failure
        self.calls: List[Dict[str, Any]] = []

    def run_agent(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.calls.append(
            {"agent_id": agent_id, "input_data": input_data, "model": model}
        )
        if self.failure is not None:
            raise self.failure
        return {
            "execution_id": 42,
            "agent_id": agent_id,
            "status": "completed",
            "output": {"answer": "done"},
            "duration_ms": 7,
        }


def make_cli(
    tmp_path: Path, failure: Optional[Exception] = None
) -> tuple[AgentWorldCLI, FakeAgentService, OutputManager]:
    """Build an isolated CLI with a real output manager and fake agent service."""

    output_manager = OutputManager(
        config_path=tmp_path / "config.json",
        environ={},
        cwd=tmp_path,
    )
    agent_service = FakeAgentService(failure=failure)
    cli = AgentWorldCLI(
        agent_service=cast(AgentService, agent_service),
        output_manager=output_manager,
    )
    return cli, agent_service, output_manager


def test_parser_accepts_output_configuration_and_run_override() -> None:
    """The parser exposes the persistent and one-shot output options."""

    parser = create_parser()

    display_args = parser.parse_args(["config", "output-dir"])
    set_args = parser.parse_args(["config", "output-dir", "generated"])
    reset_args = parser.parse_args(["config", "output-dir", "--reset"])
    run_args = parser.parse_args(
        [
            "run",
            "3",
            "--input",
            "hello",
            "--output",
            "result.json",
            "--output-dir",
            "temporary",
        ]
    )

    assert display_args.path is None
    assert display_args.reset is False
    assert set_args.path == "generated"
    assert reset_args.reset is True
    assert run_args.output_dir == "temporary"

    with pytest.raises(SystemExit):
        parser.parse_args(["config", "output-dir", "generated", "--reset"])


def test_importing_cli_does_not_initialize_flask_application() -> None:
    """Loading a filesystem-only CLI must not connect to the application DB."""

    repository_root = Path(__file__).resolve().parents[2]
    script = (
        "import sys; import backend.cli.main; "
        "assert 'backend.app' not in sys.modules"
    )

    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )

    assert completed.returncode == 0, completed.stderr


def test_backend_factory_remains_available_after_lazy_import() -> None:
    """The public backend factory keeps its original import contract."""

    from backend import create_app
    from backend.config.settings import TestingConfig

    app = create_app(TestingConfig)

    assert app.config["TESTING"] is True


def test_config_output_directory_is_displayed_persisted_and_reset(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Configuration changes survive manager instances and can be reset."""

    cli, _, output_manager = make_cli(tmp_path)
    custom_directory = tmp_path / "custom-output"
    default_directory = output_manager.get_output_directory()

    assert cli.run(["config", "output-dir", str(custom_directory)]) == 0
    assert custom_directory.resolve() == output_manager.get_output_directory()

    reloaded_manager = OutputManager(
        config_path=tmp_path / "config.json",
        environ={},
        cwd=tmp_path,
    )
    assert reloaded_manager.get_output_directory() == custom_directory.resolve()

    assert cli.run(["config", "output-dir"]) == 0
    assert str(custom_directory.resolve()) in capsys.readouterr().out

    assert cli.run(["config", "output-dir", "--reset"]) == 0
    assert output_manager.get_output_directory() == default_directory


def test_config_command_does_not_enter_flask_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filesystem-only configuration remains independent from database setup."""

    from backend.app import app

    def fail_if_context_is_requested() -> None:
        raise AssertionError("config command must not request a Flask context")

    output_manager = OutputManager(
        config_path=tmp_path / "config.json",
        environ={},
        cwd=tmp_path,
    )
    cli = AgentWorldCLI(output_manager=output_manager)
    monkeypatch.setattr(app, "app_context", fail_if_context_is_requested)

    assert cli.run(["config", "output-dir", str(tmp_path / "configured")]) == 0


def test_run_output_directory_override_is_not_persisted(tmp_path: Path) -> None:
    """A run-level override receives the JSON file without changing preference."""

    cli, agent_service, output_manager = make_cli(tmp_path)
    persistent_directory = tmp_path / "persistent"
    override_directory = tmp_path / "one-shot"
    output_manager.set_output_directory(persistent_directory)

    return_code = cli.run(
        [
            "run",
            "9",
            "--input",
            "hello",
            "--output",
            "result.json",
            "--output-dir",
            str(override_directory),
        ]
    )

    assert return_code == 0
    assert len(agent_service.calls) == 1
    assert output_manager.get_output_directory() == persistent_directory.resolve()
    assert not (persistent_directory / "result.json").exists()
    result_path = override_directory / "result.json"
    assert result_path.is_file()
    assert json.loads(result_path.read_text(encoding="utf-8"))["execution_id"] == 42


def test_traversal_is_rejected_before_agent_execution(tmp_path: Path) -> None:
    """An unsafe target fails before the potentially expensive agent run."""

    cli, agent_service, _ = make_cli(tmp_path)

    return_code = cli.run(
        [
            "run",
            "4",
            "--input",
            "hello",
            "--output",
            "../escape.json",
            "--output-dir",
            str(tmp_path / "safe"),
        ]
    )

    assert return_code == 1
    assert agent_service.calls == []
    assert not (tmp_path / "escape.json").exists()


def test_failed_agent_run_does_not_create_output_file(tmp_path: Path) -> None:
    """A validated target is only written after a successful execution."""

    cli, agent_service, _ = make_cli(tmp_path, failure=ValueError("run failed"))
    output_directory = tmp_path / "failed-run"

    return_code = cli.run(
        [
            "run",
            "4",
            "--input",
            "hello",
            "--output",
            "result.json",
            "--output-dir",
            str(output_directory),
        ]
    )

    assert return_code == 1
    assert len(agent_service.calls) == 1
    assert not (output_directory / "result.json").exists()
