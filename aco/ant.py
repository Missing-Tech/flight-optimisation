import random
import math
from performance_model import Flight
from rich import print


class Ant:
    def __init__(self, routing_graph_manager, objectives, config):
        self.routing_graph_manager = routing_graph_manager
        self.routing_graph = routing_graph_manager.get_routing_graph()
        self.objectives = objectives
        self.config = config

    def run_ant(self, id):
        solution = self.construct_solution()
        solution.run_performance_model()
        objectives = self.objective_function(solution.flight_path)
        solution.set_objective_value(objectives)

        return solution

    def objective_function(self, flight_path):
        objectives = {}
        for objective in self.objectives:
            # Get the string representation of the class name
            objective_name = str(objective)

            # Call the 'calculate_objectives' method of the object
            objective_value = objective.calculate_objective(
                flight_path,
            )

            # Store the results in the dictionary
            objectives[objective_name] = objective_value
        return objectives

    def construct_solution(self):
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
        node,
        pheromone,
        objective,
    ):
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
