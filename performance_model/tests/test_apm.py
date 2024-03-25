import unittest
import pandas as pd
from ..apm import AircraftPerformanceModel


class TestAircraftPerformanceModel(unittest.TestCase):
    def setUp(self):
        class MockWeatherGrid:
            def get_weather_data_at_point(self, point):
                return {"temperature": 25, "wind_u": 10, "wind_v": 5}

            def get_temperature_at_point(self, weather_data):
                return weather_data["temperature"]

            def get_wind_vector_at_point(self, weather_data):
                return weather_data["wind_u"], weather_data["wind_v"]

        class MockConfig:
            DEPARTURE_DATE = pd.Timestamp(
                year=2024, month=1, day=31, hour=13, minute=45, second=57
            )
            NOMINAL_ENGINE_EFFICIENCY = 0.85
            STARTING_WEIGHT = 100000
            AIRCRAFT_TYPE = "A320"

        self.mock_weather_grid = MockWeatherGrid()
        self.mock_config = MockConfig()

    def test_calculate_flight_characteristics(self):
        apm = AircraftPerformanceModel(self.mock_weather_grid, self.mock_config)
        flight_path = [
            {"latitude": 0, "longitude": 0, "altitude_ft": 0, "thrust": 1},
            {"latitude": 1, "longitude": 1, "altitude_ft": 10000, "thrust": 1},
        ]
        flight_path = apm.calculate_flight_characteristics(flight_path)
        # Assert flight characteristics are calculated correctly
        self.assertEqual(len(flight_path), 2)
        self.assertIn("course", flight_path[0])
        self.assertIn("climb_angle", flight_path[0])
        self.assertIn("time", flight_path[0])
        self.assertIn("true_airspeed", flight_path[0])
        self.assertIn("heading", flight_path[0])
        self.assertIn("ground_speed", flight_path[0])
        self.assertIn("fuel_flow", flight_path[0])
        self.assertIn("CO2", flight_path[0])
        self.assertIn("aircraft_mass", flight_path[0])
