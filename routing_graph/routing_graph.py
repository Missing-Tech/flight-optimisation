import networkx as nx
import pandas as pd
import util
import os


class RoutingGraph:
    def __init__(self, altitude_grid, contrail_grid, config):
        self.config = config
        self.altitude_grid = altitude_grid
        self.contrail_grid = contrail_grid

    def calculate_point_values(self, point, altitude):
        distance_from_departure = util.calculate_distance_between_points(
            self.config.DEPARTURE_AIRPORT,
            (point[0], point[1]),
        )
        speed = (
            self.config.NOMINAL_THRUST * 343
        )  # times by speed of sound for rough speed estimate
        time_to_point = distance_from_departure * 1000 / speed
        time_at_point = self.config.DEPARTURE_DATE + pd.Timedelta(time_to_point, "s")

        point_values = {
            "latitude": point[0],
            "longitude": point[1],
            "level": util.convert_altitude_to_pressure_bounded(altitude),
            "time": time_at_point,
            "delta_time": time_to_point,
            "fuel_burned": pd.Timedelta(time_to_point, "s").seconds
            * self.config.NOMINAL_FUEL_FLOW,
        }

        return point_values

    def calculate_routing_graph(self):
        graph = nx.DiGraph()

        altitude_grid = self.altitude_grid.get_altitude_grid()

        for altitude in altitude_grid:
            for step in altitude_grid[altitude]:
                for point in step:
                    if point is None:
                        continue

                    xi = altitude_grid[altitude].index(step)
                    yi = step.index(point)

                    consecutive_points = util.get_consecutive_points(
                        xi, yi, altitude, altitude_grid
                    )

                    point_values = self.calculate_point_values(point, altitude)
                    contrails_at_point = max(
                        self.contrail_grid.interpolate_contrail_point(
                            (*point, altitude)
                        ),
                        0.01,
                    )

                    if consecutive_points is None:
                        continue
                    for next_point in consecutive_points:
                        next_point_values = self.calculate_point_values(
                            next_point, next_point[2]
                        )
                        next_contrails_at_point = (
                            self.contrail_grid.interpolate_contrail_point(
                                (*next_point, next_point[2])
                            )
                        )

                        graph.add_edge(
                            (xi, yi, altitude),
                            (next_point[0], next_point[1], next_point[2]),
                            contrail_pheromone=self.config.TAU_MAX,
                            co2_pheromone=self.config.TAU_MAX,
                            time_pheromone=self.config.TAU_MAX,
                        )
                        graph.add_node(
                            (xi, yi, altitude),
                            contrail_heuristic=contrails_at_point,
                            co2_heuristic=point_values["fuel_burned"],
                            time_heuristic=point_values["delta_time"],
                        )
                        next_lat, next_lon, _ = next_point
                        graph.add_node(
                            next_point,
                            contrail_heuristic=next_contrails_at_point,
                            co2_heuristic=next_point_values["fuel_burned"],
                            time_heuristic=next_point_values["delta_time"],
                        )

        return graph

    def parse_node(self, s):
        # Assuming the input format is like '(0, 0, 31000)'
        parts = s.strip("()").split(",")
        return tuple(map(int, parts))

    def get_routing_graph(self):
        if os.path.exists("data/routing_graph.gml"):
            return nx.read_gml("data/routing_graph.gml", destringizer=self.parse_node)
        else:
            rg = self.calculate_routing_graph()
            nx.write_gml(rg, "data/routing_graph.gml")
            return rg
