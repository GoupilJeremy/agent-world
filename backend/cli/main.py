# 💻 Agent World - CLI Main
# Version: 0.1.0 (MVP)
# Description: Point d'entrée principal de la CLI

"""
Command Line Interface for Agent World.

Ce module contient le point d'entrée principal de la CLI et la configuration
des commandes disponibles.

Usage:
    agent create --name my_agent --model mistral-tiny
    agent list
    agent show 1
    agent run 1 --input "Hello, world!"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..config.settings import Config
from ..models.agent import Agent
from ..services.agent_service import AgentService
from ..services.file_naming import generate_filename, normalize_extension
from ..services.output_manager import OutputConfigurationError, OutputManager
from .collaboration import CollaborationCLIHandler
from .templates import TemplateCLIHandler, add_template_commands


class CLIFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter for better CLI help display."""

    pass


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Agent World - Command Line Interface",
        formatter_class=CLIFormatter,
        epilog="""
Examples:
  agent create --name my_agent --model mistral-tiny    Create a new agent
  agent list                                             List all agents
  agent show 1                                           Show agent details
  agent update 1 --name new_name                        Update an agent
  agent delete 1                                        Delete an agent
  agent run 1 --input "Hello!"                         Run an agent
        """,
    )

    # Global arguments
    parser.add_argument(
        "--version", "-v", action="version", version="Agent World CLI v0.1.0"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "table", "yaml"],
        default="table",
        help="Output format (default: table)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Add template commands
    add_template_commands(subparsers)

    # Add collaboration commands
    collaboration_handler = CollaborationCLIHandler()
    collaboration_handler.add_commands(subparsers)

    # Create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new agent",
        description="Create a new AI agent with the specified configuration",
    )
    create_parser.add_argument(
        "--name", "-n", required=True, help="Name of the agent (required)"
    )
    create_parser.add_argument(
        "--model",
        "-m",
        default="mistral-tiny",
        help="AI model to use (default: mistral-tiny)",
    )
    create_parser.add_argument("--description", "-d", help="Description of the agent")
    create_parser.add_argument(
        "--config",
        "-c",
        type=json.loads,
        default={},
        help="JSON configuration for the agent",
    )
    create_parser.add_argument(
        "--active",
        "-a",
        type=bool,
        default=True,
        help="Whether the agent is active (default: True)",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list", help="List all agents", description="List all AI agents in the database"
    )
    list_parser.add_argument(
        "--all", action="store_true", help="Show all agents including inactive ones"
    )
    list_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=10,
        help="Maximum number of agents to show (default: 10)",
    )
    list_parser.add_argument(
        "--search", "-s", help="Search agents by name or description"
    )

    # Show command
    show_parser = subparsers.add_parser(
        "show",
        help="Show agent details",
        description="Show detailed information about a specific agent",
    )
    show_parser.add_argument("id", type=int, help="ID of the agent to show")
    show_parser.add_argument(
        "--executions", "-e", action="store_true", help="Show agent executions"
    )
    show_parser.add_argument(
        "--stats", action="store_true", help="Show agent statistics"
    )

    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update an agent",
        description="Update the configuration of an existing agent",
    )
    update_parser.add_argument("id", type=int, help="ID of the agent to update")
    update_parser.add_argument("--name", "-n", help="New name for the agent")
    update_parser.add_argument("--model", "-m", help="New AI model for the agent")
    update_parser.add_argument(
        "--description", "-d", help="New description for the agent"
    )
    update_parser.add_argument(
        "--config", "-c", type=json.loads, help="New JSON configuration for the agent"
    )
    update_parser.add_argument(
        "--active", "-a", type=bool, help="Whether the agent should be active"
    )

    # Delete command
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete an agent",
        description="Delete an existing agent from the database",
    )
    delete_parser.add_argument("id", type=int, help="ID of the agent to delete")
    delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Force deletion without confirmation"
    )

    # Run command
    run_parser = subparsers.add_parser(
        "run", help="Run an agent", description="Execute an agent with the given input"
    )
    run_parser.add_argument("id", type=int, help="ID of the agent to run")
    run_parser.add_argument(
        "--input", "-i", required=True, help="Input text for the agent (required)"
    )
    run_parser.add_argument("--model", "-m", help="Override the agent model")
    run_parser.add_argument("--output", "-o", help="Output file to save the result")
    run_parser.add_argument(
        "--save",
        action="store_true",
        help="Save the result using an intelligent filename",
    )
    run_parser.add_argument(
        "--output-format",
        choices=["json", "md", "txt"],
        help="Saved file format (inferred from --output or defaults to json)",
    )
    run_parser.add_argument(
        "--name-prefix",
        help="Prefix for an automatically generated filename",
    )
    run_parser.add_argument(
        "--name-suffix",
        help="Suffix for an automatically generated filename",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Override the output directory for this execution",
    )
    run_parser.add_argument(
        "--output-layout",
        help="Override the automatic agent-directory layout for this execution",
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage Agent World configuration",
        description="View or update Agent World configuration",
    )
    config_subparsers = config_parser.add_subparsers(
        title="configuration",
        dest="config_command",
        required=True,
    )
    output_dir_parser = config_subparsers.add_parser(
        "output-dir",
        help="View or update the output directory",
    )
    output_dir_group = output_dir_parser.add_mutually_exclusive_group()
    output_dir_group.add_argument(
        "path",
        nargs="?",
        help="Directory to use for generated files",
    )
    output_dir_group.add_argument(
        "--reset",
        action="store_true",
        help="Restore the default output directory",
    )

    output_layout_parser = config_subparsers.add_parser(
        "output-layout",
        help="View or update the automatic agent-directory layout",
    )
    output_layout_group = output_layout_parser.add_mutually_exclusive_group()
    output_layout_group.add_argument(
        "layout",
        nargs="?",
        help="Layout using the {agent_id} and {agent_name} placeholders",
    )
    output_layout_group.add_argument(
        "--reset",
        action="store_true",
        help="Restore the default output layout",
    )

    files_parser = subparsers.add_parser(
        "files",
        help="Inspect or restore generated-file versions",
    )
    files_subparsers = files_parser.add_subparsers(
        title="files",
        dest="files_command",
        required=True,
    )
    versions_parser = files_subparsers.add_parser(
        "versions", help="List versions of a generated file"
    )
    versions_parser.add_argument("id", type=int, help="ID of the owning agent")
    versions_parser.add_argument("filename", help="Generated filename")
    versions_parser.add_argument("--output-dir", help="Output root override")
    versions_parser.add_argument("--output-layout", help="Output layout override")

    restore_parser = files_subparsers.add_parser(
        "restore", help="Restore a version as a new current version"
    )
    restore_parser.add_argument("id", type=int, help="ID of the owning agent")
    restore_parser.add_argument("filename", help="Generated filename")
    restore_parser.add_argument("version", type=int, help="Version number to restore")
    restore_parser.add_argument("--output-dir", help="Output root override")
    restore_parser.add_argument("--output-layout", help="Output layout override")

    return parser


