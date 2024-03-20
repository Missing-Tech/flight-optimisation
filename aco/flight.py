import pandas as pd
from utils import Conversions
from datetime import datetime


class Flight:
    def __init__(
        self, altitude_grid, routing_graph, performance_model, config, flight_path
    ):
        self.altitude_grid = altitude_grid
        self.routing_graph = routing_graph
        self.performance_model = performance_model
        self.flight_path = flight_path
        self.config = config
        self.indices = []
        self.objectives = None

    def set_departure(self, departure):
        self.indices.append(departure)
        point = self.convert_index_to_point(
            departure,
            self.altitude_grid,
        )
        point["time"] = self.config.DEPARTURE_DATE
        point["aircraft_mass"] = self.config.STARTING_WEIGHT
        self.flight_path.append(point)

    def run_performance_model(self):
        self.flight_path = self.performance_model.calculate_flight_characteristics(
            self.flight_path
        )

    def add_point_from_index(self, index):
        self.indices.append(index)
        point = self.convert_index_to_point(
            index,
            self.altitude_grid,
        )
        self.flight_path.append(point)

    def set_objective_value(self, objective_values):
        self.objectives = objective_values

    def convert_index_to_point(self, index, altitude_grid):
        thrust = self.config.NOMINAL_THRUST
        altitude_point = altitude_grid[index[2]][index[0]][index[1]]
        path_point = {
            "latitude": altitude_point[0],
            "longitude": altitude_point[1],
            "altitude_ft": index[2],
            "thrust": thrust,
            "level": Conversions().convert_altitude_to_pressure_bounded(
                index[2],
                self.config.PRESSURE_LEVELS[-1],
                self.config.PRESSURE_LEVELS[0],
            ),
        }
        return path_point


class RealFlight(Flight):
    def __init__(
        self,
        flight_name,
        altitude_grid,
        routing_graph,
        performance_model,
        config,
    ):
        super().__init__(
            altitude_grid,
            routing_graph,
            performance_model,
            config,
            [],
        )
        flight_path = pd.read_csv(f"data/{flight_name}")
        self.flight_path = flight_path[flight_path["AltMSL"] > 30000]
        self.flight_path = self.convert_real_flight_path()
        self.config = config

    def convert_real_flight_path(self):
        path = []
        for _, row in self.flight_path.iterrows():
            time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M:%S")
            path_point = {
                "latitude": row["Latitude"],
                "longitude": row["Longitude"],
                "altitude_ft": row["AltMSL"],
                "thrust": self.config.NOMINAL_THRUST,
                "time": time,
                "level": Conversions().convert_altitude_to_pressure_bounded(
                    row["AltMSL"],
                    self.config.PRESSURE_LEVELS[-1],
                    self.config.PRESSURE_LEVELS[0],
                ),
            }

            path.append(path_point)

        return path
