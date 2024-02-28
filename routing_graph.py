import networkx as nx
import config
import contrails as ct
import util
import os
import altitude_grid as ag


def calculate_routing_graph(altitude_grid, contrail_grid):
    graph = nx.DiGraph()

    for altitude in altitude_grid:
        for step in altitude_grid[altitude]:
            for point in step:
                if point is None:
                    continue

                contrails = (
                    -(
                        ct.interpolate_contrail_point(contrail_grid, (*point, altitude))
                        / 1e12
                    )
                    - 1
                )

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
                        pheromone=config.TAU_MAX,
                    )
                    graph.add_node((xi, yi, altitude), heuristic=contrails)
                    graph.add_node(next_point, heuristic=contrails)

    return graph


def parse_node(s):
    # Assuming the input format is like '(0, 0, 31000)'
    parts = s.strip("()").split(",")
    return tuple(map(int, parts))


def get_routing_graph():
    if os.path.exists("data/routing_graph.gml"):
        return nx.read_gml("data/routing_graph.gml", destringizer=parse_node)
    else:
        rg = calculate_routing_graph(
            ag.get_altitude_grid(),
            ct.get_contrail_grid(),
        )
        nx.write_gml(rg, "data/routing_graph.gml")
        return rg
