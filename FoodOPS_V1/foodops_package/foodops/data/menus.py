from ..domain.menu import Recipe
from ..domain.restaurant import RestaurantType

DEFAULT_MENUS = {
    RestaurantType.FAST_FOOD: [
        Recipe("Burger", 9.0, 0.60),
        Recipe("Frites", 4.0, 0.55),
        Recipe("Wrap", 8.0, 0.65),
    ],
    RestaurantType.BISTRO: [
        Recipe("Plat du jour", 14.0, 0.68),
        Recipe("Salade", 12.0, 0.62),
        Recipe("Pasta", 13.0, 0.66),
    ],
    RestaurantType.GASTRO: [
        Recipe("Menu dégustation", 45.0, 0.85),
        Recipe("Plat signature", 32.0, 0.80),
        Recipe("Entrée", 18.0, 0.78),
    ],
}
