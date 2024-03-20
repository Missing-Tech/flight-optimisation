import pandas as pd


class Config:
    # Flight Path
    DEPARTURE_AIRPORT = (50.74045, -3.00313)
    DESTINATION_AIRPORT = (41.59918, -71.57000)
    DEPARTURE_DATE = pd.Timestamp(
        year=2024, month=1, day=31, hour=13, minute=45, second=57
    )
    WEATHER_BOUND = pd.Timedelta("12h") - pd.Timedelta("45m") - pd.Timedelta("57s")
    NO_OF_POINTS = 10
    GRID_WIDTH = 40
    GRID_SPACING = 20  # km

    # ACO
    EVAPORATION_RATE = 0.5
    CO2_WEIGHT = 1
    CONTRAIL_WEIGHT = 1
    TIME_WEIGHT = 1
    PHEROMONE_WEIGHT = 4
    HEURISTIC_WEIGHT = 1
    TAU_MIN = 0.1
    TAU_MAX = 1
    NO_OF_ANTS = 8
    NO_OF_ITERATIONS = 100

    # Aircraft
    AIRCRAFT_TYPE = "B772"
    N_ENGINES = 4
    WINGSPAN = 60.920
    STARTING_WEIGHT = 240000
    NOMINAL_ENGINE_EFFICIENCY = 0.33
    NOMINAL_FUEL_FLOW = 1.8

    # Search Constraints
    FLIGHT_LEVELS = [310, 330, 350, 370, 390]
    PRESSURE_LEVELS = (300, 250, 200)
    STARTING_ALTITUDE = 31000
    INITIAL_THRUST = 0.83
    MAX_THRUST_VAR = 0.01
    MAX_THRUST = 0.83
    NOMINAL_THRUST = 0.83
    MAX_ALTITUDE = 39000
    MAX_ALTITUDE_VAR = 2000
    ALTITUDE_STEP = 2000
    OFFSET_VAR = 16


class ContrailMaxConfig(Config):
    CONTRAIL_WEIGHT = -1
    CO2_WEIGHT = 0
    TIME_WEIGHT = 0
