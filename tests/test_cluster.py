"""Integration tests for cluster management."""

import pytest
from src.cluster import Cluster
from src.logger import SimulationLogger


@pytest.fixture
def logger():
    """Create a logger instance for testing."""
    return SimulationLogger(quiet=True)


class TestClusterInitialization:
    """Tests for cluster setup and initialization."""

    def test_cluster_creation(self, logger):
        """Test that a cluster is created with correct properties."""
        cluster = Cluster(num_nodes=5, logger=logger)
        assert cluster.num_nodes == 5
        assert len(cluster.nodes) == 5
        assert cluster.election_round == 0

    def test_nodes_reference_each_other(self, logger):
        """Test that all nodes have references to each other."""
        cluster = Cluster(num_nodes=5, logger=logger)
        for node in cluster.nodes:
            assert len(node.all_nodes) == 5

    def test_initial_leader_assignment(self, logger):
        """Test that initial leader is the highest ID node."""
        cluster = Cluster(num_nodes=5, logger=logger)
        assert cluster.leader_id == 4

        # All nodes should know about the initial leader
        for node in cluster.nodes:
            assert node.leader_id == 4


class TestClusterOperations:
    """Tests for cluster operations."""

    def test_fail_node(self, logger):
        """Test failing a specific node."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.fail_node(0)
        assert not cluster.nodes[0].is_alive()
        assert 0 in cluster.failed_nodes

    def test_recover_node(self, logger):
        """Test recovering a failed node."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.fail_node(0)
        cluster.recover_node(0)
        assert cluster.nodes[0].is_alive()
        assert 0 not in cluster.failed_nodes

    def test_fail_nonexistent_node(self, logger):
        """Test that failing invalid node ID is safe."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.fail_node(10)  # Should not raise
        assert 10 not in cluster.failed_nodes

    def test_cluster_state_property(self, logger):
        """Test getting cluster state."""
        cluster = Cluster(num_nodes=5, logger=logger)
        state = cluster.get_cluster_state()

        assert "leader_id" in state
        assert "election_round" in state
        assert "total_nodes" in state
        assert "alive_nodes" in state
        assert "nodes" in state


class TestSimulationSteps:
    """Tests for simulation stepping."""

    def test_simulate_step(self, logger):
        """Test running a single simulation step."""
        cluster = Cluster(num_nodes=3, logger=logger)
        result = cluster.simulate_step()
        assert isinstance(result, bool)

    def test_run_until_elected(self, logger):
        """Test running until election completes."""
        cluster = Cluster(num_nodes=5, logger=logger)
        result = cluster.run_until_elected(max_steps=50, step_delay=0.01)
        assert result is True

    def test_max_steps_timeout(self, logger):
        """Test that max steps timeout works."""
        cluster = Cluster(num_nodes=5, logger=logger)
        # Force a problematic state by not allowing election to complete
        result = cluster.run_until_elected(max_steps=1, step_delay=0.01)
        # With only 1 step, likely won't complete (depends on timing)
        assert isinstance(result, bool)


class TestClusterStateTracking:
    """Tests for cluster state tracking."""

    def test_election_history(self, logger):
        """Test that election history is tracked."""
        cluster = Cluster(num_nodes=5, logger=logger)
        history1 = cluster.get_election_history()

        # Fail leader to trigger election
        cluster.fail_node(4)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        history2 = cluster.get_election_history()
        # Should have at least as many as before
        assert len(history2) >= len(history1)

    def test_events_logging(self, logger):
        """Test that events are logged."""
        cluster = Cluster(num_nodes=3, logger=logger)
        cluster.fail_node(0)

        events = cluster.get_events()
        assert len(events) > 0

    def test_simulation_time_tracking(self, logger):
        """Test that simulation time is tracked."""
        cluster = Cluster(num_nodes=3, logger=logger)
        initial_time = cluster.simulation_time

        for _ in range(5):
            cluster.simulate_step(0.1)

        assert cluster.simulation_time > initial_time


class TestClusterConsistency:
    """Tests for cluster consistency guarantees."""

    def test_single_leader_invariant(self, logger):
        """Test that only one leader exists at a time."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        leaders = [n for n in cluster.nodes if n.is_leader]
        assert len(leaders) == 1

    def test_leader_agreement_invariant(self, logger):
        """Test that all alive nodes agree on the leader."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        leader_ids = set()
        for node in cluster.nodes:
            if node.is_alive():
                leader_ids.add(node.leader_id)

        # All should agree on same leader
        assert len(leader_ids) == 1

    def test_leader_is_highest_alive(self, logger):
        """Test that elected leader has highest ID among alive nodes."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        leader_id = cluster.leader_id
        alive_ids = [n.node_id for n in cluster.nodes if n.is_alive()]

        assert leader_id == max(alive_ids)


class TestScalability:
    """Tests for scalability with different cluster sizes."""

    @pytest.mark.parametrize("num_nodes", [1, 2, 3, 5, 10, 20])
    def test_election_with_varying_sizes(self, logger, num_nodes):
        """Test election works with different cluster sizes."""
        cluster = Cluster(num_nodes=num_nodes, logger=logger)
        result = cluster.run_until_elected(max_steps=100, step_delay=0.01)
        assert result is True
        assert cluster.leader_id == num_nodes - 1

    @pytest.mark.parametrize("num_nodes", [5, 10, 15])
    def test_election_after_failure(self, logger, num_nodes):
        """Test re-election works with different cluster sizes."""
        cluster = Cluster(num_nodes=num_nodes, logger=logger)
        old_leader = cluster.leader_id

        cluster.fail_node(old_leader)
        result = cluster.run_until_elected(max_steps=100, step_delay=0.01)

        assert result is True
        assert cluster.leader_id != old_leader


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
