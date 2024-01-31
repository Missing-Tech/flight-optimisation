import numpy as np
import ecmwf
import flight_path as fp
import math
import random
import networkx as nx


def run_aco_colony(iterations, no_of_ants, routing_graph):
    ants = []
    best_solution = 0
    ef_values = {}
    for _ in range(iterations):
        ants = []
        for ant in range(no_of_ants):
            solution = construct_solution(routing_graph)
            ants.append(solution)
            if objective_function(solution) > objective_function(best_solution):
                best_solution = solution

        for ant in ants:
            routing_graph = pheromone_update(ant, best_solution, routing_graph)
            if objective_function(ant) > objective_function(best_solution):
                best_solution = ant

    return ants


def objective_function(solution):
    return random.random()


def pheromone_update(solution, best_solution, routing_graph):
    evaporation_rate = 0.5
    tau_min = 1
    tau_max = 10

    for u, v in zip(solution[:-1], solution[1:]):
        edge = routing_graph[u][v]
        delta = 1 / 1 + objective_function(solution) - objective_function(best_solution)
        new_pheromone = (1 - evaporation_rate) * edge["pheromone"] + delta
        routing_graph[u][v]["pheromone"] = max(tau_min, min(new_pheromone, tau_max))
    return routing_graph


def construct_solution(routing_graph):
    solution = [(0, 0, 30000)]

    neighbours = routing_graph[solution[0]]

    while neighbours:
        probabilities = []
        choice = None
        for n in neighbours:
            probability = calculate_probability_at_neighbour(
                n, routing_graph, 1, 4, neighbours[n]["pheromone"], solution
            )
            if probability == -1:
                choice = [n]
                break
            probabilities.append(probability)
        if not choice:
            choice = random.choices(list(neighbours), weights=probabilities, k=1)
        solution.append(choice[0])
        neighbours = routing_graph[choice[0]]

    return solution


def calculate_heuristic(node, routing_graph, solution):
    current_heuristic = routing_graph.nodes[node]["heuristic"]
    return random.random()


def calculate_probability_at_neighbour(
    node, routing_graph, alpha, beta, pheromone, solution
):
    heuristic = calculate_heuristic(node, routing_graph, solution)
    total_neighbour_factor = 0
    neighbours = routing_graph[node]
    if not neighbours:
        return -1
    for n in neighbours:
        total_neighbour_factor += math.pow(
            neighbours[n]["pheromone"], alpha
        ) * math.pow(routing_graph.nodes[n]["heuristic"], beta)

    # probability = math.pow(pheromone, alpha) * math.pow(heuristic, beta) / total_neighbour_factor
    probability = 0.1
    return probability
