# Distributed Leader Election Simulator

A comprehensive simulation of distributed systems leader election using the **Bully Algorithm**. This project demonstrates how nodes in a distributed system coordinate to elect a leader when the current leader fails.

## Overview

The Bully Algorithm is a distributed consensus algorithm where:
- Each node has a unique ID (higher ID = higher priority)
- When a node detects the leader is down, it initiates an election
- The node with the highest ID wins the election
- Elected leaders broadcast their victory to all nodes with lower IDs

## Features

✅ **Bully Algorithm Implementation** - Full consensus mechanism  
✅ **Node Failure Detection** - Automatic failure detection and re-election  
✅ **Message Simulation** - Async message passing between nodes  
✅ **Comprehensive Logging** - Track all election rounds and state changes  
✅ **Unit Tests** - Validate election correctness  
✅ **CLI Interface** - Run simulations with configurable parameters  
✅ **Modular Design** - Clean separation of concerns  

## Algorithm Explanation

### How the Bully Algorithm Works

1. **Election Trigger**: When a node `P` detects the leader failure, it initiates an election by sending `ELECTION` messages to all nodes with higher IDs.

2. **Response Phase**: Any node receiving an `ELECTION` message responds with an `OK` message and starts its own election if it hasn't already.

3. **Victory**: If `P` receives no `OK` responses, it wins and becomes the leader, announcing victory with a `LEADER` message.

4. **Leader Announcement**: Any node winning becomes the leader and sends `LEADER` messages to all nodes with lower IDs.

### Time Complexity
- **Election Initiation**: O(n) messages
- **Election Resolution**: O(n²) in worst case (all nodes run election)
- **Message Passing**: O(n) per election round

## Project Structure

```
distributed-leader-election/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py
│   ├── node.py              # Node class with election logic
│   ├── message.py           # Message types and handling
│   ├── cluster.py           # Cluster management
│   └── logger.py            # Centralized logging
├── cli/
│   ├── __init__.py
│   └── simulator.py         # CLI interface
├── tests/
│   ├── __init__.py
│   ├── test_node.py         # Unit tests for nodes
│   ├── test_election.py     # Election algorithm tests
│   └── test_cluster.py      # Cluster integration tests
└── examples/
    └── run_example.py       # Example usage
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/distributed-leader-election.git
cd distributed-leader-election

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run the simulator
python -m cli.simulator
```

## Usage

### Basic CLI Usage

```bash
# Run with default settings (5 nodes)
python -m cli.simulator

# Run with custom number of nodes
python -m cli.simulator --nodes 10

# Run with failure scenario (leader fails after round 5)
python -m cli.simulator --nodes 8 --fail-leader-at 5

# Run with verbose logging
python -m cli.simulator --verbose

# Quiet mode (only summary)
python -m cli.simulator --quiet
```

### Programmatic Usage

```python
from src.cluster import Cluster
import time

# Create a cluster with 5 nodes
cluster = Cluster(num_nodes=5)

# Start the cluster
cluster.start()

# Simulate leader failure after 5 seconds
time.sleep(5)
cluster.fail_node(cluster.leader_id)

# Wait for new election
time.sleep(3)

# Get results
print(f"Current leader: {cluster.leader_id}")
print(f"Election history: {cluster.get_election_history()}")
```

### Example Output

```
[14:32:10] INFO: Starting simulation with 5 nodes
[14:32:10] INFO: Node 4 initiated election (leader failure detected)
[14:32:10] INFO: Election round started - nodes: [0, 1, 2, 3, 4]
[14:32:11] INFO: Node 4 elected as leader
[14:32:11] INFO: ✓ Election completed: Node 4 is the new leader
[14:32:15] INFO: Leader node 4 failed
[14:32:15] INFO: Node 3 detected leader failure, initiating election
[14:32:16] INFO: Node 3 elected as leader
[14:32:16] INFO: ✓ Election completed: Node 3 is the new leader
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_election.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Algorithm Complexity

| Metric | Value |
|--------|-------|
| **Best Case** | O(n) - elected node sends n messages |
| **Worst Case** | O(n²) - all nodes participate in election |
| **Average Case** | O(n²) |
| **Message Complexity** | O(n²) |
| **Time to Elect** | O(n) rounds |

## Design Decisions

1. **Python**: Chosen for readability and rapid prototyping. Easy to understand the algorithm without language overhead.

2. **Async Simulation**: Uses threading to simulate concurrent node behavior without blocking.

3. **Centralized Logging**: A dedicated logger captures all events for debugging and visualization.

4. **Modular Structure**: Each component (Node, Message, Cluster) is independent and testable.

## Limitations & Future Enhancements

### Current Limitations
- No network latency simulation
- Single-threaded event loop (no true concurrency)
- No persistence between runs
- No Byzantine fault tolerance

### Potential Enhancements
- [ ] Add network latency and packet loss simulation
- [ ] Implement Raft algorithm alternative
- [ ] GUI dashboard for real-time visualization
- [ ] Multi-threaded message passing
- [ ] Persistent state storage
- [ ] Byzantine fault tolerance
- [ ] Performance benchmarking

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- Garcia-Molina, H. (1982). "Elections in a Distributed Computing System"
- Tanenbaum, A. S. (2006). "Distributed Systems: Principles and Paradigms"
- [Bully Algorithm on Wikipedia](https://en.wikipedia.org/wiki/Bully_algorithm)

## Author

Created as an educational demonstration of distributed systems concepts.
