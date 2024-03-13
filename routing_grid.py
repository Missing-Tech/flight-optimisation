import util
import config
import geodesic_path as gp
import numpy as np


class RoutingGrid:
    def __init__(self):
        self.path = gp.get_geodesic_path()

    def calculate_new_coordinates(self, p1, distance, bearing):
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

    def calculate_routing_grid(self):
        grid = []
        for point in self.path:
            lat, lon, _ = point
            positive_waypoints = []
            negative_waypoints = []
            potential_waypoints = []
            for i in range(1, config.GRID_WIDTH + 1):
                index = self.path.index(point)

                if index + (i / config.OFFSET_VAR) > len(self.path) - 1:
                    continue

                if index + 1 > len(self.path) - 1:
                    continue

                bearing = util.calculate_bearing(self.path[index], self.path[index + 1])
                bearing = util.calculate_normal_bearing(bearing)

                new_point_positive = self.calculate_new_coordinates(
                    point, config.GRID_SPACING * i, bearing
                )
                new_point_negative = self.calculate_new_coordinates(
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

    def get_routing_grid(self):
        return self.calculate_routing_grid()
