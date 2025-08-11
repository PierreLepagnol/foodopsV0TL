# foodops/data/__init__.py
def get_DEFAULT_MENUS():
    from .menus_presets_simple import get_default_menus_simple

    return get_default_menus_simple()


# Si tu exposes déjà d'autres données (CLIENT_PROFILES, etc.), garde-les ici comme avant.

"""
Point d'entrée data avec imports retardés pour éviter les boucles.
Expose des getters plutôt que des objets globaux calculés au chargement.
"""


def get_DEFAULT_MENUS():
    from .menus_presets_simple import get_default_menus_simple

    return get_default_menus_simple()


def get_INGREDIENT_PRICES():
    from .ingredient_prices import INGREDIENT_PRICES

    return INGREDIENT_PRICES


def get_CLIENT_PROFILES():
    # import direct (pas de dépendance domaine)
    from .profiles import CLIENT_PROFILES

    return CLIENT_PROFILES


def get_SEGMENT_WEIGHTS():
    from .profiles import SEGMENT_WEIGHTS

    return SEGMENT_WEIGHTS
