import unittest
from ..altitude_grid import AltitudeGrid
from config import Config


class TestAltitudeGrid(unittest.TestCase):
    def setUp(self):
        class MockRoutingGrid:
            def get_routing_grid(self):
                return [
                    [(0, 0), (1, 1), (2, 2)],
                    [(3, 3), (4, 4), (5, 5)],
                    [(6, 6), (7, 7), (8, 8)],
                ]

        class MockConfig(Config):
            STARTING_ALTITUDE = 0
            ALTITUDE_STEP = 1
            MAX_ALTITUDE = 3
            NOMINAL_THRUST = 100
            PRESSURE_LEVELS = [1000, 900, 800]

        self.mock_routing_grid = MockRoutingGrid()
        self.mock_config = MockConfig()
        self.altitude_grid = AltitudeGrid(self.mock_routing_grid, self.mock_config)

    def test_calculate_altitude_grid(self):
        altitude_grid = self.altitude_grid.calculate_altitude_grid(
            [
                [(0, 0), (1, 1), (2, 2)],
                [(3, 3), (4, 4), (5, 5)],
                [(6, 6), (7, 7), (8, 8)],
            ]
        )
        # Assert expected altitude grid structure
        self.assertEqual(len(altitude_grid), 4)
        self.assertEqual(len(altitude_grid[0]), 3)
        self.assertEqual(len(altitude_grid[0][0]), 3)

    def test_convert_index_to_point(self):
        point = self.altitude_grid.convert_index_to_point((0, 0, 0))
        # Assert expected point attributes
        self.assertEqual(point["latitude"], 0)
        self.assertEqual(point["longitude"], 0)
        self.assertEqual(point["altitude_ft"], 0)
        self.assertEqual(point["thrust"], 100)
        self.assertAlmostEqual(point["level"], 1000)

    def test_iteration(self):
        for altitude in self.altitude_grid:
            self.assertTrue(altitude in range(0, 4))
            for step_points in self.altitude_grid[altitude]:
                self.assertEqual(len(step_points), 3)
                for step in step_points:
                    self.assertTrue(step is None or len(step) == 2)

    def test_getitem(self):
        step_points = self.altitude_grid[0]
        # Assert step points for altitude 5
        self.assertEqual(len(step_points), 3)

    def test_setitem(self):
        # Modify altitude grid and assert the change
        self.altitude_grid[0] = [(0, 0), (0, 0), (0, 0)]
        self.assertEqual(self.altitude_grid[0], [(0, 0), (0, 0), (0, 0)])
