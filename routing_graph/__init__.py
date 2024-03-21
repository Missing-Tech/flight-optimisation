from .routing_grid import RoutingGrid
from .altitude_grid import AltitudeGrid
from .geodesic_path import GeodesicPath
from .routing_graph import RoutingGraph


class RoutingGraphManager:
    def __init__(self, config):
        self.config = config

        self.geodesic_path = GeodesicPath(self.config)
        self.routing_grid = RoutingGrid(self.geodesic_path, self.config)
        self.altitude_grid = AltitudeGrid(self.routing_grid, self.config)

    def convert_index_to_point(self, index):
        return self.altitude_grid.convert_index_to_point(index)

    def get_routing_graph(self):
        if not hasattr(self, "routing_graph"):
            self.routing_graph = RoutingGraph(
                self.get_altitude_grid(), self.get_performance_model(), self.config
            )
        return self.routing_graph

    def set_performance_model(self, performance_model):
        self.performance_model = performance_model

    def get_performance_model(self):
        if not hasattr(self, "performance_model"):
            raise ValueError("Performance model not set")
        return self.performance_model

    def get_routing_grid(self):
        return self.routing_grid

    def get_altitude_grid(self):
        return self.altitude_grid

    def get_geodesic_path(self):
        return self.geodesic_path
