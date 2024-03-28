import numpy as np
import typing

if typing.TYPE_CHECKING:
    from config import Config
    from _types import Point2D, Path2D


class GeodesicPath(list):
    """
    A class representing the geodesic path between two points.
    """

    def __init__(self, config: "Config"):
        """
        Initializes the GeodesicPath object.
        """
        self.departure_airport: Point2D = config.DEPARTURE_AIRPORT
        self.destination_airport: Point2D = config.DESTINATION_AIRPORT
        self.no_of_points: int = config.NO_OF_POINTS
        self.config: "Config" = config
        self.path: "Path2D" = self.calculate_path(
            self.no_of_points, self.departure_airport, self.destination_airport
        )
        super().__init__(self.path)

    def reduce_angle(self, angle: float) -> float:
        """
        Reduces an angle to the range -180 to 180 degrees.
        """
        while angle < -180:
            angle += 360
        while angle > 180:
            angle -= 360
        return angle

    def calculate_alpha1(self, phi1: float, phi2: float, delta: float) -> float:
        """
        Calculates the initial alpha angle.
        """
        numerator = np.cos(phi2) * np.sin(delta)
        denominator = (np.cos(phi1) * np.sin(phi2)) - (
            np.sin(phi1) * np.cos(phi2) * np.cos(delta)
        )

        alpha1 = np.arctan2(numerator, denominator)

        return alpha1

    def calculate_central_angle(self, phi1: float, phi2: float, delta: float) -> float:
        """
        Calculates the central angle (through the Earth's core) between two points.
        """
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

    def calculate_azimuth(self, alpha1: float, phi1: float) -> float:
        """
        Calculates the azimuth based off the longitude and the initial alpha angle.
        """
        numerator = np.sin(alpha1) * np.cos(phi1)
        denominator = np.sqrt(
            np.cos(alpha1) ** 2 + (np.sin(alpha1) ** 2 * np.sin(phi1) ** 2)
        )
        azimuth = np.arctan2(numerator, denominator)
        return azimuth

    def calculate_angle_1(self, alpha1: float, phi1: float) -> float:
        """
        Calculates the angle between the alpha1 and the longitude.
        """
        if phi1 == 0 and alpha1 == np.pi / 2:
            return 0
        numerator = np.tan(phi1)
        denominator = np.cos(alpha1)
        angle1 = np.arctan2(numerator, denominator)
        return angle1

    def calculate_equator_longitude(
        self, azimuth: float, angle1: float, lamda1: float
    ) -> float:
        """
        Calculate the longitude at the intersection with the equator.
        """
        numerator = np.sin(azimuth) * np.sin(angle1)
        denominator = np.cos(angle1)
        equator_longitude = lamda1 - np.arctan2(numerator, denominator)
        return equator_longitude

    def find_point_distance_along_great_circle(
        self, distance: float, azimuth: float, equator_longitude: float
    ) -> "Point2D":
        """
        Find a lat/lon point a certain distance along the great circle path.
        """
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

        return "Point2D"(self.reduce_angle(phi), self.reduce_angle(lambda1))

    def calculate_path(
        self, no_of_points: int, p1: "Point2D", p2: "Point2D"
    ) -> "Path2D":
        """
        Calculates the geodesic path with several points evenly spaced between two points.
        """
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

        points = "Path2D"(lat0, lon0)

        total_distance = self.config.R * central_angle
        step = total_distance / no_of_points
        for i in range(1, no_of_points):
            distance = angle1 + ((i * step) / self.config.R)
            points.append(
                self.find_point_distance_along_great_circle(
                    distance, azimuth, equator_longitude
                )
            )

        points.append("Point2D"(lat1, lon1))

        return points
