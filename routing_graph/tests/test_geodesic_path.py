import unittest
from ..geodesic_path import GeodesicPath


class TestGeodesicPath(unittest.TestCase):
    def setUp(self):
        class Config:
            DEPARTURE_AIRPORT = (40.7128, -74.0060)  # New York City
            DESTINATION_AIRPORT = (34.0522, -118.2437)  # Los Angeles
            NO_OF_POINTS = 100
            R = 6371  # Earth's radius in kilometers

        self.config = Config()

    def test_reduce_angle(self):
        geodesic_path = GeodesicPath(self.config)
        angle = geodesic_path.reduce_angle(360)
        self.assertEqual(angle, 0)

    def test_calculate_path(self):
        geodesic_path = GeodesicPath(self.config)
        path = geodesic_path.calculate_path(100, (0, 0), (0, 1))
        self.assertIsInstance(path, list)
        self.assertEqual(len(path), 100)

    def test_calculate_alpha1(self):
        geodesic_path = GeodesicPath(self.config)
        alpha = geodesic_path.calculate_alpha1(0, 0, 0)
        self.assertAlmostEqual(alpha, 0)

    def test_calculate_central_angle(self):
        geodesic_path = GeodesicPath(self.config)
        central_angle = geodesic_path.calculate_central_angle(0, 0, 0)
        self.assertAlmostEqual(central_angle, 0)

    def test_calculate_azimuth(self):
        geodesic_path = GeodesicPath(self.config)
        azimuth = geodesic_path.calculate_azimuth(0, 0)
        self.assertAlmostEqual(azimuth, 0)

    def test_calculate_angle_1(self):
        geodesic_path = GeodesicPath(self.config)
        angle1 = geodesic_path.calculate_angle_1(0, 0)
        self.assertAlmostEqual(angle1, 0)

    def test_calculate_equator_longitude(self):
        geodesic_path = GeodesicPath(self.config)
        equator_longitude = geodesic_path.calculate_equator_longitude(0, 0, 0)
        self.assertAlmostEqual(equator_longitude, 0)

    def test_find_point_distance_along_great_circle(self):
        geodesic_path = GeodesicPath(self.config)
        point = geodesic_path.find_point_distance_along_great_circle(0, 0, 0)
        self.assertIsInstance(point, tuple)
        self.assertEqual(len(point), 3)
