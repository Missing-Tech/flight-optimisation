import config
import ecmwf
from openap import polymer
from geopy import distance as gp
import pandas as pd
import util
import numpy as np


def calculate_flight_characteristics(
    flight_path,
    weather_data,
):
    polymer_flight = polymer.Flight(config.AIRCRAFT_TYPE)
    for i in range(len(flight_path)):

        point = flight_path[i]

        pressure = ecmwf.get_nearest_pressure_level_at_point(point)

        if i == 0:
            point["aircraft_mass"] = config.STARTING_WEIGHT
            point["time"] = config.DEPARTURE_DATE
            point["fuel_flow"] = 0
        else:
            previous_point = flight_path[i - 1]
            point["aircraft_mass"] = previous_point[
                "aircraft_mass"
            ] - calculate_fuel_flow(
                point, previous_point["aircraft_mass"], polymer_flight, previous_point
            )
            time_elapsed = calculate_time_at_point(point, previous_point)
            point["time"] = previous_point["time"] + time_elapsed.round("s")

        weather_at_point = weather_data.get_weather_data_at_point(
            point,
            pressure,
        )

        if i != len(flight_path) - 1:
            next_point = flight_path[i + 1]
            point["course"] = calculate_course_at_point(point, next_point)
            point["climb_angle"] = calculate_climb_angle(point, next_point)
        else:
            previous_point = flight_path[i - 1]
            point["course"] = previous_point["course"]
            point["climb_angle"] = 0

        point["true_airspeed"] = calculate_true_air_speed(
            point["thrust"], weather_data, weather_at_point
        )
        crabbing_angle = calculate_crabbing_angle(point, weather_data, weather_at_point)
        point["heading"] = point["course"] - crabbing_angle
        point["ground_speed"] = calculate_ground_speed(
            point, weather_data, weather_at_point
        )

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


def calculate_true_air_speed(mach, weather_data, weather_at_point):
    speed_of_sound = 340.29
    temperature = weather_data.get_temperature_at_point(weather_at_point)
    sea_level_temp = 288.15  # in kelvin
    air_temp_ratio = temperature / sea_level_temp

    true_air_speed = mach * speed_of_sound * np.sqrt(air_temp_ratio)
    return true_air_speed  # in m/s


def calculate_crabbing_angle(point, weather_data, weather_at_point):
    u, v = weather_data.get_wind_vector_at_point(weather_at_point)

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


def calculate_ground_speed(point, weather_data, weather_at_point):
    u, v = weather_data.get_wind_vector_at_point(weather_at_point)
    climb_angle = point["climb_angle"]
    first_component = v * np.cos(point["course"]) + u * np.sin(point["course"])
    second_component = np.sqrt(
        np.power((point["true_airspeed"] * np.cos(climb_angle)), 2)
        - np.power(((v * np.sin(point["course"])) - (u * np.cos(point["course"]))), 2)
    )
    ground_speed = first_component + second_component
    return ground_speed


def calculate_fuel_flow(point, mass, flight, previous_point):
    # fuelflow = FuelFlow('A320', 'CFM56-5B6')
    # FF = fuelflow.enroute(
    #     mass=mass,
    #     tas=point["true_airspeed"] * 1.944,  # convert to knots
    #     alt=point["altitude_ft"],
    #     path_angle=np.rad2deg(point["climb_angle"]),
    # )
    distance = gp.distance(
        (previous_point["latitude"], previous_point["longitude"]),
        (point["latitude"], point["longitude"]),
    ).km
    fuel_flow = flight.fuel(distance=distance, mass=mass)
    # return FF
    return fuel_flow
