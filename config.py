import pandas as pd
from objectives import ContrailObjective, CO2Objective, TimeObjective, CocipObjective

import typing

if typing.TYPE_CHECKING:
    from _types import Point2D
    from objectives import Objective


class Config:
    NAME: str = "overall"
    # Flight Path
    DEPARTURE_AIRPORT: "Point2D" = (50.74045, -3.00313)
    DESTINATION_AIRPORT: "Point2D" = (
        41.82151,
        -71.12919,
    )  # ToD for the real flight path
    DEPARTURE_DATE: pd.Timestamp = pd.Timestamp(
        year=2024, month=1, day=31, hour=13, minute=45, second=57
    )
    WEATHER_BOUND: pd.Timedelta = (
        pd.Timedelta("12h") - pd.Timedelta("45m") - pd.Timedelta("57s")
    )
    NO_OF_POINTS: int = 10
    GRID_WIDTH: int = 40
    GRID_SPACING: int = 20  # km

    # ACO
    EVAPORATION_RATE: float = 0.3
    CO2_WEIGHT: float = 1
    CONTRAIL_WEIGHT: float = 1
    TIME_WEIGHT: float = 1
    PHEROMONE_WEIGHT: float = 2
    HEURISTIC_WEIGHT: float = 1
    TAU_MIN: float = 0.1
    TAU_MAX: float = 1
    NO_OF_ANTS: int = 8
    NO_OF_ITERATIONS: int = 1

    # Aircraft
    AIRCRAFT_TYPE: str = "B77W"
    N_ENGINES: int = 4
    WINGSPAN: float = 60.920
    STARTING_WEIGHT: float = 240000
    NOMINAL_ENGINE_EFFICIENCY: float = 0.33
    NOMINAL_FUEL_FLOW: float = 1.8

    # Search Constraints
    FLIGHT_LEVELS: list[int] = [310, 330, 350, 370, 390]
    PRESSURE_LEVELS: list[int] = [300, 250, 200]
    STARTING_ALTITUDE: float = 31000
    INITIAL_THRUST: float = 0.83
    MAX_THRUST_VAR: float = 0.01
    MAX_THRUST: float = 0.83
    NOMINAL_THRUST: float = 0.83
    MAX_ALTITUDE: int = 39000
    MAX_ALTITUDE_VAR: int = 4000
    ALTITUDE_STEP: int = 2000
    OFFSET_VAR: int = 20

    # Objective Functions
    OBJECTIVES: list["Objective"] = [ContrailObjective, CO2Objective, TimeObjective]

    # Earth radius in km
    R: int = 6371


# Uses gridded CoCiP data
class ContrailConfig(Config):
    NAME: str = "contrail"
    OBJECTIVES: list["Objective"] = [ContrailObjective]
    CONTRAIL_WEIGHT: float = 1


class CocipConfig(Config):
    NAME: str = "cocip"
    OBJECTIVES: list["Objective"] = [CocipObjective, CO2Objective, TimeObjective]
    CONTRAIL_WEIGHT: float = 1


class CO2Config(Config):
    NAME: str = "co2"
    OBJECTIVES: list["Objective"] = [CO2Objective]
    CO2_WEIGHT: float = 1


class TimeConfig(Config):
    NAME: str = "time"
    OBJECTIVES: list["Objective"] = [TimeObjective]
    TIME_WEIGHT: float = 1


class ContrailMaxConfig(Config):
    NAME: str = "contrail_max"
    OBJECTIVES: list["Objective"] = [ContrailObjective]
    CONTRAIL_WEIGHT: float = -10
