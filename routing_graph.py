import networkx as nx
import pandas as pd
import ecmwf
import config
import contrails as ct
import util
import os
import altitude_grid as ag
import geodesic_path as gp


def calculate_point_values(point, weather_grid, altitude):
    distance_from_departure = gp.calculate_distance_between_points(
        config.DEPARTURE_AIRPORT,
        (point[0], point[1]),
    )
    speed = (
        config.NOMINAL_THRUST * 343
    )  # times by speed of sound for rough speed estimate
    time_to_point = distance_from_departure * 1000 / speed
    time_at_point = config.DEPARTURE_DATE + pd.Timedelta(time_to_point, "s")

    point_values = {
        "latitude": point[0],
        "longitude": point[1],
        "level": util.convert_altitude_to_pressure_bounded(altitude),
        "time": time_at_point,
        "delta_time": time_to_point,
        "fuel_burned": pd.Timedelta(time_to_point, "s").seconds
        * config.NOMINAL_FUEL_FLOW,
    }

    weather_at_point = weather_grid.get_weather_data_at_point(point_values)

    temperature = weather_at_point["air_temperature"].values.item()
    u = weather_at_point["eastward_wind"].values.item()
    v = weather_at_point["northward_wind"].values.item()

    point_values["temperature"] = temperature
    point_values["u"] = u
    point_values["v"] = v

    return point_values


def calculate_routing_graph(altitude_grid, contrail_grid, weather_grid):
    graph = nx.DiGraph()

    for altitude in altitude_grid:
        for step in altitude_grid[altitude]:
            for point in step:
                if point is None:
                    continue

                xi = altitude_grid[altitude].index(step)
                yi = step.index(point)

                consecutive_points = util.get_consecutive_points(
                    xi, yi, altitude, altitude_grid
                )

                point_values = calculate_point_values(point, weather_grid, altitude)
                contrails_at_point = max(
                    ct.interpolate_contrail_point(contrail_grid, (*point, altitude)),
                    0.01,
                )

                if consecutive_points is None:
                    continue
                for next_point in consecutive_points:
                    next_point_values = calculate_point_values(
                        next_point, weather_grid, next_point[2]
                    )
                    next_contrails_at_point = ct.interpolate_contrail_point(
                        contrail_grid, (*next_point, next_point[2])
                    )

                    graph.add_edge(
                        (xi, yi, altitude),
                        (next_point[0], next_point[1], next_point[2]),
                        contrail_pheromone=config.TAU_MAX,
                        co2_pheromone=config.TAU_MAX,
                        time_pheromone=config.TAU_MAX,
                    )
                    graph.add_node(
                        (xi, yi, altitude),
                        contrail_heuristic=contrails_at_point,
                        co2_heuristic=point_values["fuel_burned"],
                        time_heuristic=point_values["delta_time"],
                        temperature=point_values["temperature"],
                        u=point_values["u"],
                        v=point_values["v"],
                    )
                    next_lat, next_lon, _ = next_point
                    graph.add_node(
                        next_point,
                        contrail_heuristic=next_contrails_at_point,
                        co2_heuristic=next_point_values["fuel_burned"],
                        time_heuristic=next_point_values["delta_time"],
                        temperature=next_point_values["temperature"],
                        u=next_point_values["u"],
                        v=next_point_values["v"],
                    )

    return graph


def parse_node(s):
    # Assuming the input format is like '(0, 0, 31000)'
    parts = s.strip("()").split(",")
    return tuple(map(int, parts))


def get_routing_graph():
    # return calculate_routing_graph(
    #     altitude_grid,
    #     ct.get_contrail_grid(),
    #     ecmwf.MetAltitudeGrid(altitude_grid),
    # )
    if os.path.exists("data/routing_graph.gml"):
        return nx.read_gml("data/routing_graph.gml", destringizer=parse_node)
    else:
        altitude_grid = ag.get_altitude_grid()
        rg = calculate_routing_graph(
            altitude_grid,
            ct.get_contrail_grid(),
            ecmwf.MetAltitudeGrid(altitude_grid),
        )
        nx.write_gml(rg, "data/routing_graph.gml")
        return rg
