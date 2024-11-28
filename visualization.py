import networkx as nx
import matplotlib.pyplot as plt
import random

class AgentSimulation:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.agents = ['Agent A', 'Agent B', 'Agent C', 'Agent D']
        self.tasks = ['Task 1', 'Task 2', 'Task 3']
        self.setup_agents()

    def setup_agents(self):
        for agent in self.agents:
            self.graph.add_node(agent, type='agent')

        for task in self.tasks:
            self.graph.add_node(task, type='task')

    def simulate_interactions(self):
        for _ in range(10):  # Simulate 10 interactions
            agent = random.choice(self.agents)
            task = random.choice(self.tasks)
            self.graph.add_edge(agent, task, label=f"{agent} -> {task}", weight=random.randint(1, 5))

    def visualize(self):
        pos = nx.circular_layout(self.graph)  # Use a circular layout to reduce overlap
        agent_nodes = [n for n, attr in self.graph.nodes(data=True) if attr['type'] == 'agent']
        task_nodes = [n for n, attr in self.graph.nodes(data=True) if attr['type'] == 'task']

        # Limit node size variation
        node_sizes = [300 + 50 * self.graph.degree(n) for n in self.graph.nodes()]

        # Draw agent nodes with labels and size
        nx.draw_networkx_nodes(self.graph, pos, nodelist=agent_nodes, node_color='lightblue', node_size=[node_sizes[i] for i, n in enumerate(self.graph.nodes()) if n in agent_nodes], label='Agents')
        nx.draw_networkx_labels(self.graph, pos, labels={n: n for n in agent_nodes}, font_color='darkblue')

        # Draw task nodes with labels and size
        nx.draw_networkx_nodes(self.graph, pos, nodelist=task_nodes, node_color='lightgreen', node_size=[node_sizes[i] for i, n in enumerate(self.graph.nodes()) if n in task_nodes], label='Tasks')
        nx.draw_networkx_labels(self.graph, pos, labels={n: n for n in task_nodes}, font_color='darkgreen')

        # Simplify edges by removing labels
        nx.draw_networkx_edges(self.graph, pos, edgelist=self.graph.edges(), arrowstyle='->', arrowsize=15, edge_color='gray', width=[1.0 + 0.2 * self.graph[u][v].get('weight', 1) for u, v in self.graph.edges()])

        plt.title('Agent Interactions and Tasks')
        plt.legend(scatterpoints=1, loc='upper left')
        plt.axis('off')  # Turn off the axis
        plt.show()

if __name__ == "__main__":
    simulation = AgentSimulation()
    simulation.simulate_interactions()
    simulation.visualize()
