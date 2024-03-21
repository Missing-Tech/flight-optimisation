import pandas as pd
from utils import Conversions
from datetime import datetime


class Flight:
    def __init__(self, routing_graph_manager, flight_path, config):
        self.routing_graph_manager = routing_graph_manager
        self.performance_model = routing_graph_manager.get_performance_model()
        self.flight_path = flight_path
        self.config = config
        self.indices = []
        self.objectives = None

    def set_departure(self, departure):
        self.add_point_from_index(departure)
        point = self.flight_path[0]
        point["time"] = self.config.DEPARTURE_DATE
        point["aircraft_mass"] = self.config.STARTING_WEIGHT
        self.flight_path[0] = point

    def run_performance_model(self):
        self.flight_path = self.performance_model.run_apm(self.flight_path)

    def add_point_from_index(self, index):
        self.indices.append(index)
        point = self.routing_graph_manager.convert_index_to_point(
            index,
        )
        self.flight_path.append(point)

    def set_objective_value(self, objective_values):
        self.objectives = objective_values


class RealFlight(Flight):
    def __init__(
        self,
        flight_name,
        routing_graph_manager,
        config,
    ):
        super().__init__(
            routing_graph_manager,
            [],
            config,
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
