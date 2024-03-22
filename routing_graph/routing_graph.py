import networkx as nx
import os
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print


class RoutingGraph:
    def __init__(self, altitude_grid, performance_model, config, test=False):
        self.config = config
        self.altitude_grid = altitude_grid
        self.performance_model = performance_model
        self.routing_graph = self._init_routing_graph(test=test)
        self.nodes = self.routing_graph.nodes
        self.edges = self.routing_graph.edges

    def get_consecutive_points(
        self,
        xi,
        yi,
        altitude,
        grid,
    ):
        max_lateral_var = self.config.OFFSET_VAR
        max_altitude_var = self.config.MAX_ALTITUDE_VAR
        altitude_step = self.config.ALTITUDE_STEP
        max_alt = altitude + max_altitude_var
        max_alt = max(
            self.config.STARTING_ALTITUDE, min(max_alt, self.config.MAX_ALTITUDE)
        )

        points = []
        current_altitude = altitude
        while current_altitude <= max_alt:
            if xi + 1 == len(grid[current_altitude]):
                return None
            next_layer_length = len(grid[current_altitude][xi + 1]) - 1
            min_i = min(max(yi - max_lateral_var, 0), next_layer_length)
            max_i = min(yi + max_lateral_var, next_layer_length)
            for i in range(min_i, max_i + 1):
                points.append((xi + 1, i, current_altitude))
            current_altitude += altitude_step

        return points

    def calculate_routing_graph(self):
        graph = nx.DiGraph()

        altitude_grid = self.altitude_grid

        for altitude in altitude_grid:
            for step in altitude_grid[altitude]:
                for point in step:
                    if point is None:
                        continue

                    xi = altitude_grid[altitude].index(step)
                    yi = step.index(point)

                    consecutive_points = self.get_consecutive_points(
                        xi, yi, altitude, altitude_grid
                    )

                    heuristic_data = {
                        f"{objective(self.performance_model,self.config)}_heuristic": objective(
                            self.performance_model, self.config
                        ).calculate_heuristic((*point, altitude))
                        for objective in self.config.OBJECTIVES
                    }

                    if consecutive_points is None:
                        continue
                    if not graph.has_node((xi, yi, altitude)):
                        graph.add_node(
                            (xi, yi, altitude),
                            **heuristic_data,
                        )
                    for next_point in consecutive_points:
                        pheromone_data = {
                            f"{objective(self.performance_model,self.config)}_pheromone": self.config.TAU_MAX
                            for objective in self.config.OBJECTIVES
                        }
                        next_heuristic_data = {
                            f"{objective(self.performance_model,self.config)}_heuristic": objective(
                                self.performance_model, self.config
                            ).calculate_heuristic(next_point)
                            for objective in self.config.OBJECTIVES
                        }

                        graph.add_edge(
                            (xi, yi, altitude),
                            (next_point[0], next_point[1], next_point[2]),
                            **pheromone_data,
                        )
                        next_lat, next_lon, _ = next_point

                    if not graph.has_node(next_point):
                        graph.add_node(
                            (next_point[0], next_point[1], next_point[2]),
                            **next_heuristic_data,
                        )

        return graph

    def parse_node(self, s):
        # Assuming the input format is like '(0, 0, 31000)'
        parts = s.strip("()").split(",")
        return tuple(map(int, parts))

    def __getitem__(self, key):
        return self.routing_graph[key]

    def __setitem__(self, key, value):
        self.routing_graph[key] = value

    def _init_routing_graph(self, test=False):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Creating routing graph...", total=None)
            if os.path.exists("data/routing_graph.gml") and not test:
                rg = nx.read_gml("data/routing_graph.gml", destringizer=self.parse_node)
                self.routing_graph = rg
            else:
                rg = self.calculate_routing_graph()
                if not test:
                    nx.write_gml(rg, "data/routing_graph.gml")
                self.routing_graph = rg
        print("[bold green]:white_check_mark: Routing graph constructed.[/bold green]")
        return self.routing_graph
