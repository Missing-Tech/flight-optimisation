import numpy as np


class RoutingGrid:
    def __init__(self, geodesic_path, config):
        self.config = config
        self.path = geodesic_path

    def calculate_new_coordinates(self, p1, distance, bearing):
        lat1, lon1, _ = p1

        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)

        lat2 = np.arcsin(
            np.sin(lat1) * np.cos(distance / self.config.R)
            + np.cos(lat1) * np.sin(distance / self.config.R) * np.cos(bearing)
        )
        lon2 = lon1 + np.arctan2(
            np.sin(bearing) * np.sin(distance / self.config.R) * np.cos(lat1),
            np.cos(distance / self.config.R) - np.sin(lat1) * np.sin(lat2),
        )

        return np.degrees(lat2), np.degrees(lon2), bearing

    def calculate_normal_bearing(self, bearing):
        return (bearing + np.pi / 2) % (2 * np.pi)

    def calculate_bearing(self, p1, p2):
        lat1, lon1, _ = p1
        lat2, lon2, _ = p2
        delta_lon = lon2 - lon1

        lat1 = np.radians(lat1)
        lat2 = np.radians(lat2)
        delta_lon = np.radians(delta_lon)

        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(
            delta_lon
        )
        y = np.sin(delta_lon) * np.cos(lat1)
        z = np.arctan2(y, x) % (2 * np.pi)  # Convert to range [0, 2pi]

        return z

    def calculate_routing_grid(self):
        grid = []
        for point in self.path:
            lat, lon, _ = point
            positive_waypoints = []
            negative_waypoints = []
            potential_waypoints = []
            for i in range(1, self.config.GRID_WIDTH + 1):
                index = self.path.index(point)

                if index + (i / self.config.OFFSET_VAR) > len(self.path) - 1:
                    continue

                if index + 1 > len(self.path) - 1:
                    continue

                bearing = self.calculate_bearing(self.path[index], self.path[index + 1])
                bearing = self.calculate_normal_bearing(bearing)

                new_point_positive = self.calculate_new_coordinates(
                    point, self.config.GRID_SPACING * i, bearing
                )
                new_point_negative = self.calculate_new_coordinates(
                    point, self.config.GRID_SPACING * i * -1, bearing
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
        if not hasattr(self, "routing_grid"):
            self.routing_grid = self.calculate_routing_grid()
        return self.routing_grid
