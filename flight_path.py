import random
from openap import FuelFlow
from geopy import distance as gp
import pandas as pd
import util
import time
import numpy as np


def generate_random_flight_path(
    altitude_grid,
    weather_data,
    aircraft_type="A320",
    engine_type="CFM56-5B6",
    aircraft_mass=60_000,
    starting_altitude=30_000,
):
    flight_path = []
    currentYi = 0
    currentAltitude = starting_altitude
    for currentXi in range(len(altitude_grid[currentAltitude]) - 1):
        points = util.get_consecutive_points(
            currentXi, currentYi, currentAltitude, altitude_grid
        )
        next_point = random.choice(points)

        currentXi = next_point[0]
        currentAltitude = next_point[2]
        currentYi = min(
            next_point[1], len(altitude_grid[currentAltitude][currentXi]) - 1
        )

        point = altitude_grid[currentAltitude][currentXi][currentYi]
        point = {
            "latitude": point[0],
            "longitude": point[1],
            "altitude_ft": currentAltitude,
            "thrust": 0.85,
        }
        flight_path.append(point)

    flight_path_before = time.perf_counter()
    flight_path = calculate_flight_characteristics(
        flight_path, weather_data, aircraft_type, engine_type, aircraft_mass
    )
    flight_path_after = time.perf_counter()
    print(
        f"Time taken to calculate flight path 2: {flight_path_after - flight_path_before} seconds"
    )

    return flight_path


def generate_geodesic_flight_path(
    altitude_grid,
    weather_data,
    aircraft_type="A320",
    engine_type="CFM56-5B6",
    aircraft_mass=60_000,
    starting_altitude=30_000,
):
    flight_path = []
    currentAltitude = starting_altitude
    for currentXi in range(len(altitude_grid[currentAltitude]) - 1):
        mid_index = len(altitude_grid[currentAltitude][currentXi]) // 2
        point = altitude_grid[currentAltitude][currentXi][mid_index]
        point = {
            "latitude": point[0],
            "longitude": point[1],
            "altitude_ft": currentAltitude + 6000,
            "thrust": 0.85,
        }
        flight_path.append(point)
    flight_path = calculate_flight_characteristics(
        flight_path, weather_data, aircraft_type, engine_type, aircraft_mass
    )
    return flight_path


def calculate_flight_characteristics(
    flight_path, weather_data, aircraft_type, engine_type, aircraft_mass=60_000
):
    for i in range(len(flight_path)):
        point = flight_path[i]

        if i != len(flight_path) - 1:
            next_point = flight_path[i + 1]
            point["course"] = calculate_course_at_point(point, next_point)
            point["climb_angle"] = calculate_climb_angle(point, next_point)
        else:
            previous_point = flight_path[i - 1]
            point["course"] = previous_point["course"]
            point["climb_angle"] = 0

        point["true_airspeed"] = calculate_true_air_speed(
            point, point["thrust"], weather_data
        )
        crabbing_angle = calculate_crabbing_angle(point, weather_data)
        point["heading"] = point["course"] - crabbing_angle
        point["ground_speed"] = calculate_ground_speed(point, weather_data)

        if i == 0:
            point["aircraft_mass"] = aircraft_mass
            point["time"] = pd.Timestamp(year=2023, month=3, day=31, hour=23)
            point["fuel_flow"] = calculate_fuel_flow(
                point, point["aircraft_mass"], aircraft_type, engine_type
            )
        else:
            previous_point = flight_path[i - 1]
            point["fuel_flow"] = calculate_fuel_flow(
                point, previous_point["aircraft_mass"], aircraft_type, engine_type
            )
            time_elapsed = calculate_time_at_point(point, previous_point)
            point["time"] = previous_point["time"] + time_elapsed.round("s")
            fuel_consumed_kg = point["fuel_flow"] * time_elapsed.seconds
            point["aircraft_mass"] = previous_point["aircraft_mass"] - fuel_consumed_kg
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
    bearing = util.calculate_bearing(
        (point["longitude"], point["latitude"], 0),
        (next_point["longitude"], next_point["latitude"], 0),
    )
    return bearing


def calculate_true_air_speed(point, mach, weather_data):
    speed_of_sound = 340.29
    temperature = weather_data.get_temperature_at_point(point)
    sea_level_temp = 288.15  # in kelvin
    air_temp_ratio = temperature / sea_level_temp

    true_air_speed = mach * speed_of_sound * np.sqrt(air_temp_ratio)
    return true_air_speed  # in m/s


def calculate_crabbing_angle(point, weather_data):
    u, v = weather_data.get_wind_vector_at_point(point)

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


def calculate_ground_speed(point, weather_data):
    u, v = weather_data.get_wind_vector_at_point(point)
    climb_angle = point["climb_angle"]
    first_component = v * np.cos(point["course"]) + u * np.sin(point["course"])
    second_component = np.sqrt(
        np.power((point["true_airspeed"] * np.cos(climb_angle)), 2)
        - np.power(((v * np.sin(point["course"])) - (u * np.cos(point["course"]))), 2)
    )
    ground_speed = first_component + second_component
    return ground_speed


def calculate_fuel_flow(point, mass, ac="E190", eng="CF34-10E5"):
    fuelflow = FuelFlow(ac, eng)
    FF = fuelflow.enroute(
        mass=mass,
        tas=point["true_airspeed"] * 1.944,  # convert to knots
        alt=point["altitude_ft"],
        path_angle=np.rad2deg(point["climb_angle"]),
    )
    return FF
