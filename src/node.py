"""Node implementation for distributed leader election using Bully Algorithm."""

import time
from typing import List, Optional, Set
from enum import Enum
from src.message import Message, MessageType
from src.logger import SimulationLogger


class NodeState(Enum):
    """Possible states for a node."""
    ALIVE = "ALIVE"
    DEAD = "DEAD"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"


class Node:
    """
    Represents a node in the distributed system.

    Each node has:
    - A unique ID (higher ID = higher priority)
    - A state (alive, dead, candidate, leader, follower)
    - A reference to all other nodes
    - Election logic based on the Bully Algorithm
    """

    def __init__(self, node_id: int, total_nodes: int, logger: SimulationLogger):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.logger = logger
        self.state = NodeState.ALIVE
        self.is_leader = False
        self.leader_id: Optional[int] = None
        self.election_in_progress = False
        self.ok_responses: Set[int] = set()
        self.all_nodes: List['Node'] = []
        self.message_queue: List[Message] = []
        self.last_heartbeat: float = time.time()
        self.heartbeat_timeout = 2.0

    def set_all_nodes(self, nodes: List['Node']) -> None:
        """Set reference to all nodes in the cluster."""
        self.all_nodes = nodes

    def fail(self) -> None:
        """Simulate node failure."""
        self.state = NodeState.DEAD
        self.is_leader = False
        self.logger.info(f"Node {self.node_id} has failed")

    def recover(self) -> None:
        """Recover a failed node."""
        self.state = NodeState.ALIVE
        self.logger.info(f"Node {self.node_id} has recovered")

    def is_alive(self) -> bool:
        """Check if node is alive."""
        return self.state != NodeState.DEAD

    def detect_leader_failure(self) -> bool:
        """Detect if the current leader has failed."""
        if self.leader_id is None:
            return False

        if self.leader_id == self.node_id:
            return False

        leader_node = self.all_nodes[self.leader_id]
        if not leader_node.is_alive():
            self.logger.info(f"Node {self.node_id} detected leader failure (Node {self.leader_id})")
            return True

        # Check heartbeat timeout
        current_time = time.time()
        if current_time - self.last_heartbeat > self.heartbeat_timeout:
            self.logger.info(f"Node {self.node_id} detected leader timeout (Node {self.leader_id})")
            return True

        return False

    def initiate_election(self) -> None:
        """Initiate a new election."""
        if self.election_in_progress or not self.is_alive():
            return

        self.election_in_progress = True
        self.state = NodeState.CANDIDATE
        self.ok_responses.clear()

        self.logger.info(f"Node {self.node_id} initiated election")

        # Send ELECTION messages to all nodes with higher IDs
        higher_nodes = [n for n in self.all_nodes if n.node_id > self.node_id]

        if not higher_nodes:
            # No nodes with higher ID, this node becomes leader
            self._become_leader()
        else:
            for node in higher_nodes:
                if node.is_alive():
                    election_msg = Message(
                        sender_id=self.node_id,
                        recipient_id=node.node_id,
                        message_type=MessageType.ELECTION,
                        timestamp=time.time(),
                    )
                    node.receive_message(election_msg)

    def receive_message(self, message: Message) -> None:
        """Receive a message from another node."""
        if not self.is_alive():
            return

        self.message_queue.append(message)

    def process_messages(self) -> None:
        """Process all pending messages."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self._handle_message(message)

    def _handle_message(self, message: Message) -> None:
        """Handle a received message."""
        if message.message_type == MessageType.ELECTION:
            self._handle_election_message(message)
        elif message.message_type == MessageType.OK:
            self._handle_ok_message(message)
        elif message.message_type == MessageType.LEADER:
            self._handle_leader_message(message)
        elif message.message_type == MessageType.HEARTBEAT:
            self._handle_heartbeat_message(message)

    def _handle_election_message(self, message: Message) -> None:
        """
        Handle ELECTION message.

        If this node has a higher ID, respond with OK and start own election.
        """
        sender_id = message.sender_id

        # Send OK response
        ok_msg = Message(
            sender_id=self.node_id,
            recipient_id=sender_id,
            message_type=MessageType.OK,
            timestamp=time.time(),
        )
        self.all_nodes[sender_id].receive_message(ok_msg)

        # If not already in election, start one
        if not self.election_in_progress:
            self.initiate_election()

    def _handle_ok_message(self, message: Message) -> None:
        """Handle OK message - record that a higher node is alive."""
        self.ok_responses.add(message.sender_id)

    def _handle_leader_message(self, message: Message) -> None:
        """Handle LEADER message - accept new leader."""
        new_leader_id = message.data.get("leader_id") if message.data else message.sender_id
        self.leader_id = new_leader_id
        self.is_leader = False
        self.state = NodeState.FOLLOWER
        self.election_in_progress = False
        self.logger.info(f"Node {self.node_id} accepted Node {new_leader_id} as leader")
        self.last_heartbeat = time.time()

    def _handle_heartbeat_message(self, message: Message) -> None:
        """Handle HEARTBEAT message from leader."""
        self.last_heartbeat = time.time()

    def _become_leader(self) -> None:
        """Become the leader and announce victory."""
        self.is_leader = True
        self.leader_id = self.node_id
        self.state = NodeState.LEADER
        self.election_in_progress = False

        self.logger.info(f"[LEADER] Node {self.node_id} became leader")

        # Send LEADER messages to all nodes with lower IDs
        lower_nodes = [n for n in self.all_nodes if n.node_id < self.node_id]
        for node in lower_nodes:
            if node.is_alive():
                leader_msg = Message(
                    sender_id=self.node_id,
                    recipient_id=node.node_id,
                    message_type=MessageType.LEADER,
                    timestamp=time.time(),
                    data={"leader_id": self.node_id},
                )
                node.receive_message(leader_msg)

    def send_heartbeat(self) -> None:
        """Send heartbeat to all followers (if leader)."""
        if not self.is_leader or not self.is_alive():
            return

        follower_nodes = [n for n in self.all_nodes if n.node_id < self.node_id]
        for node in follower_nodes:
            if node.is_alive():
                hb_msg = Message(
                    sender_id=self.node_id,
                    recipient_id=node.node_id,
                    message_type=MessageType.HEARTBEAT,
                    timestamp=time.time(),
                )
                node.receive_message(hb_msg)

    def check_election_completion(self) -> bool:
        """Check if this node should declare election victory."""
        if not self.election_in_progress or not self.is_alive():
            return False

        # If received any OK responses, wait longer
        if self.ok_responses:
            # Wait for higher nodes to complete election
            return False

        # No higher nodes responding, declare victory
        self._become_leader()
        return True

    def get_state(self) -> dict:
        """Get current state of the node."""
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "is_leader": self.is_leader,
            "leader_id": self.leader_id,
            "election_in_progress": self.election_in_progress,
            "ok_responses": len(self.ok_responses),
            "message_queue_size": len(self.message_queue),
        }
