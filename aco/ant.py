import random
import math


class Ant:
    def __init__(self, rg, ag, cg, pm, config, objectives):
        self.routing_graph = rg
        self.altitude_grid = ag
        self.contrail_grid = cg
        self.performance_model = pm
        self.config = config
        self.objectives = objectives

    def run_ant(self, id):
        solution = self.construct_solution()
        solution.run_performance_model()
        objectives = self.objective_function(solution.flight_path)
        solution.set_objective_value(objectives)

        return solution

    def objective_function(self, flight_path):
        objectives = {}
        for obj in self.objectives:
            # Get the string representation of the class name
            objective_name = str(obj)

            # Call the 'calculate_objectives' method of the object
            objective_value = obj.calculate_objectives()

            # Store the results in the dictionary
            objectives[objective_name] = objective_value
        return objectives

    def construct_solution(self):
        from .aco import Flight

        solution = Flight(
            self.altitude_grid,
            self.routing_graph,
            self.performance_model,
            flight_path=[],
        )
        solution.set_departure(
            ((0, self.config.GRID_WIDTH, self.config.STARTING_ALTITUDE))
        )

        neighbours = self.routing_graph[solution.indices[0]]
        while neighbours:
            probabilities = []
            choice = None
            random_objective = str(random.choice(self.objectives))
            for n in neighbours:
                probability = self.calculate_probability_at_neighbour(
                    n,
                    neighbours[n][f"{random_objective}_pheromone"],
                    random_objective,
                )
                if probability == -1:
                    # reached the destination
                    choice = n
                    break
                probabilities.append(probability)
            if not choice:
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
        total_neighbour_factor = 0.01
        neighbours = self.routing_graph[node]

        alpha = self.config.PHEROMONE_WEIGHT
        beta = self.config.HEURISTIC_WEIGHT

        if not neighbours:
            return -1
        for n in neighbours:
            total_neighbour_factor += math.pow(
                neighbours[n][f"{objective}_pheromone"], alpha
            ) * math.pow(self.routing_graph.nodes[n][f"{objective}_heuristic"], beta)

        probability = (
            math.pow(pheromone, alpha) * math.pow(heuristic, beta)
        ) / total_neighbour_factor
        return probability
