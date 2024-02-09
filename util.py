import numpy as np
from datetime import datetime
import config
import ecmwf

R = 6371  # Earth radius in km


def reduce_angle(angle):
    while angle < -180:
        angle += 360
    while angle > 180:
        angle -= 360
    return angle


def calculate_normal_bearing(bearing):
    return (bearing + np.pi / 2) % (2 * np.pi)


# Formula from https://www.movable-type.co.uk/scripts/latlong.html
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


# Formula from https://www.movable-type.co.uk/scripts/latlong.html
def calculate_new_coordinates(p1, distance, bearing):
    lat1, lon1, _ = p1

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.arcsin(
        np.sin(lat1) * np.cos(distance / R)
        + np.cos(lat1) * np.sin(distance / R) * np.cos(bearing)
    )
    lon2 = lon1 + np.arctan2(
        np.sin(bearing) * np.sin(distance / R) * np.cos(lat1),
        np.cos(distance / R) - np.sin(lat1) * np.sin(lat2),
    )

    return np.degrees(lat2), np.degrees(lon2), bearing


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_altitude_ft_from_pressure(pressure):
    # Use the international barometric formula
    altitude = 44331.5 - 4946.62 * pressure ** (0.190263)
    return altitude


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_pressure_from_altitude_ft(altitude_ft):
    pressure = 100 * ((44331.514 - altitude_ft) / 11880.516) ** (1 / 0.1902632)

    return pressure


def get_nearest_value_from_list(value, list):
    return min(list, key=lambda x: abs(x - value))


def convert_indices_to_points(index_path, altitude_grid):
    path = []
    for point in index_path:
        altitude_point = altitude_grid[point[2]][point[0]][point[1]]
        path_point = {
            "latitude": altitude_point[0],
            "longitude": altitude_point[1],
            "altitude_ft": point[2],
            "thrust": config.INITIAL_THRUST,
        }
        path.append(path_point)

    return path


def convert_real_flight_path(df):
    path = []
    for index, row in df.iterrows():
        time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M:%S")
        path_point = {
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "altitude_ft": row["AltMSL"],
            "thrust": config.INITIAL_THRUST,
            "time": time,
        }
        path.append(path_point)

    return path


def get_consecutive_points(
    xi,
    yi,
    altitude,
    grid,
    max_lateral_var=config.OFFSET_VAR,
    max_altitude_var=config.MAX_ALTITUDE_VAR,
    altitude_step=config.ALTITUDE_STEP,
):

    max_alt = altitude + max_altitude_var  # Adding 4000 feet
    min_alt = altitude - max_altitude_var  # Subtracting 4000 feet
    max_alt = max(
        config.STARTING_ALTITUDE, min(max_alt, config.MAX_ALTITUDE)
    )  # Cap between 30000 and 40000
    min_alt = max(config.STARTING_ALTITUDE, min_alt)  # Cap between 30000 and 40000

    points = []
    current_altitude = min_alt
    while current_altitude <= max_alt and current_altitude >= min_alt:

        if xi + 1 == len(grid[current_altitude]):
            return None
        current_layer_length = len(grid[current_altitude][xi]) - 1
        next_layer_length = len(grid[current_altitude][xi + 1]) - 1
        min_i = min(max(yi - max_lateral_var, 0), next_layer_length)
        max_i = min(yi + max_lateral_var, next_layer_length)
        if next_layer_length > current_layer_length:
            min_i = yi
            max_i = yi + max_lateral_var * 2
        for i in range(min_i, max_i + 1):
            points.append((xi + 1, i, current_altitude))
        current_altitude += altitude_step

    return points
