from datetime import datetime
import numpy as np
import config
from geopy import distance as gp

R = 6371  # Earth radius in km


def reduce_angle(angle):
    while angle < -180:
        angle += 360
    while angle > 180:
        angle -= 360
    return angle


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_altitude_ft_from_pressure(pressure):
    pressure_pa = pressure * 100  # Convert to Pa
    # Use the international barometric formula
    altitude = 44331.5 - 4946.62 * pressure_pa ** (0.190263)
    return altitude * 3.28084


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_pressure_from_altitude_ft(altitude_ft):
    # convert altitude to meters
    altitude_m = altitude_ft / 3.28084
    pressure = ((44331.514 - altitude_m) / 11880.516) ** (1 / 0.1902632)

    return pressure


def calculate_normal_bearing(bearing):
    return (bearing + np.pi / 2) % (2 * np.pi)


def calculate_bearing(p1, p2):
    lat1, lon1, _ = p1
    lat2, lon2, _ = p2
    delta_lon = lon2 - lon1

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    delta_lon = np.radians(delta_lon)

    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)
    y = np.sin(delta_lon) * np.cos(lat1)
    z = np.arctan2(y, x) % (2 * np.pi)  # Convert to range [0, 2pi]

    return z


def calculate_distance_between_points(p1, p2):
    lat0, lon0 = p1
    lat1, lon1 = p2

    return gp.distance((lat0, lon0), (lat1, lon1)).m


def calculate_distance_between_airports():
    total_distance = calculate_distance_between_points(
        config.DEPARTURE_AIRPORT, config.DESTINATION_AIRPORT
    )

    return total_distance


def calculate_step_between_airports():
    total_distance = calculate_distance_between_airports()
    step = total_distance / config.NO_OF_POINTS
    return step


def get_nearest_value_from_list(value, list):
    return min(list, key=lambda x: abs(x - value))


def convert_indices_to_points(index_path, altitude_grid, thrust=config.NOMINAL_THRUST):
    path = []
    for point in index_path:
        path_point = convert_index_to_point(point, altitude_grid, thrust)
        path.append(path_point)

    return path


def convert_index_to_point(index, altitude_grid, thrust=config.NOMINAL_THRUST):
    altitude_point = altitude_grid[index[2]][index[0]][index[1]]
    path_point = {
        "latitude": altitude_point[0],
        "longitude": altitude_point[1],
        "altitude_ft": index[2],
        "thrust": thrust,
        "level": convert_altitude_to_pressure_bounded(index[2]),
    }
    return path_point


def convert_real_flight_path(df, weather_grid):
    path = []
    for _, row in df.iterrows():
        time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M:%S")
        path_point = {
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "altitude_ft": row["AltMSL"],
            "thrust": config.NOMINAL_THRUST,
            "time": time,
            "level": convert_altitude_to_pressure_bounded(row["AltMSL"]),
        }
        weather_at_point = weather_grid.get_weather_data_at_point(path_point)

        temperature = weather_at_point["air_temperature"].values.item()
        u = weather_at_point["eastward_wind"].values.item()
        v = weather_at_point["northward_wind"].values.item()

        path_point["temperature"] = temperature
        path_point["u"] = u
        path_point["v"] = v

        path.append(path_point)

    return path


def convert_altitude_to_pressure_bounded(altitude):
    pressure = calculate_pressure_from_altitude_ft(altitude)
    return max(config.PRESSURE_LEVELS[-1], min(pressure, config.PRESSURE_LEVELS[0]))


def get_consecutive_points(
    xi,
    yi,
    altitude,
    grid,
    max_lateral_var=config.OFFSET_VAR,
    max_altitude_var=config.MAX_ALTITUDE_VAR,
    altitude_step=config.ALTITUDE_STEP,
):
    max_alt = altitude + max_altitude_var
    max_alt = max(config.STARTING_ALTITUDE, min(max_alt, config.MAX_ALTITUDE))

    points = []
    current_altitude = altitude
    while current_altitude <= max_alt:
        if xi + 1 == len(grid[current_altitude]):
            return None
        next_layer_length = len(grid[current_altitude][xi + 1]) - 1
        min_i = min(max(yi - max_lateral_var, 0), next_layer_length)
        max_i = min(yi + max_lateral_var, next_layer_length)
        for i in range(min_i, max_i + 1):
            points.append((xi + 1, i, current_altitude))
        current_altitude += altitude_step

    return points
