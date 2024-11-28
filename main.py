# main.py

import asyncio
from manager.agent_manager import AgentManager
from knowledge_base.knowledge_base import KnowledgeBase
from user_interface.cli import CommandLineInterface

async def main():
    print("Starting main function...")
    knowledge_base = KnowledgeBase()
    manager = AgentManager()
    # Associate the knowledge base with the manager
    manager.knowledge_base = knowledge_base
    print("Knowledge base associated with manager.")
    cli = CommandLineInterface(manager)

    # Start the CLI
    print("Starting CLI...")
    await cli.start()

    # Print available attributes of the AgentManager object
    print("AgentManager attributes:", dir(manager))

    # Run agents
    await manager.run_agents()

if __name__ == "__main__":
    asyncio.run(main())