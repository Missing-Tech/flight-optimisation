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

    def get_routing_graph(self, contrail_grid):
        self.routing_graph = RoutingGraph(
            self.altitude_grid, contrail_grid, self.config
        )
        return self.routing_graph.get_routing_graph()

    def get_routing_grid(self):
        return self.routing_grid.get_routing_grid()

    def get_altitude_grid(self):
        return self.altitude_grid.get_altitude_grid()

    def get_geodesic_path(self):
        return self.geodesic_path.get_geodesic_path()
