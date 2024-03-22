import unittest
from unittest.mock import MagicMock
from ..ant import Ant
from performance_model import Flight
import pandas as pd
import networkx as nx


class TestAnt(unittest.TestCase):
    def setUp(self):
        class MockRoutingGraphManager:
            def __init__(self):
                self.routing_graph = MagicMock()
                self.performance_model = MagicMock()

            def get_routing_graph(self):
                return self.routing_graph

            def get_performance_model(self):
                return self.performance_model

            def convert_index_to_point(self, index):
                return {
                    "latitude": 0,
                    "longitude": 0,
                    "altitude_ft": 0,
                    "thrust": 1,
                    "level": 0,
                }

        class MockConfig:
            GRID_WIDTH = 0
            STARTING_ALTITUDE = 10000
            PHEROMONE_WEIGHT = 1
            HEURISTIC_WEIGHT = 1
            STARTING_WEIGHT = 100000
            DEPARTURE_DATE = pd.Timestamp(
                year=2024, month=1, day=31, hour=13, minute=45, second=57
            )

        class MockObjective:
            def __init__(self):
                self.name = "objective"

            @staticmethod
            def calculate_objective(flight_path):
                return 1

        self.mock_routing_graph_manager = MockRoutingGraphManager()
        self.mock_objective = MockObjective()
        self.mock_config = MockConfig()

    def test_run_ant(self):
        ant = Ant(
            self.mock_routing_graph_manager, [self.mock_objective], self.mock_config
        )
        ant.construct_solution = MagicMock(
            return_value=Flight(self.mock_routing_graph_manager, [], self.mock_config)
        )
        solution = ant.run_ant(1)
        # Assert that the construct_solution and objective_function methods are called
        ant.construct_solution.assert_called_once()
        self.assertTrue(solution.objectives)  # Check if objectives are set

    def test_objective_function(self):
        ant = Ant(
            self.mock_routing_graph_manager, [self.mock_objective], self.mock_config
        )
        flight_path = MagicMock()
        objectives = ant.objective_function(flight_path)
        # Assert that the objective function returns the correct values
        self.assertEqual(objectives[str(self.mock_objective)], 1)

    def test_construct_solution(self):
        ant = Ant(
            self.mock_routing_graph_manager, [self.mock_objective], self.mock_config
        )
        ant.calculate_probability_at_neighbour = MagicMock(return_value=0.5)
        ant.routing_graph = nx.DiGraph()
        ant.routing_graph.add_node(
            (0, 0, 10000), **{f"{self.mock_objective}_heuristic": 1}
        )
        ant.routing_graph.add_node(
            (0, 1, 10000), **{f"{self.mock_objective}_heuristic": 1}
        )
        ant.routing_graph.add_edge(
            (0, 0, 10000), (0, 1, 10000), **{f"{self.mock_objective}_pheromone": 1}
        )
        solution = ant.construct_solution()
        # Assert that the construct_solution method returns a valid solution
        self.assertTrue(solution.indices)
        self.assertTrue(solution.flight_path)

    def test_calculate_probability_at_neighbour(self):
        ant = Ant(
            self.mock_routing_graph_manager, [self.mock_objective], self.mock_config
        )
        ant.routing_graph = nx.DiGraph()
        ant.routing_graph.add_node(
            (0, 0, 10000), **{f"{self.mock_objective}_heuristic": 1}
        )
        ant.routing_graph.add_node(
            (0, 1, 10000), **{f"{self.mock_objective}_heuristic": 1}
        )
        ant.routing_graph.add_edge(
            (0, 0, 10000), (0, 1, 10000), **{f"{self.mock_objective}_pheromone": 1}
        )
        ant.config.PHEROMONE_WEIGHT = 1
        ant.config.HEURISTIC_WEIGHT = 1
        probability = ant.calculate_probability_at_neighbour(
            (0, 1, 10000), 1, self.mock_objective
        )
        # Assert that the probability is calculated correctly
        self.assertEqual(probability, -1)
