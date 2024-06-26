import random
import math
from performance_model import Flight

import typing

if typing.TYPE_CHECKING:
    from config import Config
    from routing_graph import RoutingGraphManager, RoutingGraph
    from _types import FlightPath, Objectives, IndexPoint3D


class Ant:
    def __init__(
        self,
        routing_graph_manager: "RoutingGraphManager",
        objectives: "Objectives",
        config: "Config",
    ):
        """
        A single ant during the ACO algorithm, containing relevant objective and
        heuristic information
        """
        self.routing_graph_manager: "RoutingGraphManager" = routing_graph_manager
        self.routing_graph: "RoutingGraph" = routing_graph_manager.get_routing_graph()
        self.objectives: "Objectives" = objectives
        self.config: "Config" = config

    def run_ant(self, id: int) -> Flight:
        """
        Runs an iteration of the ant going through the routing graph
        """
        solution = self.construct_solution()
        solution.run_performance_model()
        solution.calculate_objectives()

        return solution

    def construct_solution(self) -> Flight:
        """
        Constructs a solution by traversing the routing graph
        """
        solution = Flight(
            self.routing_graph_manager,
            [],
            self.config,
        )
        solution.set_departure(
            ((0, self.config.GRID_WIDTH, self.config.STARTING_ALTITUDE))
        )

        neighbours = self.routing_graph[solution.indices[0]]
        while neighbours:
            probabilities = []
            choice = None
            random_objective = random.choice(self.objectives)
            for n in neighbours:
                probability = self.calculate_probability_at_neighbour(
                    n,
                    neighbours[n][f"{random_objective}_pheromone"],
                    random_objective,
                )
                if probability is None:
                    # reached the destination
                    choice = n
                    break

                probabilities.append(probability)
            if not choice and probabilities:
                choice = random.choices(list(neighbours), weights=probabilities, k=1)[0]

            solution.add_point_from_index(choice)
            neighbours = self.routing_graph[choice]

        return solution

    def calculate_probability_at_neighbour(
        self,
        node: "IndexPoint3D",
        pheromone: float,
        objective: str,
    ) -> float or None:
        """
        Calculates the probability of an ant choosing this node based off the
        pheromone and heuristic values of its neighbours
        """
        heuristic = self.routing_graph.nodes[node][f"{objective}_heuristic"]
        total_neighbour_factor = 0
        neighbours = self.routing_graph[node]

        alpha = self.config.PHEROMONE_WEIGHT
        beta = self.config.HEURISTIC_WEIGHT
        if node[0] == self.config.NO_OF_POINTS and node[1] == 0:
            return None
        if len(neighbours) == 0:
            return 0.0001
        for n in neighbours:
            total_neighbour_factor += math.pow(
                neighbours[n][f"{objective}_pheromone"], alpha
            ) * math.pow(self.routing_graph.nodes[n][f"{objective}_heuristic"], beta)

        probability = (
            math.pow(pheromone, alpha) * math.pow(heuristic, beta)
        ) / total_neighbour_factor
        return probability
