"""
Domain objects for FoodOps.

The domain layer holds the core business objects that model
restaurants, locals (locations), ingredients, recipes and employees.
These classes are plain dataclasses where possible to ease unit
testing and avoid any side effects.
"""

from .restaurant import Restaurant
from .types import RestaurantType
from .local import Local
from .recipe import Recipe
from .scenario import Scenario

__all__ = ["Restaurant", "RestaurantType", "Local", "Recipe", "Scenario"]
