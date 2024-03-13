import config


class AltitudeGrid:
    def __init__(self, routing_grid):
        self.base_altitude = config.STARTING_ALTITUDE
        self.altitude_step = config.ALTITUDE_STEP
        self.max_altitude = config.MAX_ALTITUDE
        self.routing_grid = routing_grid

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

    def get_altitude_grid(self):
        return self.calculate_altitude_grid(self.routing_grid.get_routing_grid())
