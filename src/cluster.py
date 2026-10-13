"""Cluster management for distributed leader election simulation."""

import time
from typing import List, Optional, Dict
from src.node import Node
from src.logger import SimulationLogger


class Cluster:
    """
    Manages a cluster of nodes in a distributed election simulation.

    Coordinates message passing, detects failures, and tracks election state.
    """

    def __init__(self, num_nodes: int = 5, logger: Optional[SimulationLogger] = None):
        self.num_nodes = num_nodes
        self.logger = logger or SimulationLogger()
        self.nodes: List[Node] = []
        self.election_round = 0
        self.simulation_time = 0.0
        self.failed_nodes: set = set()

        # Initialize nodes
        for node_id in range(num_nodes):
            node = Node(node_id, num_nodes, self.logger)
            self.nodes.append(node)

        # Set all nodes reference
        for node in self.nodes:
            node.set_all_nodes(self.nodes)

        # Elect initial leader (highest ID)
        self.nodes[-1].is_leader = True
        self.nodes[-1].leader_id = num_nodes - 1
        self.logger.info(f"Initial leader elected: Node {num_nodes - 1}")

        for node in self.nodes:
            if not node.is_leader:
                node.leader_id = num_nodes - 1

    @property
    def leader_id(self) -> Optional[int]:
        """Get current leader ID."""
        for node in self.nodes:
            if node.is_leader:
                return node.node_id
        return None

    def start(self) -> None:
        """Start the cluster simulation."""
        self.logger.info(f"Starting cluster with {self.num_nodes} nodes")

    def fail_node(self, node_id: int) -> None:
        """Simulate failure of a specific node."""
        if 0 <= node_id < self.num_nodes:
            self.nodes[node_id].fail()
            self.failed_nodes.add(node_id)

            # If leader failed, trigger election
            if self.nodes[node_id].is_leader:
                self.logger.info(f"Leader Node {node_id} failed - triggering new election")
                self._trigger_election_on_failure()

    def recover_node(self, node_id: int) -> None:
        """Recover a failed node."""
        if 0 <= node_id < self.num_nodes:
            self.nodes[node_id].recover()
            self.failed_nodes.discard(node_id)

    def _trigger_election_on_failure(self) -> None:
        """Trigger election when leader fails."""
        # Find highest alive node to initiate election
        for node in reversed(self.nodes):
            if node.is_alive() and not node.is_leader:
                node.initiate_election()
                break

    def simulate_step(self, timeout: float = 1.0) -> bool:
        """
        Simulate one step of the election process.

        Returns True if an election completed, False otherwise.
        """
        # Process all pending messages
        for node in self.nodes:
            if node.is_alive():
                node.process_messages()

        # Check for election completion
        for node in self.nodes:
            if node.is_alive():
                if node.check_election_completion():
                    self.election_round += 1
                    self.logger.log_election_round(
                        self.election_round,
                        node.node_id,
                        [n.node_id for n in self.nodes if n.is_alive()],
                    )
                    return True

        # Check for leader failure
        for node in self.nodes:
            if node.is_alive() and not node.is_leader:
                if node.detect_leader_failure():
                    node.initiate_election()

        # Leader sends heartbeat
        leader = self.nodes[self.leader_id] if self.leader_id is not None else None
        if leader and leader.is_alive():
            leader.send_heartbeat()

        self.simulation_time += timeout
        return False

    def run_until_elected(self, max_steps: int = 100, step_delay: float = 0.1) -> bool:
        """
        Run simulation until a leader is elected.

        Args:
            max_steps: Maximum simulation steps before timeout
            step_delay: Delay between steps in seconds

        Returns:
            True if election succeeded, False if timeout
        """
        for step in range(max_steps):
            # Check if we already have a valid leader
            if self.leader_id is not None and self.nodes[self.leader_id].is_alive():
                if step > 0:
                    self.logger.info(f"Leader elected in {step} steps")
                return True

            if self.simulate_step(step_delay):
                self.logger.info(f"Election completed in {step} steps")
                return True

            time.sleep(step_delay)

        self.logger.warning(f"Election timeout after {max_steps} steps")
        return False

    def get_cluster_state(self) -> Dict:
        """Get current state of entire cluster."""
        return {
            "leader_id": self.leader_id,
            "election_round": self.election_round,
            "simulation_time": self.simulation_time,
            "total_nodes": self.num_nodes,
            "alive_nodes": len([n for n in self.nodes if n.is_alive()]),
            "failed_nodes": list(self.failed_nodes),
            "nodes": [node.get_state() for node in self.nodes],
        }

    def get_election_history(self) -> List[Dict]:
        """Get history of all elections."""
        return self.logger.get_election_history()

    def get_events(self) -> List[Dict]:
        """Get all logged events."""
        return self.logger.get_events()

    def print_state(self) -> None:
        """Print current cluster state."""
        state = self.get_cluster_state()
        print(f"\nCluster State (Round {state['election_round']}):")
        print(f"  Leader: Node {state['leader_id']}")
        print(f"  Alive: {state['alive_nodes']}/{state['total_nodes']}")
        if state["failed_nodes"]:
            print(f"  Failed: {state['failed_nodes']}")

        print("  Nodes:")
        for node_state in state["nodes"]:
            status = "[OK]" if node_state["state"] == "ALIVE" else "[XX]"
            leader_mark = " (LEADER)" if node_state["is_leader"] else ""
            print(f"    {status} Node {node_state['node_id']}{leader_mark}")
