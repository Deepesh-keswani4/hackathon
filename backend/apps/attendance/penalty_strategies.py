"""
Penalty calculation strategies (Strategy pattern).
Swappable via AttendancePolicy.penalty_order without changing callers.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import List

logger = logging.getLogger("hrms")


@dataclass
class PenaltySlice:
    leave_type: str   # "PL" or "LOP"
    days: Decimal


class BasePenaltyStrategy(ABC):
    @abstractmethod
    def calculate(self, total_days: Decimal, pl_available: Decimal) -> List[PenaltySlice]:
        """
        Return ordered slices that should be deducted.
        total_days = days to penalize (usually 1.0).
        pl_available = current PL balance for the employee.
        """


class PLThenLOPStrategy(BasePenaltyStrategy):
    """Deduct PL first; if PL exhausted, remainder becomes LOP."""

    def calculate(self, total_days: Decimal, pl_available: Decimal) -> List[PenaltySlice]:
        slices: List[PenaltySlice] = []
        remaining = total_days

        pl_deduct = min(pl_available, remaining)
        if pl_deduct > 0:
            slices.append(PenaltySlice(leave_type="PL", days=pl_deduct))
            remaining -= pl_deduct

        if remaining > 0:
            slices.append(PenaltySlice(leave_type="LOP", days=remaining))

        return slices


class LOPOnlyStrategy(BasePenaltyStrategy):
    """Always deduct LOP regardless of PL balance (future use)."""

    def calculate(self, total_days: Decimal, pl_available: Decimal) -> List[PenaltySlice]:
        return [PenaltySlice(leave_type="LOP", days=total_days)]


class PenaltyStrategyFactory:
    _REGISTRY = {
        "PL": PLThenLOPStrategy,   # penalty_order starts with PL → PLThenLOP
        "LOP": LOPOnlyStrategy,    # penalty_order starts with LOP → LOPOnly
    }

    @classmethod
    def get(cls, penalty_order: list) -> BasePenaltyStrategy:
        """
        penalty_order is e.g. ["PL", "LOP"] from AttendancePolicy.
        First element drives strategy selection.
        """
        first = (penalty_order or ["PL"])[0]
        strategy_cls = cls._REGISTRY.get(first, PLThenLOPStrategy)
        logger.debug("PenaltyStrategyFactory selected %s for order=%s", strategy_cls.__name__, penalty_order)
        return strategy_cls()

    @classmethod
    def register(cls, key: str, strategy_cls: type) -> None:
        """Extension point — register new strategies without modifying this file."""
        cls._REGISTRY[key] = strategy_cls
