import numpy as np
import ecmwf

R = 6371  # Earth radius in km
ds = ecmwf.met


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


# def get_consecutive_points(xi, yi, altitude, altitude_grid):
#     current_altitude = altitude_grid[altitude]
#
#     next_points = []
#     xi = xi + 1
#     max_offset = 2
#     if xi < len(current_altitude):
#         min_yi = max(yi - max_offset, 0)
#         max_yi = min(yi + max_offset, len(current_altitude[xi]) - 1)
#         print(min_yi, max_yi)
#         next_points = altitude_grid[altitude][xi][min_yi:max_yi]
#
#     print(next_points)
#     return next_points


def get_consecutive_points(xi, yi, altitude, altitude_grid):
    max_offset = 2
    max_altitude_offset = 2000
    current_altitude = altitude_grid[altitude]
    consecutive_points = []
    xi += 1
    if xi > len(current_altitude) or len(current_altitude) <= 0:
        return []

    min_yi = max(yi - max_offset, 0)
    max_yi = min(yi + max_offset, len(current_altitude[xi - 1]) - 1)
    min_altitude = max(altitude - max_altitude_offset, 30000)
    max_altitude = min(altitude + max_altitude_offset, 40000)

    altitudes = np.arange(min_altitude, max_altitude, max_altitude_offset)
    steps = np.arange(min_yi, max_yi).tolist()
    for alt in altitudes:
        for i in steps:
            consecutive_points.append([xi, i, alt])

    return consecutive_points
