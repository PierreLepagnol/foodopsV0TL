"""
Core package for FoodOps.

This package provides high‑level functions used during game setup
and orchestrates the simulation loop.  It exposes only the public
API; internal modules should not be imported directly by user code.
"""

from .setup import create_restaurants

__all__ = ["create_restaurants"]
