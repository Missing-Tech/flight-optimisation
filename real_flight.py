import pandas as pd
import util
from flight import Flight


class RealFlight(Flight):
    def __init__(self, flight_name, weather_grid, performance_model):
        flight_path = pd.read_csv(f"data/{flight_name}")
        flight_path = flight_path[flight_path["AltMSL"] > 30000]
        flight_path = util.convert_real_flight_path(flight_path, weather_grid)
        self.flight_path = performance_model.calculate_flight_characteristics(
            flight_path
        )
