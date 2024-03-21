import unittest
from ..routing_grid import RoutingGrid


class TestRoutingGrid(unittest.TestCase):
    def setUp(self):
        class GeodesicPath(list):
            def __init__(self):
                self.path = [(0, 0, 0), (1, 1, 0), (2, 2, 0)]
                super().__init__(self.path)

        class Config:
            R = 6371  # Earth's radius in kilometers
            GRID_WIDTH = 3
            GRID_SPACING = 100
            OFFSET_VAR = 1

        self.geodesic_path = GeodesicPath()
        self.config = Config()
        self.routing_grid = RoutingGrid(self.geodesic_path, self.config)

    def test_calculate_new_coordinates(self):
        new_coordinates = self.routing_grid.calculate_new_coordinates((0, 0, 0), 100, 0)
        # Assert expected latitude, longitude, and bearing
        self.assertAlmostEqual(new_coordinates[0], 0.8993, places=3)
        self.assertAlmostEqual(new_coordinates[1], 0.0, places=3)
        self.assertAlmostEqual(new_coordinates[2], 0.0, places=3)

    def test_calculate_normal_bearing(self):
        normal_bearing = self.routing_grid.calculate_normal_bearing(0)
        # Assert expected normal bearing
        self.assertAlmostEqual(normal_bearing, 1.5708, places=3)

    def test_calculate_bearing(self):
        bearing = self.routing_grid.calculate_bearing((0, 0, 0), (1, 1, 0))
        # Assert expected bearing
        self.assertAlmostEqual(bearing, 0.7853, places=3)

    def test_calculate_routing_grid(self):
        routing_grid = self.routing_grid.calculate_routing_grid()
        # Assert expected length and structure of routing grid
        # Length should match number of points in path
        self.assertEqual(len(routing_grid), 3)
        # Width should match GRID_WIDTH
        self.assertEqual(len(routing_grid[0]), self.config.GRID_WIDTH * 2 - 1)

    def test_get_routing_grid(self):
        routing_grid = self.routing_grid.get_routing_grid()
        # Length should match number of points in path
        self.assertEqual(len(routing_grid), 3)
        # Width should match GRID_WIDTH
        self.assertEqual(len(routing_grid[0]), self.config.GRID_WIDTH * 2 - 1)
