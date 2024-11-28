"""Command-line interface for the Arcana Agent Framework."""

import click
import json
import yaml
from typing import Dict, Any
from pathlib import Path
import asyncio
from datetime import datetime

from core.agent_registry import AgentRegistry
from core.protocol import Message
from core.user_profile import UserProfile
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback import Feedback, FeedbackManager

@click.group()
@click.pass_context
def cli(ctx):
    """Arcana Agent Framework CLI."""
    ctx.ensure_object(dict)
    
    # Initialize core components
    ctx.obj['metrics'] = MetricsCollector()
    ctx.obj['error_handler'] = ErrorHandler()
    ctx.obj['agent_registry'] = AgentRegistry(
        ctx.obj['metrics'],
        ctx.obj['error_handler']
    )
    ctx.obj['feedback_manager'] = FeedbackManager(
        ctx.obj['metrics'],
        ctx.obj['error_handler']
    )

@cli.command()
@click.pass_context
def list_agents(ctx):
    """List all registered agents."""
    registry = ctx.obj['agent_registry']
    agents = registry.list_agents()
    
    if not agents:
        click.echo("No agents registered")
        return
        
    click.echo("\nRegistered Agents:")
    for agent in agents:
        status = registry.get_agent_status(agent)
        click.echo(f"\n{agent}:")
        click.echo(f"  Status: {status['active']}")
        click.echo(f"  Type: {status['type']}")

@cli.command()
@click.option('--name', required=True, help='Name of the agent to run')
@click.option('--payload', required=True, help='JSON payload for the agent')
@click.pass_context
def run_agent(ctx, name: str, payload: str):
    """Run an agent with specified payload."""
    try:
        payload_data = json.loads(payload)
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON payload")
        return

    registry = ctx.obj['agent_registry']
    
    if name not in registry.list_agents():
        click.echo(f"Error: Agent '{name}' not found")
        return

    message = Message.create(
        intent="execute",
        agent=name,
        payload=payload_data
    )

    async def run():
        try:
            await registry.send_message(message)
            click.echo(f"Message sent to agent: {name}")
        except Exception as e:
            click.echo(f"Error running agent: {str(e)}")

    asyncio.run(run())

@cli.command()
@click.option('--workflow', required=True, help='Path to workflow YAML file')
@click.pass_context
def run_workflow(ctx, workflow: str):
    """Run a workflow from a YAML file."""
    if not Path(workflow).exists():
        click.echo(f"Error: Workflow file not found: {workflow}")
        return

    try:
        with open(workflow, 'r') as f:
            workflow_data = yaml.safe_load(f)
    except yaml.YAMLError:
        click.echo("Error: Invalid YAML file")
        return

    registry = ctx.obj['agent_registry']

    async def run():
        try:
            message = Message.create(
                intent="start_workflow",
                agent="coordinator",
                payload=workflow_data
            )
            await registry.send_message(message)
            click.echo("Workflow started")
        except Exception as e:
            click.echo(f"Error running workflow: {str(e)}")

    asyncio.run(run())

@cli.command()
@click.option('--agent', required=True, help='Name of the agent')
@click.option('--type', required=True, help='Type of feedback')
@click.option('--message', required=True, help='Feedback message')
@click.option('--severity', default='info', help='Feedback severity')
@click.pass_context
def feedback(ctx, agent: str, type: str, message: str, severity: str):
    """Submit feedback for an agent."""
    manager = ctx.obj['feedback_manager']
    
    feedback = Feedback.create(
        agent_name=agent,
        feedback_type=type,
        message=message,
        severity=severity
    )
    
    manager.add_feedback(feedback)
    click.echo("Feedback submitted successfully")

@cli.command()
@click.option('--agent', help='Filter by agent name')
@click.pass_context
def status(ctx, agent: str = None):
    """Show status of agents and workflows."""
    registry = ctx.obj['agent_registry']
    
    if agent:
        if agent not in registry.list_agents():
            click.echo(f"Error: Agent '{agent}' not found")
            return
            
        status = registry.get_agent_status(agent)
        click.echo(f"\nAgent: {agent}")
        click.echo(f"Status: {status['active']}")
        click.echo(f"Type: {status['type']}")
        
        # Show feedback summary if available
        manager = ctx.obj['feedback_manager']
        summary = manager.get_feedback_summary(agent)
        if summary['total_feedback'] > 0:
            click.echo("\nFeedback Summary:")
            click.echo(f"Total Feedback: {summary['total_feedback']}")
            click.echo("Types:")
            for type, count in summary['feedback_types'].items():
                click.echo(f"  {type}: {count}")
    else:
        # Show all agents
        click.echo("\nAgent Status:")
        for agent_name in registry.list_agents():
            status = registry.get_agent_status(agent_name)
            click.echo(f"\n{agent_name}:")
            click.echo(f"  Status: {status['active']}")
            click.echo(f"  Type: {status['type']}")

if __name__ == '__main__':
    cli(obj={})
