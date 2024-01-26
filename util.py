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


def convert_indices_to_points(index_path, altitude_grid):
    path = []
    for point in index_path:
        path.append((*altitude_grid[point[2]][point[0]][point[1]], point[2]))

    return path


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
