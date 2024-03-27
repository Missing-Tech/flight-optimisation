from geopy import distance as gp
import pandas as pd
import numpy as np
from openap import FuelFlow, Emission
import math
import pycontrails as pc
from utils import Conversions


class AircraftPerformanceModel:
    def __init__(self, weather_grid, config):
        self.weather_grid = weather_grid
        self.config = config

    def calculate_flight_characteristics(self, flight_path):
        flight_path = self.calculate_coarse_characteristics(flight_path)
        flight_path = self.resample(flight_path)
        for i, point in enumerate(flight_path):
            if i != len(flight_path) - 1:
                next_point = flight_path[i + 1]
            else:
                next_point = None

            if i == 0:
                previous_point = None
            else:
                previous_point = flight_path[i - 1]

            point = self.recalculate_flight_characteristics(i, point, next_point)
            point = self.calculate_emission_data(i, point, previous_point)

        return flight_path

    def calculate_coarse_characteristics(self, flight_path):
        for i in range(len(flight_path)):
            point = flight_path[i]

            if i != len(flight_path) - 1:
                next_point = flight_path[i + 1]
                point["course"] = self.calculate_course_at_point(point, next_point)
                point["climb_angle"] = self.calculate_climb_angle(point, next_point)
            else:
                point["course"] = 0
                point["climb_angle"] = 0

            if i == 0:
                point["time"] = self.config.DEPARTURE_DATE
            else:
                previous_point = flight_path[i - 1]
                time_elapsed = self.calculate_time_at_point(point, previous_point)
                point["time"] = previous_point["time"] + time_elapsed.round("s")

            weather_at_point = self.weather_grid.get_weather_data_at_point(point)
            temperature = self.weather_grid.get_temperature_at_point(weather_at_point)
            u, v = self.weather_grid.get_wind_vector_at_point(weather_at_point)

            point["true_airspeed"] = self.calculate_true_air_speed(
                point["thrust"], temperature
            )
            crabbing_angle = self.calculate_crabbing_angle(point, u, v)
            point["heading"] = point["course"] - crabbing_angle
            point["ground_speed"] = self.calculate_ground_speed(point, u, v)

        return flight_path

    def recalculate_flight_characteristics(self, i, point, next_point):
        # if i != len(flight_path) - 1:
        #     next_point = flight_path[i + 1]
        if next_point is not None:
            point["course"] = self.calculate_course_at_point(point, next_point)
            point["climb_angle"] = self.calculate_climb_angle(point, next_point)
            point["segment_length"] = self.calculate_segment_length(next_point, point)
        else:
            point["segment_length"] = 0
            point["course"] = 0
            point["climb_angle"] = 0

        point["level"] = Conversions().convert_altitude_to_pressure_bounded(
            point["altitude_ft"],
            self.config.PRESSURE_LEVELS[-1],
            self.config.PRESSURE_LEVELS[0],
        )
        weather_at_point = self.weather_grid.get_weather_data_at_point(point)
        temperature = self.weather_grid.get_temperature_at_point(weather_at_point)
        u, v = self.weather_grid.get_wind_vector_at_point(weather_at_point)
        point["thrust"] = self.config.NOMINAL_THRUST

        point["true_airspeed"] = self.calculate_true_air_speed(
            point["thrust"], temperature
        )
        crabbing_angle = self.calculate_crabbing_angle(point, u, v)
        point["heading"] = point["course"] - crabbing_angle
        point["ground_speed"] = self.calculate_ground_speed(point, u, v)
        return point

    def calculate_emission_data(self, i, point, previous_point):
        if i == 0:
            point["aircraft_mass"] = self.config.STARTING_WEIGHT
            fuel_flow = self.calculate_fuel_flow(point, point["aircraft_mass"])
            point["fuel_flow"] = fuel_flow
            point["CO2"] = self.calculate_emissions(fuel_flow)
        else:
            fuel_flow = self.calculate_fuel_flow(point, previous_point["aircraft_mass"])
            time_elapsed = pd.Timedelta(point["time"] - previous_point["time"]).seconds
            point["fuel_flow"] = fuel_flow
            point["CO2"] = (
                self.calculate_emissions(fuel_flow) * time_elapsed
            ) / 1000  # kg
            point["aircraft_mass"] = (
                previous_point["aircraft_mass"] - point["fuel_flow"] * time_elapsed
            )

        return point

    def resample(self, flight_path):
        flight_path_df = pd.DataFrame(flight_path)

        attrs = {
            "flight_id": 123,
            "aircraft_type": self.config.AIRCRAFT_TYPE,
            "wingspan": self.config.WINGSPAN,
            "nvpm_ei_n": 1.897264e15,
            "n_engine": self.config.N_ENGINES,
            "engine_efficiency": self.config.NOMINAL_ENGINE_EFFICIENCY,
        }

        flight = pc.Flight(flight_path_df, flight_id=123, attrs=attrs)
        resample_path = flight.resample_and_fill("1min")
        resample_df = resample_path.dataframe
        resample_df["altitude_ft"] = resample_df["altitude"] * 3.28084
        resample_path = resample_df.to_dict("records")
        return resample_path

    def calculate_segment_length(self, point, previous_point):
        flat_distance = gp.distance(
            (point["latitude"], point["longitude"]),
            (previous_point["latitude"], previous_point["longitude"]),
        ).m
        euclidean_distance = math.sqrt(
            flat_distance**2
            + ((point["altitude_ft"] - previous_point["altitude_ft"]) / 3.281) ** 2
        )
        return euclidean_distance

    def calculate_time_at_point(self, point, previous_point):
        distance = gp.distance(
            (point["latitude"], point["longitude"]),
            (previous_point["latitude"], previous_point["longitude"]),
        ).m
        time_from_previous_point = pd.Timedelta(
            seconds=distance / previous_point["ground_speed"]
        )
        return time_from_previous_point

    def calculate_bearing(self, p1, p2):
        lat1, lon1, _ = p1
        lat2, lon2, _ = p2
        delta_lon = lon2 - lon1

        lat1 = np.radians(lat1)
        lat2 = np.radians(lat2)
        delta_lon = np.radians(delta_lon)

        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(
            delta_lon
        )
        y = np.sin(delta_lon) * np.cos(lat1)
        z = np.arctan2(y, x) % (2 * np.pi)  # Convert to range [0, 2pi]

        return z

    def calculate_course_at_point(self, point, next_point):
        bearing = self.calculate_bearing(
            (point["longitude"], point["latitude"], 0),
            (next_point["longitude"], next_point["latitude"], 0),
        )
        return bearing

    def calculate_true_air_speed(self, mach, temperature):
        speed_of_sound = 340.29
        sea_level_temp = 288.15  # in kelvin
        air_temp_ratio = temperature / sea_level_temp

        true_air_speed = mach * speed_of_sound * np.sqrt(air_temp_ratio)
        return true_air_speed  # in m/s

    def calculate_crabbing_angle(self, point, u, v):
        numerator = (v * np.sin(point["course"])) - (u * np.cos(point["course"]))
        crabbing_angle = np.arcsin(numerator / point["true_airspeed"])
        return crabbing_angle

    def calculate_climb_angle(self, point, next_point):
        change_in_altitude = next_point["altitude_ft"] - point["altitude_ft"]
        change_in_altitude_km = change_in_altitude / 3281
        distance = gp.distance(
            (point["latitude"], point["longitude"]),
            (next_point["latitude"], next_point["longitude"]),
        ).km
        angle = np.arctan2(change_in_altitude_km, distance)
        return angle

    def calculate_ground_speed(self, point, u, v):
        climb_angle = point["climb_angle"]
        first_component = v * np.cos(point["course"]) + u * np.sin(point["course"])
        second_component = np.sqrt(
            np.power((point["true_airspeed"] * np.cos(climb_angle)), 2)
            - np.power(
                ((v * np.sin(point["course"])) - (u * np.cos(point["course"]))), 2
            )
        )
        ground_speed = first_component + second_component
        return ground_speed

    def calculate_emissions(self, FF):
        emission = Emission(ac=self.config.AIRCRAFT_TYPE)
        return emission.co2(FF)  # g/s

    def calculate_fuel_flow(self, point, mass):
        fuelflow = FuelFlow(ac=self.config.AIRCRAFT_TYPE)

        FF = fuelflow.enroute(
            mass=mass,
            alt=point["altitude_ft"],
            tas=point["true_airspeed"],
            path_angle=point["heading"],
        )
        return FF
