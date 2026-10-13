"""CLI interface for the distributed leader election simulator."""

import argparse
import time
import sys
from src.cluster import Cluster
from src.logger import SimulationLogger


def print_banner():
    """Print welcome banner."""
    banner = """
====================================================
  Distributed Leader Election Simulator
  (Bully Algorithm)
====================================================
"""
    print(banner)


def run_interactive_simulation(args):
    """Run an interactive simulation."""
    print_banner()

    logger = SimulationLogger(verbose=args.verbose, quiet=args.quiet)
    cluster = Cluster(num_nodes=args.nodes, logger=logger)
    cluster.start()

    logger.info(f"Starting simulation with {args.nodes} nodes")
    logger.info(f"Initial leader: Node {cluster.leader_id}")

    # Run initial election
    logger.info("\n--- Initial Election Phase ---")
    cluster.run_until_elected(max_steps=50, step_delay=0.05)

    # Simulate failure scenarios
    if args.fail_leader_at and args.fail_leader_at > 0:
        logger.info(f"\n--- Waiting {args.fail_leader_at} seconds before leader failure ---")
        time.sleep(args.fail_leader_at)

        logger.info("\n--- Leader Failure Scenario ---")
        current_leader = cluster.leader_id
        logger.info(f"Failing leader Node {current_leader}...")
        cluster.fail_node(current_leader)

        logger.info("\n--- Re-election Phase ---")
        cluster.run_until_elected(max_steps=50, step_delay=0.05)

    # Print final state
    cluster.print_state()
    logger.print_summary()

    # Print detailed election history if verbose
    if args.verbose:
        print("\nDetailed Event Log:")
        for i, event in enumerate(logger.get_events(), 1):
            print(f"  {i}. [{event['level']}] {event['message']}")


def run_automated_scenarios(args):
    """Run predefined test scenarios."""
    scenarios = [
        {
            "name": "Scenario 1: Initial Election",
            "nodes": 5,
            "failures": [],
            "duration": 3,
        },
        {
            "name": "Scenario 2: Leader Failure & Recovery",
            "nodes": 7,
            "failures": [("fail", 3, 6)],  # (action, node_id, timestamp)
            "duration": 8,
        },
        {
            "name": "Scenario 3: Multiple Failures",
            "nodes": 10,
            "failures": [("fail", 9, 2), ("fail", 8, 4), ("recover", 9, 6)],
            "duration": 10,
        },
    ]

    print_banner()

    for scenario in scenarios:
        print(f"\n{'=' * 60}")
        print(f"{scenario['name']}")
        print(f"{'=' * 60}")

        logger = SimulationLogger(verbose=args.verbose, quiet=False)
        cluster = Cluster(num_nodes=scenario["nodes"], logger=logger)
        cluster.start()

        logger.info(f"Running: {scenario['name']}")
        logger.info(f"Initial leader: Node {cluster.leader_id}")

        # Run initial election
        cluster.run_until_elected(max_steps=50, step_delay=0.05)

        # Process scenario events
        start_time = time.time()
        for action, node_id, timestamp in scenario["failures"]:
            # Wait until event time
            while time.time() - start_time < timestamp:
                cluster.simulate_step(0.05)
                time.sleep(0.05)

            if action == "fail":
                logger.info(f"Event: Failing Node {node_id}")
                cluster.fail_node(node_id)
                cluster.run_until_elected(max_steps=50, step_delay=0.05)
            elif action == "recover":
                logger.info(f"Event: Recovering Node {node_id}")
                cluster.recover_node(node_id)

        # Continue simulation until end
        while time.time() - start_time < scenario["duration"]:
            cluster.simulate_step(0.05)
            time.sleep(0.05)

        cluster.print_state()
        logger.print_summary()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Distributed Leader Election Simulator using Bully Algorithm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic simulation with 5 nodes
  python -m cli.simulator

  # Simulation with 10 nodes
  python -m cli.simulator --nodes 10

  # Leader fails after 3 seconds
  python -m cli.simulator --nodes 8 --fail-leader-at 3

  # Run automated test scenarios
  python -m cli.simulator --scenarios

  # Verbose output with debug info
  python -m cli.simulator --verbose

  # Quiet mode (no output except summary)
  python -m cli.simulator --quiet
        """,
    )

    parser.add_argument(
        "--nodes",
        type=int,
        default=5,
        help="Number of nodes in the cluster (default: 5)",
    )

    parser.add_argument(
        "--fail-leader-at",
        type=float,
        default=0,
        help="Seconds before leader failure (0 = no failure)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except summary",
    )

    parser.add_argument(
        "--scenarios",
        action="store_true",
        help="Run predefined test scenarios",
    )

    args = parser.parse_args()

    try:
        if args.scenarios:
            run_automated_scenarios(args)
        else:
            run_interactive_simulation(args)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
