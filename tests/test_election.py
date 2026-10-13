"""Integration tests for the election algorithm."""

import pytest
import time
from src.cluster import Cluster
from src.logger import SimulationLogger


@pytest.fixture
def logger():
    """Create a logger instance for testing."""
    return SimulationLogger(quiet=True)


class TestElectionAlgorithm:
    """Tests for complete election algorithm."""

    def test_initial_leader_election(self, logger):
        """Test that initial leader is elected correctly."""
        cluster = Cluster(num_nodes=5, logger=logger)
        assert cluster.leader_id == 4  # Highest ID node

    def test_all_nodes_know_leader(self, logger):
        """Test that all nodes know who the leader is."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        for node in cluster.nodes:
            if node.is_alive():
                assert node.leader_id is not None
                assert node.leader_id == cluster.leader_id

    def test_leader_failure_triggers_election(self, logger):
        """Test that leader failure triggers new election."""
        cluster = Cluster(num_nodes=5, logger=logger)
        old_leader = cluster.leader_id

        # Fail the leader
        cluster.fail_node(old_leader)

        # Run election until completion
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # New leader should be different
        new_leader = cluster.leader_id
        assert new_leader != old_leader
        assert new_leader is not None

    def test_single_node_cluster(self, logger):
        """Test election with single node."""
        cluster = Cluster(num_nodes=1, logger=logger)
        assert cluster.leader_id == 0

    def test_two_node_cluster(self, logger):
        """Test election with two nodes."""
        cluster = Cluster(num_nodes=2, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Higher ID node should be leader
        assert cluster.leader_id == 1

        # Fail leader
        cluster.fail_node(1)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Lower ID node becomes leader
        assert cluster.leader_id == 0

    def test_large_cluster(self, logger):
        """Test election with many nodes."""
        cluster = Cluster(num_nodes=20, logger=logger)
        cluster.run_until_elected(max_steps=100, step_delay=0.01)

        assert cluster.leader_id == 19
        assert cluster.election_round >= 0

    def test_multiple_failures(self, logger):
        """Test handling multiple node failures."""
        cluster = Cluster(num_nodes=7, logger=logger)
        initial_leader = cluster.leader_id

        # Fail leader multiple times
        cluster.fail_node(initial_leader)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)
        leader1 = cluster.leader_id

        cluster.fail_node(leader1)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)
        leader2 = cluster.leader_id

        # Each time should elect a different leader
        assert leader1 != initial_leader
        assert leader2 != leader1

    def test_node_recovery(self, logger):
        """Test that recovered nodes participate in cluster."""
        cluster = Cluster(num_nodes=5, logger=logger)
        original_leader = cluster.leader_id

        # Fail a non-leader node
        cluster.fail_node(0)
        assert not cluster.nodes[0].is_alive()

        # Recover it
        cluster.recover_node(0)
        assert cluster.nodes[0].is_alive()

    def test_election_round_tracking(self, logger):
        """Test that election rounds are tracked."""
        cluster = Cluster(num_nodes=5, logger=logger)
        initial_rounds = len(cluster.get_election_history())

        # Trigger election by failing leader
        cluster.fail_node(cluster.leader_id)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Should have recorded a new election
        history = cluster.get_election_history()
        assert len(history) > initial_rounds

    def test_cluster_state_consistency(self, logger):
        """Test that cluster state remains consistent."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        state = cluster.get_cluster_state()

        # Verify state consistency
        assert state["leader_id"] is not None
        assert state["total_nodes"] == 5
        assert 0 <= state["alive_nodes"] <= 5
        assert len(state["nodes"]) == 5

    def test_election_completes(self, logger):
        """Test that election always completes."""
        for num_nodes in [3, 5, 7, 10]:
            cluster = Cluster(num_nodes=num_nodes, logger=logger)
            result = cluster.run_until_elected(max_steps=100, step_delay=0.01)
            assert result, f"Election failed for {num_nodes} nodes"
            assert cluster.leader_id is not None

    def test_no_split_brain(self, logger):
        """Test that only one leader exists at a time."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Count leaders
        leaders = [n for n in cluster.nodes if n.is_leader]
        assert len(leaders) == 1, "Multiple leaders detected (split brain)"

    def test_leader_consensus(self, logger):
        """Test that all alive nodes agree on leader."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Get leader ID from first alive node
        first_leader = None
        for node in cluster.nodes:
            if node.is_alive():
                first_leader = node.leader_id
                break

        # All alive nodes should agree
        for node in cluster.nodes:
            if node.is_alive():
                assert node.leader_id == first_leader, f"Node {node.node_id} disagrees on leader"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_all_nodes_fail(self, logger):
        """Test behavior when all nodes fail."""
        cluster = Cluster(num_nodes=3, logger=logger)

        for i in range(cluster.num_nodes):
            cluster.fail_node(i)

        # No leader should be present
        assert cluster.leader_id is None

    def test_partial_network_partition(self, logger):
        """Test cluster with some dead nodes."""
        cluster = Cluster(num_nodes=5, logger=logger)
        cluster.run_until_elected(max_steps=50, step_delay=0.01)

        # Fail some non-leader nodes
        cluster.fail_node(0)
        cluster.fail_node(1)

        state = cluster.get_cluster_state()
        assert state["alive_nodes"] == 3

    def test_rapid_failures(self, logger):
        """Test rapid successive failures."""
        cluster = Cluster(num_nodes=5, logger=logger)

        for i in range(4):
            cluster.fail_node(i)
            assert not cluster.nodes[i].is_alive()

        # Last node should still be alive and be leader
        assert cluster.nodes[4].is_alive()
        assert cluster.nodes[4].is_leader


class TestPerformance:
    """Performance-related tests."""

    def test_election_speed(self, logger):
        """Test that election completes quickly."""
        cluster = Cluster(num_nodes=10, logger=logger)
        start_time = time.time()
        cluster.run_until_elected(max_steps=50, step_delay=0.01)
        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 5.0, f"Election took too long: {elapsed}s"

    def test_simulation_step_speed(self, logger):
        """Test that simulation steps are fast."""
        cluster = Cluster(num_nodes=20, logger=logger)

        start_time = time.time()
        for _ in range(100):
            cluster.simulate_step(0.01)
        elapsed = time.time() - start_time

        # 100 steps should be fast
        assert elapsed < 10.0, f"Simulation too slow: {elapsed}s for 100 steps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
