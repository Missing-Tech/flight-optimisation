import util


def calculate_routing_grid(
    grid_width,
    path,
):
    grid = []
    for point in path:
        lat, lon, _ = point
        positive_waypoints = []
        negative_waypoints = []
        potential_waypoints = []
        for i in range(1, grid_width + 1):
            index = path.index(point)

            if index - i < 0:
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
        # reverse positive waypoints
        positive_waypoints = list(reversed(positive_waypoints))
        potential_waypoints = positive_waypoints + [(lat, lon)] + negative_waypoints

        grid.append(potential_waypoints)
    return grid
