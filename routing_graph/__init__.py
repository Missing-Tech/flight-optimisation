class RoutingGraphManager:
    def __init__(self, config):
        from routing_graph import RoutingGrid, AltitudeGrid, GeodesicPath

        self.config = config

        self.geodesic_path = GeodesicPath(self.config)
        self.routing_grid = RoutingGrid(self.geodesic_path, self.config)
        self.altitude_grid = AltitudeGrid(self.routing_grid, self.config)

    def get_routing_graph(self, contrail_grid):
        from routing_graph import RoutingGraph

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
