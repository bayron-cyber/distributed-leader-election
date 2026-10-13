"""Centralized logging for the distributed election system."""

import logging
from datetime import datetime
from typing import List
from enum import Enum


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class SimulationLogger:
    """Centralized logger for election simulation events."""

    def __init__(self, verbose: bool = True, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet
        self.events: List[dict] = []
        self.election_rounds: List[dict] = []

        # Configure logging
        self.logger = logging.getLogger("ElectionSimulator")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        if not quiet:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str) -> None:
        """Log info level message."""
        if not self.quiet:
            self.logger.info(message)
        self._record_event("INFO", message)

    def warning(self, message: str) -> None:
        """Log warning level message."""
        if not self.quiet:
            self.logger.warning(message)
        self._record_event("WARNING", message)

    def error(self, message: str) -> None:
        """Log error level message."""
        if not self.quiet:
            self.logger.error(message)
        self._record_event("ERROR", message)

    def debug(self, message: str) -> None:
        """Log debug level message."""
        if self.verbose and not self.quiet:
            self.logger.debug(message)
        self._record_event("DEBUG", message)

    def _record_event(self, level: str, message: str) -> None:
        """Record event in history."""
        self.events.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
        })

    def log_election_round(self, round_num: int, elected_leader: int, participants: List[int]) -> None:
        """Log a completed election round."""
        self.election_rounds.append({
            "round": round_num,
            "elected_leader": elected_leader,
            "participants": participants,
            "timestamp": datetime.now().isoformat(),
        })

    def get_events(self) -> List[dict]:
        """Get all recorded events."""
        return self.events.copy()

    def get_election_history(self) -> List[dict]:
        """Get election round history."""
        return self.election_rounds.copy()

    def print_summary(self) -> None:
        """Print a summary of the simulation."""
        if self.quiet:
            return

        print("\n" + "=" * 60)
        print("SIMULATION SUMMARY")
        print("=" * 60)
        print(f"Total Events: {len(self.events)}")
        print(f"Election Rounds: {len(self.election_rounds)}")

        if self.election_rounds:
            print("\nElection History:")
            for round_data in self.election_rounds:
                print(
                    f"  Round {round_data['round']}: "
                    f"Leader = Node {round_data['elected_leader']}, "
                    f"Participants = {len(round_data['participants'])}"
                )

        print("=" * 60 + "\n")
