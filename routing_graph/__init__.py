from .routing_grid import RoutingGrid
from .altitude_grid import AltitudeGrid
from .geodesic_path import GeodesicPath
from .routing_graph import RoutingGraph

from config import Config
from _types import IndexPoint3D, FlightPoint
from performance_model import PerformanceModel


class RoutingGraphManager:
    def __init__(self, config: Config):
        """
        External interface for the routing graph and all its components
        """
        self.config: Config = config

        self.geodesic_path: GeodesicPath = GeodesicPath(self.config)
        self.routing_grid: RoutingGrid = RoutingGrid(self.geodesic_path, self.config)
        self.altitude_grid: AltitudeGrid = AltitudeGrid(self.routing_grid, self.config)

    def convert_index_to_point(self, index: IndexPoint3D) -> FlightPoint:
        """
        Converts an IndexPoint to a FlightPoint
        """
        return self.altitude_grid.convert_index_to_point(index)

    def get_routing_graph(self) -> RoutingGraph:
        """
        Retrieves the routing graph, or creates it if it doesn't exist
        """
        if not hasattr(self, "routing_graph"):
            self.routing_graph = RoutingGraph(
                self.get_altitude_grid(), self.get_performance_model(), self.config
            )
        return self.routing_graph

    def set_performance_model(self, performance_model: PerformanceModel) -> None:
        """
        Sets the performance model for the routing graph
        """
        self.performance_model: PerformanceModel = performance_model

    def get_performance_model(self) -> PerformanceModel:
        """
        Retrieves the performance model
        """
        if not hasattr(self, "performance_model"):
            raise ValueError("Performance model not set")
        return self.performance_model

    def get_routing_grid(self) -> RoutingGrid:
        """
        Retrieves the routing grid
        """
        return self.routing_grid

    def get_altitude_grid(self) -> AltitudeGrid:
        """
        Retrieves the altitude grid
        """
        return self.altitude_grid

    def get_geodesic_path(self) -> GeodesicPath:
        """
        Retrieves the geodesic path
        """
        return self.geodesic_path
