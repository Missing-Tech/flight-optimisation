from utils import Conversions


class AltitudeGrid:
    def __init__(self, routing_grid, config):
        self.config = config
        self.base_altitude = self.config.STARTING_ALTITUDE
        self.altitude_step = self.config.ALTITUDE_STEP
        self.max_altitude = self.config.MAX_ALTITUDE
        self.routing_grid = routing_grid.get_routing_grid()
        self.altitude_grid = self.calculate_altitude_grid(self.routing_grid)

    def calculate_altitude_grid(self, grid):
        def calculate_altitudes():
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
                        self.base_altitude + (index * self.altitude_step),
                        self.max_altitude,
                    )
                    if altitude > max_altitude_at_step:
                        step_points.append(None)
                        continue
                    step_points.append(point)
                if len(step_points) > 0:
                    altitude_grid[altitude].append(step_points)

        return altitude_grid

    def convert_index_to_point(self, index):
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

    def __getitem__(self, key):
        return self.altitude_grid[key]

    def __setitem__(self, key, value):
        self.altitude_grid[key] = value
