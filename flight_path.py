import random


def generate_random_flight_path(altitude_grid):
    def get_consecutive_points(
        xi,
        yi,
        altitude,
        grid,
        max_lateral_var=2,
        max_altitude_var=2_000,
        altitude_step=2_000,
    ):
        if xi == len(grid[altitude]) - 1:
            return None
        min_i = max(yi - max_lateral_var, 0)
        max_i = min(yi + max_lateral_var, len(grid[altitude][xi]) - 1)
        # points = grid[altitude][xi + 1][min_i : max_i + 1]
        points = []
        if max_i > 0:
            for i in range(min_i, max_i + 1):
                points.append((xi + 1, i))
        else:
            points.append((xi + 1, 0))

        max_alt = altitude + max_altitude_var  # Adding 4000 feet
        min_alt = altitude - max_altitude_var  # Subtracting 4000 feet
        max_alt = max(30000, min(max_alt, 40000))  # Cap between 30000 and 40000
        min_alt = max(30000, min_alt)  # Cap between 30000 and 40000

        altitude_points = []
        current_altitude = min_alt
        while current_altitude <= max_alt and current_altitude >= min_alt:
            for point in points:
                altitude_points.append((*point, current_altitude))
            current_altitude += altitude_step

        return altitude_points

    flight_path = []

    currentYi = 0
    currentAltitude = 30_000
    for currentXi in range(len(altitude_grid[currentAltitude]) - 1):
        points = get_consecutive_points(
            currentXi, currentYi, currentAltitude, altitude_grid
        )
        next_point = random.choice(points)

        currentXi = next_point[0]
        currentAltitude = next_point[2]
        currentYi = min(
            next_point[1], len(altitude_grid[currentAltitude][currentXi]) - 1
        )

        point = altitude_grid[currentAltitude][currentXi][currentYi]
        point = {
            "latitude": point[0],
            "longitude": point[1],
            "altitude": currentAltitude,
        }
        flight_path.append(point)

    return flight_path
