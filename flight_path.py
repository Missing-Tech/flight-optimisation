import random
from openap import FuelFlow
from geopy import distance as gp
import pandas as pd
import util
import numpy as np


def generate_random_flight_path(
    altitude_grid, aircraft_type="E190", engine_type="CF34-10E5"
):
    def get_consecutive_points(
        xi,
        yi,
        altitude,
        grid,
        max_lateral_var=2,
        max_altitude_var=2_000,
        altitude_step=2_000,
    ):
        if xi == len(grid[altitude]) - 1:
            return None
        min_i = max(yi - max_lateral_var, 0)
        max_i = min(yi + max_lateral_var, len(grid[altitude][xi]) - 1)

        points = []
        if max_i > 0:
            for i in range(min_i, max_i + 1):
                points.append((xi + 1, i))
        else:
            points.append((xi + 1, 0))

        max_alt = altitude + max_altitude_var  # Adding 4000 feet
        min_alt = altitude - max_altitude_var  # Subtracting 4000 feet
        max_alt = max(30000, min(max_alt, 40000))  # Cap between 30000 and 40000
        min_alt = max(30000, min_alt)  # Cap between 30000 and 40000

        altitude_points = []
        current_altitude = min_alt
        while current_altitude <= max_alt and current_altitude >= min_alt:
            for point in points:
                altitude_points.append((*point, current_altitude))
            current_altitude += altitude_step

        return altitude_points

    flight_path = []

    currentYi = 0
    currentAltitude = 30_000
    for currentXi in range(len(altitude_grid[currentAltitude]) - 1):
        points = get_consecutive_points(
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
            "thrust": 0.9,
        }
        flight_path.append(point)

    flight_path = calculate_course_at_points(flight_path)
    flight_path = calculate_true_air_speed_at_points(flight_path)
    flight_path = calculate_headings_at_points(flight_path)
    flight_path = calculate_climb_angle_at_points(flight_path)
    flight_path = calculate_ground_speed_at_points(flight_path)
    flight_path = calculate_time_at_points(
        flight_path, pd.Timestamp(year=2023, month=3, day=31, hour=0)
    )
    flight_path = calculate_fuel_flow_at_points(flight_path, aircraft_type, engine_type)

    return flight_path


def calculate_course_at_points(flight_path):
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        next_point = flight_path[i + 1]
        bearing = util.calculate_bearing(
            (point["longitude"], point["latitude"], 0),
            (next_point["longitude"], next_point["latitude"], 0),
        )
        flight_path[i]["course"] = bearing
    return flight_path


def calculate_time_at_points(flight_path, start_time):
    time = start_time
    flight_path[0]["time"] = time
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        next_point = flight_path[i + 1]
        distance = gp.distance(
            (point["latitude"], point["longitude"]),
            (next_point["latitude"], next_point["longitude"]),
        ).km
        flight_path[i + 1]["time"] = time + pd.Timedelta(
            hours=distance / point["ground_speed"]
        )
        time = flight_path[i + 1]["time"]
    return flight_path


def calculate_true_air_speed(point, mach):
    speed_of_sound = 340.29
    temperature = util.get_temperature_at_point(point)
    sea_level_temp = 288.15  # in kelvin
    air_temp_ratio = temperature / sea_level_temp

    return mach * speed_of_sound * np.sqrt(air_temp_ratio)


def calculate_true_air_speed_at_points(flight_path):
    for i in range(len(flight_path)):
        point = flight_path[i]
        tas = calculate_true_air_speed(point, point["thrust"])
        flight_path[i]["true_airspeed"] = tas
    return flight_path


def calculate_crabbing_angle(point):
    u, v = util.get_wind_vector_at_point(point)

    numerator = (v * np.sin(point["course"])) - (u * np.cos(point["course"]))
    crabbing_angle = np.arcsin(numerator / point["true_airspeed"])
    return crabbing_angle


def calculate_headings_at_points(flight_path):
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        crabbing_angle = calculate_crabbing_angle(point)
        flight_path[i]["heading"] = flight_path[i]["course"] - crabbing_angle
    return flight_path


def calculate_climb_angle(point, next_point):
    change_in_altitude = next_point["altitude_ft"] - point["altitude_ft"]
    change_in_altitude_km = change_in_altitude / 3281
    distance = gp.distance(
        (point["latitude"], point["longitude"]),
        (next_point["latitude"], next_point["longitude"]),
    ).km
    angle = np.arctan2(change_in_altitude_km, distance)
    return angle


def calculate_climb_angle_at_points(flight_path):
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        next_point = flight_path[i + 1]
        climb_angle = calculate_climb_angle(point, next_point)
        flight_path[i]["climb_angle"] = climb_angle
    flight_path[-1]["climb_angle"] = 0
    return flight_path


def calculate_ground_speed(point):
    u, v = util.get_wind_vector_at_point(point)
    climb_angle = point["climb_angle"]
    first_component = v * np.cos(point["course"]) + u * np.sin(point["course"])
    second_component = np.sqrt(
        np.power((point["true_airspeed"] * np.cos(climb_angle)), 2)
        - np.power(((v * np.sin(point["course"])) - (u * np.cos(point["course"]))), 2)
    )
    ground_speed = first_component + second_component
    return ground_speed


def calculate_ground_speed_at_points(flight_path):
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        ground_speed = calculate_ground_speed(point)
        flight_path[i]["ground_speed"] = ground_speed * 1.852  # convert from Kn to kmph

    return flight_path


# TODO: Calculate fuel flow + weight at points


def calculate_fuel_flow(point, ac="E190", eng="CF34-10E5"):
    fuelflow = FuelFlow(ac, eng)
    FF = fuelflow.enroute(
        mass=point["aircraft_mass"],
        tas=point["true_airspeed"],
        alt=point["altitude_ft"],
        path_angle=np.rad2deg(point["climb_angle"]),
    )
    return FF


def calculate_fuel_flow_at_points(
    flight_path, ac="E190", eng="CF34-10E5", mass=150_000
):
    flight_path[0]["aircraft_mass"] = mass
    for i in range(len(flight_path) - 1):
        point = flight_path[i]
        fuel_flow_kg_s = calculate_fuel_flow(point, ac, eng)
        time_to_next_point_s = (flight_path[i + 1]["time"] - point["time"]).seconds
        fuel_consumption_kg = fuel_flow_kg_s * time_to_next_point_s
        flight_path[i + 1]["aircraft_mass"] = (
            point["aircraft_mass"] - fuel_consumption_kg
        )
        flight_path[i]["fuel_flow"] = fuel_flow_kg_s
    flight_path[-1]["fuel_flow"] = calculate_fuel_flow(flight_path[-1], ac, eng)
    return flight_path
