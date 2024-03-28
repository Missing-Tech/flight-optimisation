import typing
from utils import Conversions

if typing.TYPE_CHECKING:
    from _types import Grid2D, Grid3D, IndexPoint3D, FlightPoint
    from config import Config


class AltitudeGrid:
    """
    A class representing an altitude grid based on a routing grid
    """

    def __init__(self, routing_grid: "Grid2D", config: "Config"):
        """
        Constructs an AltitudeGrid object from a routing grid
        """
        self.config: "Config" = config
        self.base_altitude: int = self.config.STARTING_ALTITUDE
        self.altitude_step: int = self.config.ALTITUDE_STEP
        self.max_altitude_var: int = self.config.MAX_ALTITUDE_VAR
        self.max_altitude: int = self.config.MAX_ALTITUDE
        self.routing_grid: "Grid2D" = routing_grid.get_routing_grid()
        self.altitude_grid: "Grid3D" = self.calculate_altitude_grid(self.routing_grid)

    def calculate_altitude_grid(self, grid: "Grid2D") -> "Grid3D":
        """
        Calculates which points are reachable at each altitude, and constructs the grid object
        """

        def calculate_altitudes() -> list[int]:
            altitudes = []
            current_altitude = self.base_altitude
            while current_altitude <= self.max_altitude:
                altitudes.append(current_altitude)
                current_altitude += self.altitude_step
            return altitudes

        altitudes = calculate_altitudes()
        altitude_grid = {}

        for altitude in altitudes:
            altitude_grid[altitude] = []
            for step in grid:
                step_points = []
                for point in step:
                    index = grid.index(step)
                    max_altitude_at_step = min(
                        self.base_altitude + (index * self.max_altitude_var),
                        self.max_altitude,
                    )
                    if altitude > max_altitude_at_step:
                        step_points.append(None)
                        continue
                    step_points.append(point)
                if len(step_points) > 0:
                    altitude_grid[altitude].append(step_points)

        return altitude_grid

    def convert_index_to_point(self, index: "IndexPoint3D") -> "FlightPoint":
        """
        Converts an IndexPoint to a FlightPoint
        """
        thrust = self.config.NOMINAL_THRUST
        altitude_point = self.altitude_grid[index[2]][index[0]][index[1]]
        path_point = {
            "latitude": altitude_point[0],
            "longitude": altitude_point[1],
            "altitude_ft": index[2],
            "thrust": thrust,
            "level": Conversions().convert_altitude_to_pressure_bounded(
                index[2],
                self.config.PRESSURE_LEVELS[-1],
                self.config.PRESSURE_LEVELS[0],
            ),
        }
        return path_point

    def __iter__(self) -> "iter":
        return iter(self.altitude_grid)

    def __getitem__(self, key: int) -> "Grid2D":
        return self.altitude_grid[key]

    def __setitem__(self, key: int, value: "Grid2D") -> None:
        self.altitude_grid[key] = value
