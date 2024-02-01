import networkx as nx
import random
import util
import numpy as np


def calculate_routing_graph(altitude_grid):
    graph = nx.DiGraph()
    for altitude in altitude_grid:
        for step in altitude_grid[altitude]:
            for point in step:

                xi = altitude_grid[altitude].index(step)
                yi = step.index(point)

                consecutive_points = util.get_consecutive_points(
                    xi, yi, altitude, altitude_grid
                )

                if consecutive_points is None:
                    continue
                for next_point in consecutive_points:
                    graph.add_edge(
                        (xi, yi, altitude),
                        (next_point[0], next_point[1], next_point[2]),
                        pheromone=10,
                    )
                    graph.add_node((xi, yi, altitude), heuristic=0.5)
                    graph.add_node(next_point, heuristic=0.5)

    return graph
