import networkx as nx
import util


def calculate_routing_graph(altitude_grid):
    graph = nx.DiGraph()
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

                if consecutive_points is None:
                    continue
                for next_point in consecutive_points:
                    if next_point is not None:
                        currentXi = next_point[0]
                        currentAltitude = next_point[2]
                        currentYi = next_point[1] - 1
                        next_point = altitude_grid[currentAltitude][currentXi][
                            currentYi
                        ]
                        graph.add_edge((*point, altitude), (*next_point, altitude))

    return graph
