"""Unit tests for node election logic."""

import pytest
import time
from src.node import Node, NodeState
from src.message import Message, MessageType
from src.logger import SimulationLogger


@pytest.fixture
def logger():
    """Create a logger instance for testing."""
    return SimulationLogger(quiet=True)


@pytest.fixture
def nodes(logger):
    """Create a cluster of 5 nodes for testing."""
    nodes_list = [Node(i, 5, logger) for i in range(5)]
    for node in nodes_list:
        node.set_all_nodes(nodes_list)
    return nodes_list


class TestNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, logger):
        """Test that a node is created with correct properties."""
        node = Node(0, 5, logger)
        assert node.node_id == 0
        assert node.total_nodes == 5
        assert node.state == NodeState.ALIVE
        assert node.is_leader is False
        assert node.leader_id is None

    def test_multiple_nodes(self, nodes):
        """Test creation of multiple nodes."""
        assert len(nodes) == 5
        for i, node in enumerate(nodes):
            assert node.node_id == i
            assert node.state == NodeState.ALIVE


class TestNodeFailure:
    """Tests for node failure detection and handling."""

    def test_node_failure(self, logger):
        """Test that a node can fail."""
        node = Node(0, 5, logger)
        assert node.is_alive()
        node.fail()
        assert not node.is_alive()
        assert node.state == NodeState.DEAD

    def test_node_recovery(self, logger):
        """Test that a node can recover from failure."""
        node = Node(0, 5, logger)
        node.fail()
        assert not node.is_alive()
        node.recover()
        assert node.is_alive()
        assert node.state == NodeState.ALIVE

    def test_dead_node_rejects_messages(self, nodes):
        """Test that dead nodes don't process messages."""
        nodes[0].fail()
        msg = Message(
            sender_id=1,
            recipient_id=0,
            message_type=MessageType.ELECTION,
            timestamp=time.time(),
        )
        nodes[0].receive_message(msg)
        assert len(nodes[0].message_queue) == 0


class TestElectionMessages:
    """Tests for election message handling."""

    def test_send_election_message(self, nodes):
        """Test sending an election message."""
        msg = Message(
            sender_id=0,
            recipient_id=1,
            message_type=MessageType.ELECTION,
            timestamp=time.time(),
        )
        nodes[1].receive_message(msg)
        assert len(nodes[1].message_queue) == 1
        assert nodes[1].message_queue[0] == msg

    def test_handle_election_message(self, nodes):
        """Test handling an election message."""
        # Node 1 sends election to Node 0
        msg = Message(
            sender_id=1,
            recipient_id=0,
            message_type=MessageType.ELECTION,
            timestamp=time.time(),
        )
        nodes[0].receive_message(msg)
        nodes[0].process_messages()

        # Node 0 should have started election and sent OK response
        assert nodes[0].election_in_progress
        assert len(nodes[1].message_queue) > 0

    def test_ok_response_tracking(self, nodes):
        """Test that OK responses are tracked."""
        nodes[0].ok_responses.add(2)
        nodes[0].ok_responses.add(3)
        assert len(nodes[0].ok_responses) == 2
        assert 2 in nodes[0].ok_responses


class TestBullyElection:
    """Tests for Bully algorithm election logic."""

    def test_highest_node_wins(self, nodes):
        """Test that the highest node ID wins election."""
        # Initiate election from node 0
        nodes[0].initiate_election()

        # Process messages in order
        for _ in range(20):
            for node in nodes:
                node.process_messages()

        # Highest node should be leader
        assert nodes[4].is_leader
        assert nodes[4].leader_id == 4

    def test_single_node_election(self, logger):
        """Test election with a single node."""
        node = Node(0, 1, logger)
        node.set_all_nodes([node])
        node.initiate_election()
        node.process_messages()
        node.check_election_completion()
        assert node.is_leader

    def test_election_propagation(self, nodes):
        """Test that election message propagates correctly."""
        # Start election from node 0
        nodes[0].initiate_election()

        # Simulate message passing
        for _ in range(30):
            for node in nodes:
                node.process_messages()
                node.check_election_completion()

        # Verify all nodes know about the leader
        leader_id = nodes[4].node_id
        for node in nodes:
            if node.is_alive():
                assert node.leader_id == leader_id

    def test_leader_detection(self, nodes):
        """Test that a leader is correctly detected."""
        # Set node 3 as leader
        nodes[3].is_leader = True
        nodes[3].leader_id = 3
        for node in nodes:
            node.leader_id = 3

        # Leader should not detect its own failure
        assert not nodes[3].detect_leader_failure()

        # Fail the leader
        nodes[3].fail()

        # Other nodes should detect failure
        assert nodes[2].detect_leader_failure()
        assert nodes[1].detect_leader_failure()


