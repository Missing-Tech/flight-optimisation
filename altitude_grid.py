def calculate_altitude_grid(
    grid,
    base_altitude=30_000,
    altitude_step=2_000,
    max_altitude=40_000,
):
    def calculate_altitudes():
        altitudes = []
        current_altitude = base_altitude
        while current_altitude <= max_altitude:
            altitudes.append(current_altitude)
            current_altitude += altitude_step
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
                    base_altitude + (index * altitude_step), max_altitude
                )
                if altitude > max_altitude_at_step:
                    step_points.append(None)
                    continue
                step_points.append(point)
            if len(step_points) > 0:
                altitude_grid[altitude].append(step_points)

    return altitude_grid
