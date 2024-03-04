import util
import config
import os
import pickle
import geodesic_path as gp
import numpy as np


def get_routing_grid():
    return calculate_routing_grid(gp.get_geodesic_path())
    # if os.path.exists("data/routing_grid.p"):
    #     return pickle.load(open("data/routing_grid.p", "rb"))
    # else:
    #     rg = calculate_routing_grid(gp.get_geodesic_path())
    #     pickle.dump(rg, open("data/routing_grid.p", "wb"))
    #     return rg


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
        np.sin(lat1) * np.cos(distance / util.R)
        + np.cos(lat1) * np.sin(distance / util.R) * np.cos(bearing)
    )
    lon2 = lon1 + np.arctan2(
        np.sin(bearing) * np.sin(distance / util.R) * np.cos(lat1),
        np.cos(distance / util.R) - np.sin(lat1) * np.sin(lat2),
    )

    return np.degrees(lat2), np.degrees(lon2), bearing


def calculate_routing_grid(
    path,
):
    grid = []
    for point in path:
        lat, lon, _ = point
        positive_waypoints = []
        negative_waypoints = []
        potential_waypoints = []
        for i in range(1, config.GRID_WIDTH + 1):
            index = path.index(point)

            # if index - (i / config.GRID_STEP) < 0:
            #     continue
            #
            if index + (i / config.OFFSET_VAR) > len(path) - 1:
                continue

            if index + 1 > len(path) - 1:
                continue

            bearing = calculate_bearing(path[index], path[index + 1])
            bearing = calculate_normal_bearing(bearing)

            new_point_positive = calculate_new_coordinates(
                point, config.GRID_SPACING * i, bearing
            )
            new_point_negative = calculate_new_coordinates(
                point, config.GRID_SPACING * i * -1, bearing
            )
            plat, plon, _ = new_point_positive
            nlat, nlon, _ = new_point_negative
            positive_waypoints.append((plat, plon))
            negative_waypoints.append((nlat, nlon))
        # reverse positive waypoints
        positive_waypoints = list(reversed(positive_waypoints))
        potential_waypoints = positive_waypoints + [(lat, lon)] + negative_waypoints

        grid.append(potential_waypoints)
    return grid
