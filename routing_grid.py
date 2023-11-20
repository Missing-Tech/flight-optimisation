import util


def calculate_routing_grid(
    grid_width, path, base_altitude=30_000, altitude_steps=[2_000, 4_000, 6_000]
):
    def calculate_altitudes():
        altitudes = [base_altitude]
        for altitude in altitude_steps:
            altitudes.append(base_altitude + altitude)
        return altitudes

    def calculate_altitude_waypoints(waypoints):
        altitude_waypoints = []
        for altitude in calculate_altitudes():
            for waypoint in waypoints:
                lat, lon = waypoint
                altitude_waypoints.append((lat, lon, altitude))
        return altitude_waypoints

    grid = []
    for point in path:
        lat, lon, _ = point
        positive_waypoints = []
        negative_waypoints = []
        potential_waypoints = []
        for i in range(1, grid_width + 1):
            index = path.index(point)

            if index - i <= 0:
                continue

            if index + i > len(path) - 1:
                continue

            bearing = util.calculate_bearing(path[index], path[index + i])
            bearing = util.calculate_normal_bearing(bearing)

            distance = 100  # distance in km
            new_point_positive = util.calculate_new_coordinates(
                point, distance * i, bearing
            )
            new_point_negative = util.calculate_new_coordinates(
                point, distance * i * -1, bearing
            )
            plat, plon, _ = new_point_positive
            nlat, nlon, _ = new_point_negative
            positive_waypoints.append((plat, plon))
            negative_waypoints.append((nlat, nlon))
        potential_waypoints = positive_waypoints + [(lat, lon)] + negative_waypoints
        altitude_waypoints = calculate_altitude_waypoints(potential_waypoints)
        grid.append(altitude_waypoints)
    return grid
