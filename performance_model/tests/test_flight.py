import unittest
from unittest.mock import MagicMock
from ..flight import Flight, RealFlight
from config import Config


class TestFlight(unittest.TestCase):
    def setUp(self):
        class MockRoutingGraphManager:
            def convert_index_to_point(self, index):
                return {
                    "latitude": 0,
                    "longitude": 0,
                    "altitude_ft": 0,
                    "thrust": 1,
                    "level": 0,
                }

            def get_performance_model(self):
                return MagicMock()

        class MockConfig(Config):
            DEPARTURE_DATE = "2024-01-01"
            STARTING_WEIGHT = 100000

        self.mock_routing_graph_manager = MockRoutingGraphManager()
        self.mock_config = MockConfig()

    def test_set_departure(self):
        flight = Flight(self.mock_routing_graph_manager, [], self.mock_config)
        flight.set_departure((0, 0, 0))
        # Assert departure point is correctly set
        self.assertEqual(len(flight.flight_path), 1)
        self.assertEqual(flight.flight_path[0]["latitude"], 0)
        self.assertEqual(flight.flight_path[0]["longitude"], 0)
        self.assertEqual(flight.flight_path[0]["altitude_ft"], 0)
        self.assertEqual(flight.flight_path[0]["thrust"], 1)
        self.assertEqual(flight.flight_path[0]["time"], "2024-01-01")
        self.assertEqual(flight.flight_path[0]["aircraft_mass"], 100000)

    def test_run_performance_model(self):
        flight = Flight(self.mock_routing_graph_manager, [], self.mock_config)
        flight.performance_model.run_apm = MagicMock()
        flight.run_performance_model()
        # Assert performance model is run
        flight.performance_model.run_apm.assert_called_once_with([])

    def test_add_point_from_index(self):
        flight = Flight(self.mock_routing_graph_manager, [], self.mock_config)
        flight.routing_graph_manager.convert_index_to_point = MagicMock(
            return_value={
                "latitude": 1,
                "longitude": 1,
                "altitude_ft": 1,
                "thrust": 1,
                "level": 1,
            }
        )

        flight.add_point_from_index((1, 1, 1))
        # Assert point is correctly added from index
        self.assertEqual(len(flight.flight_path), 1)
        self.assertEqual(flight.flight_path[0]["latitude"], 1)
        self.assertEqual(flight.flight_path[0]["longitude"], 1)
        self.assertEqual(flight.flight_path[0]["altitude_ft"], 1)
        self.assertEqual(flight.flight_path[0]["thrust"], 1)


class TestRealFlight(unittest.TestCase):
    def setUp(self):
        class MockRoutingGraphManager:
            def convert_index_to_point(self, index):
                return {
                    "latitude": 0,
                    "longitude": 0,
                    "altitude_ft": 0,
                    "thrust": 1,
                    "level": 1,
                }

            def get_performance_model(self):
                return MagicMock()

        class MockConfig(Config):
            NOMINAL_THRUST = 1
            PRESSURE_LEVELS = [0, 1]

        self.mock_routing_graph_manager = MockRoutingGraphManager()
        self.mock_config = MockConfig()

    def test_convert_real_flight_path(self):
        real_flight = RealFlight(
            "test-flight.csv", self.mock_routing_graph_manager, self.mock_config
        )
        # Assert real flight path is correctly converted
        self.assertEqual(len(real_flight.flight_path), 2)
        self.assertEqual(real_flight.flight_path[0]["latitude"], 50)
        self.assertEqual(real_flight.flight_path[0]["longitude"], -3)
        self.assertEqual(real_flight.flight_path[0]["altitude_ft"], 30551)
        self.assertEqual(real_flight.flight_path[0]["thrust"], 1)
        self.assertEqual(real_flight.flight_path[0]["level"], 1)
