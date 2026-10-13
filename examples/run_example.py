"""Example usage of the distributed leader election simulator."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.cluster import Cluster
from src.logger import SimulationLogger


def example_basic_election():
    """Example 1: Basic election with 5 nodes."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Election (5 nodes)")
    print("=" * 60)

    logger = SimulationLogger(verbose=False)
    cluster = Cluster(num_nodes=5, logger=logger)
    cluster.start()

    logger.info("Scenario: Initial leader election")
    logger.info(f"Initial leader: Node {cluster.leader_id}")

    cluster.run_until_elected(max_steps=50, step_delay=0.05)
    cluster.print_state()


def example_leader_failure():
    """Example 2: Leader failure and re-election."""
    print("\n" + "=" * 60)
    print("Example 2: Leader Failure & Re-election (8 nodes)")
    print("=" * 60)

    logger = SimulationLogger(verbose=False)
    cluster = Cluster(num_nodes=8, logger=logger)
    cluster.start()

    logger.info("Phase 1: Initial election")
    cluster.run_until_elected(max_steps=50, step_delay=0.05)
    initial_leader = cluster.leader_id
    print(f"\nInitial leader: Node {initial_leader}")

    # Simulate leader failure
    logger.info("\nPhase 2: Triggering leader failure...")
    time.sleep(1)
    cluster.fail_node(initial_leader)

    logger.info("\nPhase 3: Re-election after failure")
    cluster.run_until_elected(max_steps=50, step_delay=0.05)
    new_leader = cluster.leader_id
    print(f"\nNew leader after failure: Node {new_leader}")
    print(f"Leader changed: {initial_leader} -> {new_leader}")


def example_cascading_failures():
    """Example 3: Multiple cascading failures."""
    print("\n" + "=" * 60)
    print("Example 3: Cascading Failures (10 nodes)")
    print("=" * 60)

    logger = SimulationLogger(verbose=False)
    cluster = Cluster(num_nodes=10, logger=logger)
    cluster.start()

    logger.info("Initial election...")
    cluster.run_until_elected(max_steps=50, step_delay=0.05)

    # Simulate multiple failures
    leaders_history = [cluster.leader_id]
    for iteration in range(3):
        logger.info(f"\nIteration {iteration + 1}: Failing current leader...")
        current_leader = cluster.leader_id
        cluster.fail_node(current_leader)

        time.sleep(0.5)
        cluster.run_until_elected(max_steps=50, step_delay=0.05)
        new_leader = cluster.leader_id
        leaders_history.append(new_leader)

        print(f"  Leader: Node {current_leader} -> Node {new_leader}")

    print(f"\nLeadership history: {' -> '.join(map(str, leaders_history))}")


def example_programmatic_usage():
    """Example 4: Programmatic API usage."""
    print("\n" + "=" * 60)
    print("Example 4: Programmatic API Usage")
    print("=" * 60)

    logger = SimulationLogger(verbose=True)
    cluster = Cluster(num_nodes=6, logger=logger)

    # Start simulation
    cluster.start()
    print(f"\nCluster started with {cluster.num_nodes} nodes")

    # Run initial election
    print("\nRunning initial election...")
    cluster.run_until_elected(max_steps=50, step_delay=0.05)

    # Get and print cluster state
    state = cluster.get_cluster_state()
    print(f"\nCluster State:")
    print(f"  Leader: Node {state['leader_id']}")
    print(f"  Alive nodes: {state['alive_nodes']}/{state['total_nodes']}")
    print(f"  Election round: {state['election_round']}")

    # Simulate some operations
    print("\nSimulating node failures...")
    for node_id in [0, 1]:
        cluster.fail_node(node_id)
        print(f"  Failed Node {node_id}")

    state = cluster.get_cluster_state()
    print(f"  Alive nodes now: {state['alive_nodes']}/{state['total_nodes']}")

    # Get events
    events = cluster.get_events()
    print(f"\nTotal events logged: {len(events)}")
    print("Recent events:")
    for event in events[-3:]:
        print(f"  [{event['level']}] {event['message']}")


def example_verification():
    """Example 5: Verifying algorithm properties."""
    print("\n" + "=" * 60)
    print("Example 5: Algorithm Property Verification")
    print("=" * 60)

    logger = SimulationLogger(quiet=True)

    # Test 1: Single leader property
    print("\nTest 1: Only one leader at a time")
    cluster = Cluster(num_nodes=7, logger=logger)
    cluster.run_until_elected(max_steps=50, step_delay=0.05)

    leaders = [n for n in cluster.nodes if n.is_leader]
    print(f"  Leaders in cluster: {len(leaders)} (Expected: 1)")
    assert len(leaders) == 1, "Multiple leaders found!"
    print("  [PASS] Single leader invariant maintained")

    # Test 2: Leader consensus
    print("\nTest 2: All nodes agree on leader")
    leader_ids = set()
    for node in cluster.nodes:
        if node.is_alive():
            leader_ids.add(node.leader_id)

    print(f"  Unique leader IDs: {len(leader_ids)} (Expected: 1)")
    assert len(leader_ids) == 1, "Nodes disagree on leader!"
    print("  [PASS] Leader consensus maintained")

    # Test 3: Leader is highest ID
    print("\nTest 3: Leader has highest ID")
    leader_id = cluster.leader_id
    alive_ids = [n.node_id for n in cluster.nodes if n.is_alive()]
    highest_alive = max(alive_ids)

    print(f"  Leader ID: {leader_id}, Highest alive: {highest_alive}")
    assert leader_id == highest_alive, "Leader is not the highest ID!"
    print("  [PASS] Highest ID election property maintained")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Distributed Leader Election Simulator - Examples")
    print("(Bully Algorithm)")
    print("=" * 60)

    example_basic_election()
    time.sleep(1)

    example_leader_failure()
    time.sleep(1)

    example_cascading_failures()
    time.sleep(1)

    example_programmatic_usage()
    time.sleep(1)

    example_verification()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
