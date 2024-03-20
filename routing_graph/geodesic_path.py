import numpy as np

# Equations from Wikipedia https://en.wikipedia.org/wiki/Great-circle_navigation


class GeodesicPath:
    def __init__(self, config):
        self.departure_airport = config.DEPARTURE_AIRPORT
        self.destination_airport = config.DESTINATION_AIRPORT
        self.no_of_points = config.NO_OF_POINTS
        self.config = config

    def reduce_angle(self, angle):
        while angle < -180:
            angle += 360
        while angle > 180:
            angle -= 360
        return angle

    def calculate_alpha1(self, phi1, phi2, delta):
        numerator = np.cos(phi2) * np.sin(delta)
        denominator = (np.cos(phi1) * np.sin(phi2)) - (
            np.sin(phi1) * np.cos(phi2) * np.cos(delta)
        )

        alpha1 = np.arctan2(numerator, denominator)

        return alpha1

    def calculate_central_angle(self, phi1, phi2, delta):
        numerator = np.sqrt(
            pow(
                (
                    (np.cos(phi1) * np.sin(phi2))
                    - np.sin(phi1) * np.cos(phi2) * np.cos(delta)
                ),
                2,
            )
            + pow((np.cos(phi2) * np.sin(delta)), 2)
        )
        denominator = (np.sin(phi1) * np.sin(phi2)) + np.cos(phi1) * np.cos(
            phi2
        ) * np.cos(delta)

        central_angle = np.arctan2(numerator, denominator)
        return central_angle

    def calculate_azimuth(self, alpha1, phi1):
        numerator = np.sin(alpha1) * np.cos(phi1)
        denominator = np.sqrt(
            np.cos(alpha1) ** 2 + (np.sin(alpha1) ** 2 * np.sin(phi1) ** 2)
        )
        azimuth = np.arctan2(numerator, denominator)
        return azimuth

    def calculate_angle_1(self, alpha1, phi1):
        if phi1 == 0 and alpha1 == np.pi / 2:
            return 0
        numerator = np.tan(phi1)
        denominator = np.cos(alpha1)
        angle1 = np.arctan2(numerator, denominator)
        return angle1

    def calculate_equator_longitude(self, azimuth, angle1, lamda1):
        numerator = np.sin(azimuth) * np.sin(angle1)
        denominator = np.cos(angle1)
        equator_longitude = lamda1 - np.arctan2(numerator, denominator)
        return equator_longitude

    def find_point_distance_along_great_circle(
        self, distance, azimuth, equator_longitude
    ):
        phi_numerator = np.cos(azimuth) * np.sin(distance)
        phi_denominator = np.sqrt(
            pow(np.cos(distance), 2)
            + (pow(np.sin(azimuth), 2) * pow(np.sin(distance), 2))
        )
        phi = np.arctan2(phi_numerator, phi_denominator)
        lambda_numerator = np.sin(azimuth) * np.sin(distance)
        lambda_denominator = np.cos(distance)
        lambda1 = np.arctan2(lambda_numerator, lambda_denominator) + equator_longitude

        phi = np.degrees(phi)
        lambda1 = np.degrees(lambda1)

        azimuth_numerator = np.tan(azimuth)
        azimuth_denominator = np.cos(distance)
        local_azimuth = np.arctan2(azimuth_numerator, azimuth_denominator)

        return (self.reduce_angle(phi), self.reduce_angle(lambda1), local_azimuth)

    def calculate_path(self, no_of_points, p1, p2):
        lat0, lon0 = p1
        lat1, lon1 = p2

        phi1 = np.radians(lat0)
        lambda1 = np.radians(lon0)
        phi2 = np.radians(lat1)
        lambda2 = np.radians(lon1)

        delta = lambda2 - lambda1
        delta = self.reduce_angle(delta)

        alpha1 = self.calculate_alpha1(phi1, phi2, delta)

        azimuth = self.calculate_azimuth(alpha1, phi1)

        central_angle = self.calculate_central_angle(phi1, phi2, delta)

        angle1 = self.calculate_angle_1(alpha1, phi1)
        equator_longitude = self.calculate_equator_longitude(azimuth, angle1, lambda1)

        points = [(lat0, lon0, 0)]

        total_distance = self.config.R * central_angle
        step = total_distance / no_of_points
        for i in range(1, no_of_points):
            distance = angle1 + ((i * step) / self.config.R)
            points.append(
                self.find_point_distance_along_great_circle(
                    distance, azimuth, equator_longitude
                )
            )

        points.append((lat1, lon1, 0))

        return points

    def get_geodesic_path(self):
        path = self.calculate_path(
            self.no_of_points, self.departure_airport, self.destination_airport
        )
        return path
