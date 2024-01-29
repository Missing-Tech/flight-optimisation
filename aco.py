import numpy as np
import ecmwf
import flight_path as fp
import routing_graph as rgraph
import util
import contrails as ct
import random


def run_aco_colony(iterations, no_of_ants, altitude_grid):
    ants = []
    best_solution = None
    ef_values = {}
    routing_graph = rgraph.calculate_routing_graph(altitude_grid)
    for _ in range(iterations):
        ants = []
        for ant in range(no_of_ants):
            solution = construct_solution(routing_graph)
            optimised_path = util.convert_indices_to_points(solution, altitude_grid)
            weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
            flight_path = fp.calculate_flight_characteristics(
                optimised_path, weather_data
            )
            ef_values[tuple(solution)] = ct.calculate_ef_from_flight_path(flight_path)
            ants.append(solution)
            if best_solution is None or ef_values[tuple(solution)] < ef_values[tuple(best_solution)]:
                best_solution = solution

        for ant in ants:
            routing_graph = pheromone_update(ant, best_solution, routing_graph, ef_values)
            if ef_values[tuple(solution)] < ef_values[tuple(best_solution)]:
                best_solution = ant

    return best_solution


def objective_function(solution):
    return random.random()


def pheromone_update(solution, best_solution, routing_graph, ef_values):
    evaporation_rate = 0.5
    tau_min = 1
    tau_max = 99

    for u, v in zip(solution[:-1], solution[1:]):
        edge = routing_graph[u][v]
        delta = 1 / 1 + ef_values[tuple(solution)] - ef_values[tuple(best_solution)]
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
                n, routing_graph, 1, 4, neighbours[n]["pheromone"]
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


def calculate_probability_at_neighbour(node, routing_graph, alpha, beta, pheromone):
    heuristic = routing_graph.nodes[node]["heuristic"]
    total_neighbour_factor = 0
    neighbours = routing_graph[node]
    if not neighbours:
        return -1
    for n in neighbours:
        total_neighbour_factor += (
            neighbours[n]["pheromone"] * routing_graph.nodes[n]["heuristic"]
        )
    probability = (pheromone * heuristic) / total_neighbour_factor
    return probability
