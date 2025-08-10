from dataclasses import dataclass


@dataclass
class DefaultScenario:
    nb_tours: int = 12
    demand_per_tour: int = 1000
