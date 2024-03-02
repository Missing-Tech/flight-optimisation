import pandas as pd

# Flight Path
DEPARTURE_AIRPORT = (50.74045, -3.00313)
DESTINATION_AIRPORT = (41.59918, -71.57000)
DEPARTURE_DATE = pd.Timestamp(year=2024, month=1, day=31, hour=13)
WEATHER_BOUND = pd.Timedelta("12h")
NO_OF_POINTS = 25
GRID_WIDTH = 10
GRID_SPACING = 100  # km

# ACO
EVAPORATION_RATE = 0.8
CO2_WEIGHT = 0
CONTRAIL_WEIGHT = 0
TIME_WEIGHT = 1
PHEROMONE_WEIGHT = 1
HEURISTIC_WEIGHT = 1
TAU_MIN = 0
TAU_MAX = 1
NO_OF_ANTS = 50
NO_OF_ITERATIONS = 50
NO_OF_PROCESSES = 6

# Aircraft
AIRCRAFT_TYPE = "B772"
N_ENGINES = 2
WINGSPAN = 60.93
STARTING_WEIGHT = 240000
NOMINAL_ENGINE_EFFICIENCY = 0.33
NOMINAL_FUEL_FLOW = 1.747

# Search Constraints
FLIGHT_LEVELS = [310, 330, 350, 370, 390]
PRESSURE_LEVELS = (300, 250, 200)
STARTING_ALTITUDE = 31000
INITIAL_THRUST = 0.8
MAX_THRUST_VAR = 0.05
MAX_THRUST = 0.85
MAX_ALTITUDE = 39000
MAX_ALTITUDE_VAR = 2000
ALTITUDE_STEP = 2000
OFFSET_VAR = 1