class AgentWorldCLI:
    """Main CLI class for Agent World."""

    def __init__(
        self,
        agent_service: Optional[AgentService] = None,
        output_manager: Optional[OutputManager] = None,
    ) -> None:
        """Initialize the CLI."""
        self.parser = create_parser()
        self._agent_service_injected = agent_service is not None
        self.agent_service = (
            agent_service if agent_service is not None else AgentService()
        )
        self.output_manager = (
            output_manager
            if output_manager is not None
            else OutputManager(environ={**os.environ, "OUTPUT_DIR": Config.OUTPUT_DIR})
        )
        self.verbose = False
        self.format = "table"
        self.template_handler = TemplateCLIHandler()
        self.collaboration_handler = CollaborationCLIHandler()

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with the given arguments.

        Args:
            args: List of command line arguments (default: sys.argv[1:])
        """
        args = sys.argv[1:] if args is None else args
        parsed_args = self.parser.parse_args(args)

        # Set global options
        self.verbose = parsed_args.verbose
        self.format = parsed_args.format

        # Route to the appropriate command handler
        command = parsed_args.command

        # Handle collaboration commands
        if command in [
            "invite",
            "invitations",
            "accept-invite",
            "revoke-invite",
            "create-project",
            "list-projects",
        ]:
            self.collaboration_handler.verbose = self.verbose
            self.collaboration_handler.format = self.format
            if hasattr(parsed_args, "handler"):
                return parsed_args.handler(parsed_args)
            else:
                print(f"❌ Unknown collaboration command: {command}")
                return 1

        # Handle template subcommands
        if command == "template":
            self.template_handler.verbose = self.verbose
            self.template_handler.format = self.format
            template_command = parsed_args.template_command
            template_handler_name = f"handle_template_{template_command}"

            if hasattr(self.template_handler, template_handler_name):
                handler: Callable[[argparse.Namespace], int] = getattr(
                    self.template_handler, template_handler_name
                )
                return handler(parsed_args)
            else:
                # Check for nested commands (versions)
                if hasattr(parsed_args, "versions_command"):
                    versions_handler_name = (
                        f"handle_template_versions_{parsed_args.versions_command}"
                    )
                    if hasattr(self.template_handler, versions_handler_name):
                        handler = getattr(self.template_handler, versions_handler_name)
                        return handler(parsed_args)

                print(f"❌ Unknown template command: {template_command}")
                return 1

        handler_name = f"handle_{command}"

        if not hasattr(self, handler_name):
            print(f"❌ Unknown command: {command}")
            self.parser.print_help()
            return 1

        handler: Callable[[argparse.Namespace], int] = getattr(self, handler_name)
        if command == "config" or self._agent_service_injected:
            return handler(parsed_args)

        from flask import has_app_context

        if has_app_context():
            return handler(parsed_args)

        from ..app import app

        with app.app_context():
            return handler(parsed_args)

    def handle_config(self, args: argparse.Namespace) -> int:
        """Handle configuration commands."""
        try:
            if args.config_command == "output-dir":
                if args.reset:
                    value: Any = self.output_manager.reset_output_directory()
                elif args.path is not None:
                    value = self.output_manager.set_output_directory(args.path)
                else:
                    value = self.output_manager.get_output_directory()
                print(f"Output directory: {value}")
            elif args.config_command == "output-layout":
                if args.reset:
                    value = self.output_manager.reset_output_layout()
                elif args.layout is not None:
                    value = self.output_manager.set_output_layout(args.layout)
                else:
                    value = self.output_manager.get_output_layout()
                print(f"Output layout: {value}")
            else:
                print(f"Unknown configuration command: {args.config_command}")
                return 1
            return 0
        except OutputConfigurationError as error:
            print(f"Error: {error}")
            return 1

    def handle_create(self, args) -> int:
        """Handle the create command."""
        try:
            config = args.config or {}

            if self.verbose:
                print(f"🔧 Creating agent: {args.name}")
                print(f"   Model: {args.model}")
                print(f"   Description: {args.description}")
                print(f"   Configuration: {json.dumps(config, indent=2)}")

            agent = self.agent_service.create_agent(
                name=args.name,
                model=args.model,
                description=args.description,
                configuration=config,
                is_active=args.active,
            )

            if self.verbose:
                print(f"✅ Agent created with ID: {agent.id}")

            self.print_agent(agent)
            return 0

        except ValueError as e:
            print(f"❌ Error: {str(e)}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Unexpected error: {str(e)}")
            return 1

    def handle_list(self, args) -> int:
        """Handle the list command."""
        try:
            if args.search:
                agents = self.agent_service.search_agents(args.search, args.limit)
            elif args.all:
                agents = [
                    a.to_dict()
                    for a in self.agent_service.get_all_agents(only_active=False)
                ]
            else:
                agents = [
                    a.to_dict()
                    for a in self.agent_service.get_all_agents(only_active=True)
                ]

            if not agents:
                print("🔍 No agents found")
                return 0

            if self.format == "json":
                print(json.dumps(agents, indent=2))
            else:
                self.print_table(agents)

            return 0

        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Error listing agents: {str(e)}")
            return 1

    def handle_show(self, args) -> int:
        """Handle the show command."""
        try:
            agent = self.agent_service.get_agent(args.id)

            if not agent:
                print(f"❌ Agent with ID {args.id} not found")
                return 1

            if args.stats:
                stats = self.agent_service.get_agent_statistics(args.id)
                self.print_dict(stats, title=f"📊 Statistics for Agent {agent.name}")
            elif args.executions:
                executions = self.agent_service.get_agent_executions(args.id, limit=10)
                if executions:
                    self.print_table(
                        executions, title=f"📋 Executions for Agent {agent.name}"
                    )
                else:
                    print(f"🔍 No executions found for agent {agent.name}")
            else:
                self.print_agent(agent)

            return 0

        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Error showing agent: {str(e)}")
            return 1

    def handle_update(self, args) -> int:
        """Handle the update command."""
        try:
            update_data = {}

            if args.name:
                update_data["name"] = args.name
            if args.model:
                update_data["model"] = args.model
            if args.description:
                update_data["description"] = args.description
            if args.config:
                update_data["configuration"] = args.config
            if args.active is not None:
                update_data["is_active"] = args.active

            if not update_data:
                print("⚠️  No fields to update")
                return 0

            if self.verbose:
                print(f"🔧 Updating agent {args.id}")
                for key, value in update_data.items():
                    print(f"   {key}: {value}")

            agent = self.agent_service.update_agent(args.id, **update_data)

            if not agent:
                print(f"❌ Agent with ID {args.id} not found")
                return 1

            if self.verbose:
                print(f"✅ Agent updated: {agent.name}")

            self.print_agent(agent)
            return 0

        except ValueError as e:
            print(f"❌ Error: {str(e)}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Unexpected error: {str(e)}")
            return 1

    def handle_delete(self, args) -> int:
        """Handle the delete command."""
        try:
            agent = self.agent_service.get_agent(args.id)

            if not agent:
                print(f"❌ Agent with ID {args.id} not found")
                return 1

            if not args.force:
                response = input(
                    f"🗑️  Are you sure you want to delete agent '{agent.name}'? (y/N): "
                )
                if response.lower() not in ["y", "yes"]:
                    print("⚠️  Deletion cancelled")
                    return 0

            success = self.agent_service.delete_agent(args.id)

            if success:
                print(f"✅ Agent {agent.name} (ID: {args.id}) deleted")
                return 0
            else:
                print(f"❌ Failed to delete agent {args.id}")
                return 1

        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Error deleting agent: {str(e)}")
            return 1

    def handle_run(self, args) -> int:
        """Handle the run command."""
        try:
            output_directory = getattr(args, "output_dir", None)
            output_layout = getattr(args, "output_layout", None)
            save_requested = bool(args.save or args.output)
            if args.output_format and not save_requested:
                raise OutputConfigurationError(
                    "An output format requires --save or --output"
                )
            if (args.name_prefix or args.name_suffix) and (
                not args.save or args.output
            ):
                raise OutputConfigurationError(
                    "Filename prefix and suffix require --save without --output"
                )
            if output_layout and not save_requested:
                raise OutputConfigurationError(
                    "An output layout requires --save or --output"
                )

            output_format = self._resolve_output_format(args)
            output_filename = args.output

            agent_name = f"agent-{args.id}"
            if save_requested:
                get_agent = getattr(self.agent_service, "get_agent", None)
                if callable(get_agent):
                    agent = get_agent(args.id)
                    if agent is None:
                        print(f"Agent with ID {args.id} not found")
                        return 1
                    candidate_name = getattr(agent, "name", None)
                    if isinstance(candidate_name, str) and candidate_name.strip():
                        agent_name = candidate_name

            if output_filename:
                self.output_manager.resolve_output_path(
                    output_filename,
                    output_dir=output_directory,
                    agent_id=args.id,
                    agent_name=agent_name,
                    output_layout=output_layout,
                )
            elif save_requested:
                # Validate the configured root and layout before starting the
                # potentially expensive execution.  The intelligent filename
                # itself is derived from the generated result below.
                self.output_manager.get_agent_output_directory(
                    args.id,
                    agent_name,
                    output_dir=output_directory,
                    output_layout=output_layout,
                )

            if self.verbose:
                print(f"▶️  Running agent {args.id} with input: {args.input[:50]}...")

            result = self.agent_service.run_agent(
                agent_id=args.id, input_data={"text": args.input}, model=args.model
            )

            if self.verbose:
                print(f"✅ Execution completed in {result.get('duration_ms', 0)}ms")

            if args.save and output_filename is None:
                output_filename = generate_filename(
                    self._filename_content(result),
                    extension=output_format,
                    prefix=args.name_prefix,
                    suffix=args.name_suffix,
                )

            if output_filename:
                if output_format == "json":
                    written = self.output_manager.write_versioned_json(
                        output_filename,
                        result,
                        agent_id=args.id,
                        agent_name=agent_name,
                        output_dir=output_directory,
                        output_layout=output_layout,
                    )
                else:
                    written = self.output_manager.write_versioned_text(
                        output_filename,
                        self._result_as_text(result),
                        agent_id=args.id,
                        agent_name=agent_name,
                        output_dir=output_directory,
                        output_layout=output_layout,
                    )
                written_path = written.path
                print(f"💾 Result saved to: {written_path}")

            if self.format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"🎯 Execution ID: {result.get('execution_id')}")
                print(f"📊 Status: {result.get('status')}")
                print(f"⏱️  Duration: {result.get('duration_ms', 0)}ms")
                if "output" in result:
                    print(f"📝 Output: {result['output']}")

            return 0

        except OutputConfigurationError as e:
            print(f"❌ Error: {str(e)}")
            return 1
        except ValueError as e:
            print(f"❌ Error: {str(e)}")
            return 1
        except Exception as e:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"❌ Unexpected error: {str(e)}")
            return 1

    def handle_files(self, args: argparse.Namespace) -> int:
        """Handle generated-file history and restoration commands."""

        try:
            agent = self.agent_service.get_agent(args.id)
            if agent is None:
                print(f"Agent with ID {args.id} not found")
                return 1

            common = {
                "agent_id": args.id,
                "agent_name": agent.name,
                "output_dir": args.output_dir,
                "output_layout": args.output_layout,
            }
            if args.files_command == "versions":
                versions = self.output_manager.list_versions(args.filename, **common)
                if self.format == "json":
                    print(
                        json.dumps(
                            [version.to_dict() for version in versions],
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                elif not versions:
                    print(f"No versions found for {args.filename}")
                else:
                    for version in versions:
                        restored_note = (
                            f", restored from v{version.restored_from}"
                            if version.restored_from is not None
                            else ""
                        )
                        print(
                            f"v{version.version}: {version.created_at}, "
                            f"{version.size_bytes} bytes{restored_note}"
                        )
                return 0

            if args.files_command == "restore":
                restored_version = self.output_manager.restore_version(
                    args.filename,
                    args.version,
                    **common,
                )
                print(
                    f"Restored v{args.version} as v{restored_version.version}: "
                    f"{restored_version.path}"
                )
                return 0

            print(f"Unknown files command: {args.files_command}")
            return 1
        except OutputConfigurationError as error:
            print(f"Error: {error}")
            return 1
        except Exception as error:
            if self.verbose:
                import traceback

                traceback.print_exc()
            print(f"Unexpected error: {error}")
            return 1

    @staticmethod
    def _resolve_output_format(args: argparse.Namespace) -> str:
        requested = (
            normalize_extension(args.output_format) if args.output_format else None
        )
        if args.output:
            extension = Path(args.output).suffix
            if extension:
                inferred = normalize_extension(extension)
                if requested is not None and requested != inferred:
                    raise OutputConfigurationError(
                        "--output-format must match the --output filename extension"
                    )
                return inferred
        return requested or "json"

    @staticmethod
    def _result_as_text(result: Dict[str, Any]) -> str:
        output = result.get("output", result)
        if isinstance(output, str):
            return output
        if isinstance(output, dict) and isinstance(output.get("result"), str):
            return output["result"]
        return json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _filename_content(result: Dict[str, Any]) -> str:
        """Extract meaningful generated content for intelligent naming."""

        output = result.get("output", result)
        if isinstance(output, str):
            return output
        if isinstance(output, dict):
            for key in ("title", "summary", "result", "answer"):
                value = output.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return json.dumps(output, ensure_ascii=False, sort_keys=True)

    def print_agent(self, agent: Agent) -> None:
        """Print agent information."""
        if self.format == "json":
            print(json.dumps(agent.to_dict(), indent=2))
        else:
            print(f"🤖 Agent: {agent.name}")
            print(f"   ID: {agent.id}")
            print(f"   Model: {agent.model}")
            print(f"   Description: {agent.description}")
            print(f"   Active: {agent.is_active}")
            print(f"   Created: {agent.created_at}")
            print(f"   Updated: {agent.updated_at}")

    def print_table(
        self, data: List[Dict[str, Any]], title: Optional[str] = None
    ) -> None:
        """Print data as a formatted table."""
        if not data:
            print("🔍 No data to display")
            return

        if title:
            print(f"\n{title}")
            print("=" * 60)

        # Get headers from first item
        headers = list(data[0].keys())

        # Filter out long fields for table display
        display_headers = [
            h
            for h in headers
            if h not in ["description", "configuration", "input_data", "output_data"]
        ]

        # Print header
        header_line = " | ".join(f"{h:15}" for h in display_headers)
        print(header_line)
        print("-" * len(header_line))

        # Print rows
        for item in data:
            row = []
            for h in display_headers:
                value = item.get(h, "")
                if isinstance(value, dict):
                    value = json.dumps(value)[:15]
                elif isinstance(value, str) and len(value) > 20:
                    value = value[:17] + "..."
                row.append(f"{str(value):15}")
            print(" | ".join(row))

    def print_dict(self, data: Dict[str, Any], title: Optional[str] = None) -> None:
        """Print dictionary as formatted output."""
        if title:
            print(f"\n{title}")
            print("=" * 60)

        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{key}: ")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")


# Create CLI instance
cli = AgentWorldCLI()


def main() -> int:
    """Main entry point for the CLI."""
    return cli.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
