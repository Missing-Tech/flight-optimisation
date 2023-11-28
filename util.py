import numpy as np

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
