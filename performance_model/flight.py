import random
import pandas as pd
from utils import Conversions
import typing

if typing.TYPE_CHECKING:
    from routing_graph import RoutingGraphManager
    from _types import FlightPath, IndexPath, Objectives, IndexPoint3D
    from config import Config
    from performance_model import PerformanceModel


class Flight:
    def __init__(
        self,
        routing_graph_manager: "RoutingGraphManager",
        flight_path: "FlightPath",
        config: "Config",
    ):
        """
        Class to hold a flight path and relevant objective information
        """
        self.routing_graph_manager: "RoutingGraphManager" = routing_graph_manager
        self.performance_model: "PerformanceModel" = (
            routing_graph_manager.get_performance_model()
        )
        self.flight_path: "FlightPath" = flight_path
        self.config: "Config" = config
        self.indices: "IndexPath" = []
        self.objectives: "Objectives" or None = None

    def set_departure(self, departure: "IndexPoint3D") -> None:
        """
        Sets the departure point for the flight path
        """
        self.add_point_from_index(departure)
        point = self.flight_path[0]
        point["time"] = self.config.DEPARTURE_DATE
        point["aircraft_mass"] = self.config.STARTING_WEIGHT
        self.flight_path[0] = point

    def run_performance_model(self) -> None:
        """
        Runs the performance model on the flight path
        """
        self.flight_path = self.performance_model.run_apm(self.flight_path)

    def add_point_from_index(self, index: "IndexPoint3D") -> None:
        """
        Adds an index point to the index path
        """
        self.indices.append(index)
        point = self.routing_graph_manager.convert_index_to_point(
            index,
        )
        self.flight_path.append(point)

    def calculate_objectives(self) -> "Objectives":
        """
        Calculates the objective values for this flight path
        """
        objectives = {}
        for objective in self.config.OBJECTIVES:
            objective = objective(self.performance_model, self.config)
            objective_name = str(objective)
            objective_value = objective._run_objective_function(self.flight_path)
            objectives[objective_name] = objective_value

        self.objectives = objectives
        return objectives


class RealFlight(Flight):
    def __init__(
        self,
        flight_name: str,
        routing_graph_manager: "RoutingGraphManager",
        config: "Config",
    ):
        super().__init__(
            routing_graph_manager,
            [],
            config,
        )
        self.flight_path = pd.read_csv(f"data/{flight_name}")
        self.flight_path: "FlightPath" = self.convert_real_flight_path()
        self.config: "Config" = config

    def convert_real_flight_path(self) -> "FlightPath":
        """
        Converts a dataframe of a real flight path to a list of dictionaries
        """
        path = []
        for _, row in self.flight_path.iterrows():
            path_point = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "altitude_ft": row["altitude_ft"],
                "thrust": self.config.NOMINAL_THRUST,
                "time": row["time"],
                "level": Conversions().convert_altitude_to_pressure_bounded(
                    row["altitude_ft"],
                    self.config.PRESSURE_LEVELS[-1],
                    self.config.PRESSURE_LEVELS[0],
                ),
            }

            path.append(path_point)

        return path


class RandomFlight(Flight):
    def __init__(self, routing_graph_manager, config):
        super().__init__(
            routing_graph_manager,
            [],
            config,
        )
        self.routing_graph_manager = routing_graph_manager
        self.routing_graph = routing_graph_manager.get_routing_graph()
        self.config = config

    def construct_random_flight(self):
        self.set_departure((0, self.config.GRID_WIDTH, self.config.STARTING_ALTITUDE))
        consecutive_points = self.routing_graph[self.indices[0]]

        while consecutive_points != {}:
            choice = random.choice(list(consecutive_points))
            self.add_point_from_index(choice)
            consecutive_points = self.routing_graph[choice]

        return self.flight_path
