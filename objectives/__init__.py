import pandas as pd
from openap import Emission
import geopy.distance as gd
import math


class Objective:
    def __init__(self, performance_model, config):
        self.config = config
        self.weight = 1
        self.performance_model = performance_model
        self.name = NotImplemented

    def _run_objective_function(self, flight_path):
        return NotImplemented

    def calculate_objective(self, flight_path):
        return self._run_objective_function(flight_path) * self.weight

    def calculate_heuristic(self, flight_path):
        return NotImplemented

    def _calculate_time_estimation(self, point):
        flat_distance_from_departure = gd.distance(
            (point[0], point[1]),
            self.config.DEPARTURE_AIRPORT,
        ).m
        distance_from_departure = math.sqrt(
            flat_distance_from_departure**2
            + (point[2] - self.config.STARTING_ALTITUDE) ** 2
        )
        speed = (
            self.config.NOMINAL_THRUST * 343
        )  # times by speed of sound for rough speed estimate
        time_to_point = distance_from_departure / speed
        time_at_point = self.config.DEPARTURE_DATE + pd.Timedelta(time_to_point, "s")
        return time_to_point, time_at_point

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ContrailObjective(Objective):
    def __init__(self, performance_model, config):
        super().__init__(performance_model, config)
        self.name = "contrail"
        self.weight = config.CONTRAIL_WEIGHT

    def _run_objective_function(self, flight_path):
        contrail_ef = self.performance_model.contrail_grid.interpolate_contrail_grid(
            flight_path
        )
        return contrail_ef

    def calculate_heuristic(self, point):
        contrails_at_point = max(
            self.performance_model.contrail_grid.interpolate_contrail_point(point),
            0.01,
        )
        return -contrails_at_point


class CocipObjective(Objective):
    def __init__(self, performance_model, config):
        super().__init__(performance_model, config)
        self.name = "contrail"
        self.weight = config.CONTRAIL_WEIGHT

    def _run_objective_function(self, flight_path):
        ef, _, _ = self.performance_model.cocip_manager.calculate_ef_from_flight_path(
            flight_path,
        )
        return ef.sum()

    def calculate_heuristic(self, point):
        contrails_at_point = max(
            self.performance_model.contrail_grid.interpolate_contrail_point(point),
            0.01,
        )
        return -contrails_at_point


class CO2Objective(Objective):
    def __init__(self, performance_model, config):
        super().__init__(performance_model, config)
        self.name = "co2"
        self.weight = config.CO2_WEIGHT

    def _calculate_flight_duration(self, flight_path):
        return (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600

    def _run_objective_function(self, flight_path):
        co2_kg = (
            sum(point["CO2"] for point in flight_path)
            * self._calculate_flight_duration(flight_path)
            * 3600
            / 1000  # convert g/s to kg
        )
        return co2_kg

    def calculate_heuristic(self, point):
        time_to_point, time_at_point = self._calculate_time_estimation(point)
        ps_grid = self.performance_model.ps_grid
        point = {
            "latitude": point[0],
            "longitude": point[1],
            "altitude_ft": point[2],
            "time": time_at_point,
        }
        fuel_flow_estimation = ps_grid.get_performance_data_at_point(point)["fuel_flow"]
        co2 = Emission(ac=self.config.AIRCRAFT_TYPE).co2(fuel_flow_estimation)
        return -co2


class TimeObjective(Objective):
    def __init__(self, performance_model, config):
        super().__init__(performance_model, config)
        self.name = "time"
        self.weight = config.TIME_WEIGHT

    def _run_objective_function(self, flight_path):
        flight_duration = (
            flight_path[-1]["time"] - flight_path[0]["time"]
        ).seconds / 3600
        return flight_duration

    def calculate_heuristic(self, point):
        time_to_point, _ = self._calculate_time_estimation(point)
        return -time_to_point
