import pandas as pd

# Flight Path
DESTINATION_AIRPORT = (51.4, 0.5)
DEPARTURE_AIRPORT = (40.6, -73.7)
DEPARTURE_DATE = pd.Timestamp(year=2023, month=12, day=20, hour=2)
WEATHER_BOUND = pd.Timedelta("12h")
NO_OF_POINTS = 25
GRID_WIDTH = 5
GRID_SPACING = 100  # km

# ACO
EVAPORATION_RATE = 0.5
CO2_WEIGHT = 1
CONTRAIL_WEIGHT = 1
PHEROMONE_WEIGHT = 1
HEURISTIC_WEIGHT = 4
TAU_MIN = 1
TAU_MAX = 100
NO_OF_ANTS = 3
NO_OF_ITERATIONS = 1

# Aircraft
AIRCRAFT_TYPE = "A320"
ENGINE_TYPE = "CFM56-5B6"
N_ENGINES = 2
WINGSPAN = 64.75
INITIAL_THRUST = 0.5
ENGINE_EFFICIENCY = 0.3
STARTING_WEIGHT = 60000

# Search Constraints
FLIGHT_LEVELS = [310, 330, 350, 370, 390]
PRESSURE_LEVELS = (300, 250, 200)
STARTING_ALTITUDE = 31000
MAX_ALTITUDE = 39000
MAX_ALTITUDE_VAR = 2000
ALTITUDE_STEP = 2000
OFFSET_VAR = 1
