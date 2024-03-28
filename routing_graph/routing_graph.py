from networkx import DiGraph, read_gml, write_gml
from networkx.classes.reportviews import NodeView, EdgeView
import os
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
import typing

if typing.TYPE_CHECKING:
    from config import Config
    from performance_model import PerformanceModel
    from .altitude_grid import AltitudeGrid
    from _types import IndexPoint3D, Grid3D


class RoutingGraph:
    def __init__(
        self,
        altitude_grid: "AltitudeGrid",
        performance_model: "PerformanceModel",
        config: "Config",
        test: bool = False,
    ):
        """
        Create a RoutingGraph object
        """
        self.config: "Config" = config
        self.altitude_grid: "AltitudeGrid" = altitude_grid
        self.performance_model: "PerformanceModel" = performance_model
        self.routing_graph: DiGraph = self._init_routing_graph(test=test)
        self.nodes: NodeView = self.routing_graph.nodes
        self.edges: EdgeView = self.routing_graph.edges

    def get_consecutive_points(
        self,
        point: "IndexPoint3D",
        grid: "Grid3D",
    ) -> list["IndexPoint3D"] or None:
        """
        Get a list of consecutive points from the current position
        """

        xi, yi, altitude = point
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

    def calculate_routing_graph(self) -> DiGraph:
        """
        Calculates a full routing graph from an altitude grid
        """
        graph = DiGraph()

        altitude_grid = self.altitude_grid

        for altitude in altitude_grid:
            for step in altitude_grid[altitude]:
                for point in step:
                    if point is None:
                        continue

                    xi = altitude_grid[altitude].index(step)
                    yi = step.index(point)

                    consecutive_points = self.get_consecutive_points(
                        (xi, yi, altitude), altitude_grid
                    )

                    heuristic_data = {
                        f"{objective(self.performance_model,self.config)}_heuristic": objective(
                            self.performance_model, self.config
                        ).calculate_heuristic((*point, altitude))
                        for objective in self.config.OBJECTIVES
                    }

                    if consecutive_points is None:
                        continue
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

                        graph.add_node(
                            (next_point[0], next_point[1], next_point[2]),
                            **next_heuristic_data,
                        )

        return graph

    def parse_node(self, s: str) -> "IndexPoint3D":
        """
        Parses a GML node into an IndexPoint3D
        """
        parts = s.strip("()").split(",")
        return tuple(map(int, parts))

    def __getitem__(self, key: "IndexPoint3D") -> NodeView:
        return self.routing_graph[key]

    def _init_routing_graph(self, test: bool = False) -> DiGraph:
        """
        Retrieves the routing graph from a file or calculates it
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Creating routing graph...", total=None)
            if os.path.exists("data/routing_graph.gml") and not test:
                rg = read_gml("data/routing_graph.gml", destringizer=self.parse_node)
                self.routing_graph = rg
            else:
                rg = self.calculate_routing_graph()
                if not test:
                    write_gml(rg, "data/routing_graph.gml")
                self.routing_graph = rg
        print("[bold green]:white_check_mark: Routing graph constructed.[/bold green]")
        return self.routing_graph
