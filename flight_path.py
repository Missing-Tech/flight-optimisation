import config
import util
import ecmwf
from geopy import distance as gp
import pandas as pd
import routing_grid as rg
import numpy as np
import time


def convert_altitude_to_pressure_bounded(altitude):
    pressure = util.calculate_pressure_from_altitude_ft(altitude)
    return max(config.PRESSURE_LEVELS[-1], min(pressure, config.PRESSURE_LEVELS[0]))


def calculate_flight_characteristics(
    flight_path,
    weather_data,
):
    for i in range(len(flight_path)):
        point = flight_path[i]

        point["level"] = convert_altitude_to_pressure_bounded(point["altitude_ft"])

        if i == 0:
            point["aircraft_mass"] = config.STARTING_WEIGHT
            point["time"] = config.DEPARTURE_DATE
        else:
            previous_point = flight_path[i - 1]
            time_elapsed = calculate_time_at_point(point, previous_point)
            point["time"] = previous_point["time"] + time_elapsed.round("s")

            point["fuel_flow"] = config.NOMINAL_FUEL_FLOW
            point["engine_efficiency"] = config.NOMINAL_ENGINE_EFFICIENCY
            point["aircraft_mass"] = (
                previous_point["aircraft_mass"]
                - point["fuel_flow"] * time_elapsed.total_seconds()
            )
        weather_at_point = weather_data.get_weather_data_at_point(point)
        temperature = weather_at_point["air_temperature"].values.item()
        u = weather_at_point["eastward_wind"].values.item()
        v = weather_at_point["northward_wind"].values.item()

        if i != len(flight_path) - 1:
            next_point = flight_path[i + 1]
            point["course"] = calculate_course_at_point(point, next_point)
            point["climb_angle"] = calculate_climb_angle(point, next_point)
        else:
            previous_point = flight_path[i - 1]
            point["course"] = previous_point["course"]
            point["climb_angle"] = 0

        point["true_airspeed"] = calculate_true_air_speed(point["thrust"], temperature)
        crabbing_angle = calculate_crabbing_angle(point, u, v)
        point["heading"] = point["course"] - crabbing_angle
        point["ground_speed"] = calculate_ground_speed(point, u, v)
    return flight_path


def calculate_time_at_point(point, previous_point):
    distance = gp.distance(
        (point["latitude"], point["longitude"]),
        (previous_point["latitude"], previous_point["longitude"]),
    ).m
    time_from_previous_point = pd.Timedelta(
        seconds=distance / previous_point["ground_speed"]
    )
    return time_from_previous_point


def calculate_course_at_point(point, next_point):
    bearing = rg.calculate_bearing(
        (point["longitude"], point["latitude"], 0),
        (next_point["longitude"], next_point["latitude"], 0),
    )
    return bearing


def calculate_true_air_speed(mach, temperature):
    speed_of_sound = 340.29
    sea_level_temp = 288.15  # in kelvin
    air_temp_ratio = temperature / sea_level_temp

    true_air_speed = mach * speed_of_sound * np.sqrt(air_temp_ratio)
    return true_air_speed  # in m/s


def calculate_crabbing_angle(point, u, v):
    numerator = (v * np.sin(point["course"])) - (u * np.cos(point["course"]))
    crabbing_angle = np.arcsin(numerator / point["true_airspeed"])
    return crabbing_angle


def calculate_climb_angle(point, next_point):
    change_in_altitude = next_point["altitude_ft"] - point["altitude_ft"]
    change_in_altitude_km = change_in_altitude / 3281
    distance = gp.distance(
        (point["latitude"], point["longitude"]),
        (next_point["latitude"], next_point["longitude"]),
    ).km
    angle = np.arctan2(change_in_altitude_km, distance)
    return angle


def calculate_ground_speed(point, u, v):
    climb_angle = point["climb_angle"]
    first_component = v * np.cos(point["course"]) + u * np.sin(point["course"])
    second_component = np.sqrt(
        np.power((point["true_airspeed"] * np.cos(climb_angle)), 2)
        - np.power(((v * np.sin(point["course"])) - (u * np.cos(point["course"]))), 2)
    )
    ground_speed = first_component + second_component
    return ground_speed
