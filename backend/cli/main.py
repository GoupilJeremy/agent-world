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
import sys
from typing import Any, Dict, List, Optional

from ..models.agent import Agent
from ..services.agent_service import AgentService


class CLIFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter for better CLI help display."""

    pass


def create_parser():
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

    return parser


class AgentWorldCLI:
    """Main CLI class for Agent World."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = create_parser()
        self.agent_service = AgentService()
        self.verbose = False
        self.format = "table"

    def run(self, args: Optional[List[str]] = None):
        """
        Run the CLI with the given arguments.

        Args:
            args: List of command line arguments (default: sys.argv[1:])
        """
        args = args or sys.argv[1:]
        parsed_args = self.parser.parse_args(args)

        # Set global options
        self.verbose = parsed_args.verbose
        self.format = parsed_args.format

        # Route to the appropriate command handler
        command = parsed_args.command
        handler_name = f"handle_{command}"

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return handler(parsed_args)
        else:
            print(f"❌ Unknown command: {command}")
            self.parser.print_help()
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
            if self.verbose:
                print(f"▶️  Running agent {args.id} with input: {args.input[:50]}...")

            result = self.agent_service.run_agent(
                agent_id=args.id, input_data={"text": args.input}, model=args.model
            )

            if self.verbose:
                print(f"✅ Execution completed in {result.get('duration_ms', 0)}ms")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Result saved to: {args.output}")

            if self.format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"🎯 Execution ID: {result.get('execution_id')}")
                print(f"📊 Status: {result.get('status')}")
                print(f"⏱️  Duration: {result.get('duration_ms', 0)}ms")
                if "output" in result:
                    print(f"📝 Output: {result['output']}")

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


def main():
    """Main entry point for the CLI."""
    import sys

    return cli.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
