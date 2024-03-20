from routing_graph import RoutingGraph, RoutingGrid, AltitudeGrid, GeodesicPath


class RoutingGraphManager:
    def __init__(self, destination, departure):
        self.destination = destination
        self.departure = departure

        self.geodesic_path = GeodesicPath(departure, destination)
        self.routing_grid = RoutingGrid(self.geodesic_path)
        self.altitude_grid = AltitudeGrid(self.routing_grid)

    def get_routing_graph(self, contrail_grid):
        self.routing_graph = RoutingGraph(self.altitude_grid, contrail_grid)
        return self.routing_graph.get_routing_graph()

    def get_routing_grid(self):
        return self.routing_grid.get_routing_grid()

    def get_altitude_grid(self):
        return self.altitude_grid.get_altitude_grid()

    def get_geodesic_path(self):
        return self.geodesic_path.get_geodesic_path()
