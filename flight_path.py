import config
from geopy import distance as gp
import pandas as pd
import numpy as np
import util
from openap import FuelFlow, Emission


class AircraftPerformanceModel:
    def __init__(self):
        pass

    def calculate_flight_characteristics(self, flight_path):
        for i in range(len(flight_path)):
            point = flight_path[i]

            if i != len(flight_path) - 1:
                next_point = flight_path[i + 1]
                point["course"] = self.calculate_course_at_point(point, next_point)
                point["climb_angle"] = self.calculate_climb_angle(point, next_point)
            else:
                previous_point = flight_path[i - 1]
                point["course"] = 0
                point["climb_angle"] = 0

            temperature = point["temperature"]
            u = point["u"]
            v = point["v"]

            point["true_airspeed"] = self.calculate_true_air_speed(
                point["thrust"], temperature
            )
            crabbing_angle = self.calculate_crabbing_angle(point, u, v)
            point["heading"] = point["course"] - crabbing_angle
            point["ground_speed"] = self.calculate_ground_speed(point, u, v)

            if i == 0:
                point["aircraft_mass"] = config.STARTING_WEIGHT
                fuel_flow = self.calculate_fuel_flow(point, point["aircraft_mass"])
                point["fuel_flow"] = fuel_flow
                point["CO2"] = self.calculate_emissions(fuel_flow)
                point["time"] = config.DEPARTURE_DATE
            else:
                previous_point = flight_path[i - 1]
                time_elapsed = self.calculate_time_at_point(point, previous_point)
                point["time"] = previous_point["time"] + time_elapsed.round("s")

                fuel_flow = self.calculate_fuel_flow(
                    point, previous_point["aircraft_mass"]
                )
                point["fuel_flow"] = fuel_flow
                point["CO2"] = self.calculate_emissions(fuel_flow)
                point["engine_efficiency"] = config.NOMINAL_ENGINE_EFFICIENCY
                point["aircraft_mass"] = (
                    previous_point["aircraft_mass"]
                    - point["fuel_flow"] * time_elapsed.total_seconds()
                )

        return flight_path

    def calculate_time_at_point(self, point, previous_point):
        distance = gp.distance(
            (point["latitude"], point["longitude"]),
            (previous_point["latitude"], previous_point["longitude"]),
        ).m
        time_from_previous_point = pd.Timedelta(
            seconds=distance / previous_point["ground_speed"]
        )
        return time_from_previous_point

    def calculate_course_at_point(self, point, next_point):
        bearing = util.calculate_bearing(
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
        emission = Emission(ac="B77W", eng="GE90-115B")
        return emission.co2(FF)

    def calculate_fuel_flow(self, point, mass):
        fuelflow = FuelFlow(ac="B77W", eng="GE90-115B")

        FF = fuelflow.enroute(
            mass=mass,
            tas=point["true_airspeed"],
            alt=point["altitude_ft"],
            path_angle=point["heading"],
        )
        return FF
