"""
Predefined scenarios for the FoodOps simulation.

Scenarios encapsulate the initial state of a game session, such as the
number of tours, the demand curve and available locals.  They are
intended to provide ready‑to‑play configurations for different
pedagogical contexts.
"""

from .default import DefaultScenario

__all__ = ["DefaultScenario"]
