import unittest
from routing_graph import RoutingGraph
from config import Config


class TestRoutingGraph(unittest.TestCase):
    def setUp(self):
        class MockAltitudeGrid:
            def __init__(self):
                self.altitude_grid = {
                    0: [
                        [(0, 0), (1, 1), (2, 2)],
                        [(3, 3), (4, 4), (5, 5)],
                        [(6, 6), (7, 7), (8, 8)],
                    ],
                    1: [
                        [None, None, None],
                        [(3, 3), (4, 4), (5, 5)],
                        [(6, 6), (7, 7), (8, 8)],
                    ],
                }

            def __iter__(self):
                return iter(self.altitude_grid)

            def __setitem__(self, key, value):
                self.altitude_grid[key] = value

            def __getitem__(self, key):
                return self.altitude_grid[key]

        class MockObjective:
            def __init__(self, performance_model, config):
                self.config = config
                self.name = "test"
                self.performance_model = performance_model

            def calculate_heuristic(self, point):
                return 1

            def __str__(self):
                return self.name

        class MockConfig(Config):
            OBJECTIVES = [MockObjective]
            STARTING_ALTITUDE = 0
            MAX_ALTITUDE = 0
            OFFSET_VAR = 1
            ALTITUDE_STEP = 1
            TAU_MAX = 1

        class MockPerformanceModel:
            pass

        self.mock_altitude_grid = MockAltitudeGrid()
        self.mock_performance_model = MockPerformanceModel()
        self.mock_config = MockConfig()
        self.routing_graph = RoutingGraph(
            self.mock_altitude_grid,
            self.mock_performance_model,
            self.mock_config,
            test=True,
        )

    def test_get_consecutive_points(self):
        points = self.routing_graph.get_consecutive_points(
            0, 0, 0, self.mock_altitude_grid
        )
        # Assert that points are correctly calculated
        self.assertEqual(points, [(1, 0, 0), (1, 1, 0)])

    def test_calculate_routing_graph(self):
        graph = self.routing_graph.calculate_routing_graph()
        # Assert expected number of nodes and edges
        self.assertEqual(len(graph.nodes), 15)
        self.assertEqual(len(graph.edges), 14)

    def test_parse_node(self):
        node = self.routing_graph.parse_node("(0, 0, 31000)")
        # Assert parsing of node string
        self.assertEqual(node, (0, 0, 31000))

    def test_init_routing_graph(self):
        routing_graph = self.routing_graph._init_routing_graph(test=True)
        # Assert initialization of routing graph
        self.assertEqual(len(routing_graph.nodes), 15)
        self.assertEqual(len(routing_graph.edges), 14)  # 8 edges

    def test_getitem(self):
        item = self.routing_graph[(0, 0, 0)]
        # Assert getting an item from routing graph
        self.assertIsNotNone(item)

    def test_pheromones(self):
        routing_graph = self.routing_graph._init_routing_graph(test=True)
        for edge in routing_graph.edges:
            pheromones = routing_graph.edges[edge]["test_pheromone"]
            self.assertEqual(pheromones, 1)

    def test_heuristic(self):
        routing_graph = self.routing_graph._init_routing_graph(test=True)
        for node in routing_graph.nodes:
            heuristic = routing_graph.nodes[node]["test_heuristic"]
            self.assertEqual(heuristic, 1)
