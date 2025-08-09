
"""
Domain objects for FoodOps.

The domain layer holds the core business objects that model
restaurants, locals (locations), ingredients, recipes and employees.
These classes are plain dataclasses where possible to ease unit
testing and avoid any side effects.
"""

from .restaurant import Restaurant, RestaurantType
from .local import Local
from .recipe import Recipe
__all__ = ["Restaurant", "RestaurantType", "Local", "Recipe"]
