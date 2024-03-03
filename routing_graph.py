import networkx as nx
import config
import contrails as ct
import util
import os
import altitude_grid as ag
import geodesic_path as gp


def calculate_routing_graph(altitude_grid, contrail_grid):
    graph = nx.DiGraph()

    total_distance = gp.calculate_distance_between_airports()
    for altitude in altitude_grid:
        for step in altitude_grid[altitude]:
            for point in step:
                if point is None:
                    continue

                # contrails = (
                #     ct.interpolate_contrail_point(contrail_grid, (*point, altitude))
                #     / 1e15
                # ) - 0.01
                #

                distance_to_destination = gp.calculate_distance_between_points(
                    point, config.DESTINATION_AIRPORT
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
                    graph.add_node(
                        (xi, yi, altitude),
                        heuristic=max(
                            1 - (distance_to_destination / total_distance), 0.01
                        ),
                    )
                    next_lat, next_lon, _ = next_point
                    next_distance_to_destination = gp.calculate_distance_between_points(
                        (next_lat, next_lon), config.DESTINATION_AIRPORT
                    )
                    graph.add_node(
                        next_point,
                        heuristic=max(
                            1 - (next_distance_to_destination / total_distance), 0.01
                        ),
                    )

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