class TestLeaderElection:
    """Tests for leader announcement."""

    def test_leader_announcement(self, nodes):
        """Test that elected leader announces to all."""
        nodes[4].is_leader = True
        nodes[4].leader_id = 4
        nodes[4].state = NodeState.LEADER

        # Send leader messages
        for node in nodes:
            if node.node_id < 4 and node.is_alive():
                msg = Message(
                    sender_id=4,
                    recipient_id=node.node_id,
                    message_type=MessageType.LEADER,
                    timestamp=time.time(),
                    data={"leader_id": 4},
                )
                node.receive_message(msg)

        # Process messages
        for node in nodes:
            node.process_messages()

        # All nodes should recognize the leader
        for node in nodes:
            if node.node_id != 4:
                assert node.leader_id == 4
                assert not node.is_leader

    def test_heartbeat_message(self, nodes):
        """Test heartbeat message from leader."""
        nodes[4].is_leader = True
        nodes[4].leader_id = 4

        # Send heartbeat
        nodes[4].send_heartbeat()

        # Check that heartbeat messages were sent
        total_messages = sum(len(node.message_queue) for node in nodes if node.node_id < 4)
        assert total_messages > 0

        # Process heartbeats
        for node in nodes:
            node.process_messages()

        # Heartbeat time should be updated
        for node in nodes:
            if node.node_id < 4:
                assert node.last_heartbeat > time.time() - 1


class TestMessageHandling:
    """Tests for message processing."""

    def test_message_queue_fifo(self, nodes):
        """Test that messages are processed FIFO."""
        msg1 = Message(
            sender_id=1,
            recipient_id=0,
            message_type=MessageType.ELECTION,
            timestamp=time.time(),
        )
        msg2 = Message(
            sender_id=2,
            recipient_id=0,
            message_type=MessageType.OK,
            timestamp=time.time(),
        )

        nodes[0].receive_message(msg1)
        nodes[0].receive_message(msg2)

        assert nodes[0].message_queue[0] == msg1
        assert nodes[0].message_queue[1] == msg2

    def test_process_all_messages(self, nodes):
        """Test that all messages in queue are processed."""
        for i in range(1, 5):
            msg = Message(
                sender_id=i,
                recipient_id=0,
                message_type=MessageType.ELECTION,
                timestamp=time.time(),
            )
            nodes[0].receive_message(msg)

        assert len(nodes[0].message_queue) == 4
        nodes[0].process_messages()
        assert len(nodes[0].message_queue) == 0


class TestNodeState:
    """Tests for node state management."""

    def test_state_transitions(self, logger):
        """Test valid state transitions."""
        node = Node(0, 5, logger)

        # Initial state
        assert node.state == NodeState.ALIVE

        # Transition to candidate
        node.state = NodeState.CANDIDATE
        assert node.state == NodeState.CANDIDATE

        # Transition to leader
        node.state = NodeState.LEADER
        assert node.state == NodeState.LEADER

        # Transition to dead
        node.fail()
        assert node.state == NodeState.DEAD

    def test_get_state_dict(self, nodes):
        """Test state dictionary export."""
        nodes[0].is_leader = True
        nodes[0].leader_id = 0
        state = nodes[0].get_state()

        assert state["node_id"] == 0
        assert state["is_leader"] is True
        assert state["leader_id"] == 0
        assert state["state"] == "ALIVE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
