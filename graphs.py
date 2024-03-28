from matplotlib.patches import Patch
import numpy as np
from matplotlib.collections import PolyCollection
import shapely
import json
import pandas as pd


def show_objectives_over_time(display, objectives):
    blank = display.blank
    _, objective_axs = blank.create_fig(3, 1)

    # Show objectives over time
    blank.show_plot(
        objectives["contrail"],
        objective_axs[0],
        color="b",
        title="Lowest contrail EF over iterations",
        x_label="Iteration",
        y_label="EF",
    )
    blank.show_plot(
        objectives["co2"],
        objective_axs[1],
        color="r",
        title="Least kg of CO2 over iterations",
        x_label="Iteration",
        y_label="kg of CO2",
    )
    blank.show_plot(
        objectives["time"],
        objective_axs[2],
        color="g",
        title="Shortest time over iterations",
        x_label="Iteration",
        y_label="Time (s)",
    )


def show_flight_frames(
    display, real_flight_df, aco_path, random_path_df, contrail_grid, config
):
    maps = display.maps
    fig, map_axs = maps.create_fig(2, 2)

    fig.title = "Flight Path Comparison Over Time"

    time = aco_path["time"].min()
    aco_cutoff_df = get_path_before_time(aco_path, time)

    legend_patches = [
        Patch(color="blue", label="BA177 Flight Path"),
        Patch(color="green", label="Random Flight Path"),
        Patch(color="red", label="ACO Flight Path"),
    ]

    timestamps = contrail_grid["time"]
    fig.legend(handles=legend_patches)

    for ax in map_axs:
        flight_duration = real_flight_df["time"].max() - real_flight_df["time"].min()
        time_step = flight_duration / len(map_axs)
        time = time + pd.Timedelta(time_step)

        aco_cutoff_df = get_path_before_time(aco_path, time)
        random_cutoff_df = get_path_before_time(random_path_df, time)
        real_cutoff_df = get_path_before_time(real_flight_df, time)
        maps.show_path(real_cutoff_df, ax, color="blue", linewidth=2)
        maps.show_path(random_cutoff_df, ax, color="green", linewidth=2)
        maps.show_path(aco_cutoff_df, ax, color="red", linewidth=2)
        ax.set_title("Time: {}".format(time))
        #
        # Interpolate contrail grid data at the given timestamp
        nearest_timestamp_index = np.argmin(
            np.abs(timestamps - np.datetime64(time)).values
        )
        nearest_flight_level_index = np.argmin(
            np.abs(config.FLIGHT_LEVELS - (aco_cutoff_df["altitude_ft"].iloc[-1] / 100))
        )
        interpolated_grid = contrail_grid.isel(
            flight_level=nearest_flight_level_index, time=nearest_timestamp_index
        )
        maps.show_contrail_grid(interpolated_grid, ax)

    return fig


def get_path_before_time(path, time):
    time = pd.Timestamp(time)
    return path[path["time"] <= time]


def show_3d_flight_frames(
    display,
    real_flight_df,
    aco_path,
    random_path_df,
    contrail_polys,
    contrail_grid,
    config,
):
    def get_contrail_polys_at_time(contrail_polys, time):
        collections = {}
        polys = contrail_polys["polys"]
        for level in config.FLIGHT_LEVELS:
            patches = []
            for poly in polys:
                if (
                    poly["properties"]["level"] == level
                    and poly["properties"]["time"] == time
                ):
                    multipoly = shapely.from_geojson(json.dumps(poly))
                    for geom in multipoly.geoms:
                        geom = geom.simplify(0.3)
                        x, y = geom.exterior.coords.xy
                        patches.append(np.asarray(tuple(zip(x, y))))
            collection = PolyCollection(patches, facecolor="red", alpha=0.3)
            collections[level] = collection

        return collections

    def convert_time_string(time):
        new_time_str = np.datetime_as_string(time, unit="s") + "Z"
        return new_time_str

    maps = display.maps3d
    fig, map_axs = maps.create_fig(2, 2)

    fig.title = "3D Flight Path Comparison"

    time = aco_path["time"].min()
    aco_cutoff_df = get_path_before_time(aco_path, time)

    legend_patches = [
        Patch(color="blue", label="BA177 Flight Path"),
        Patch(color="green", label="Random Flight Path"),
        Patch(color="red", label="ACO Flight Path"),
    ]

    fig.legend(handles=legend_patches)

    for ax in map_axs:
        flight_duration = real_flight_df["time"].max() - real_flight_df["time"].min()
        time_step = flight_duration / len(map_axs)
        time = time + pd.Timedelta(time_step)

        aco_cutoff_df = get_path_before_time(aco_path, time)
        random_cutoff_df = get_path_before_time(random_path_df, time)
        real_cutoff_df = get_path_before_time(real_flight_df, time)
        maps.show_3d_path(real_cutoff_df, ax, color="blue", linewidth=2)
        maps.show_3d_path(random_cutoff_df, ax, color="green", linewidth=2)
        maps.show_3d_path(aco_cutoff_df, ax, color="red", linewidth=2)
        ax.set_title("Time: {}".format(time))

        timestamps = contrail_grid["time"]

        # Interpolate contrail grid data at the given timestamp
        nearest_timestamp_index = np.argmin(
            np.abs(timestamps - np.datetime64(time)).values
        )
        time_string = convert_time_string(
            contrail_grid["time"][nearest_timestamp_index].values
        )
        # Interpolate contrail grid data at the given timestamp
        polys_at_time = get_contrail_polys_at_time(contrail_polys, time_string)
        for level in polys_at_time:
            ax.add_collection3d(polys_at_time[level], zs=level * 100, zdir="z")

    return fig


def show_flight_path_comparison(
    display,
    geodesic_path,
    real_flight_df,
    chosen_pareto_path_df,
    random_path_df,
    pareto_set,
    fp_cocip,
    aco_cocip,
    rand_cocip,
):
    maps = display.maps
    fig, map_axs = maps.create_fig(3, 1)

    fig.title = "Flight Path Comparison"

    maps.show_path(geodesic_path, map_axs[0], color="k", linestyle="--")
    maps.show_path(real_flight_df, map_axs[0], color="blue", linewidth=2)
    maps.set_title(map_axs[0], "BA177 Flight Path - Jan 31 2024")

    maps.show_path(geodesic_path, map_axs[1], color="k", linestyle="--")
    maps.show_path(random_path_df, map_axs[1], color="green", linewidth=2)
    maps.set_title(map_axs[1], "Random Flight Path")

    maps.show_path(geodesic_path, map_axs[2], color="k", linestyle="--")
    maps.show_path(chosen_pareto_path_df, map_axs[2], color="red", linewidth=2)
    maps.set_title(map_axs[2], "ACO Flight Path")

    for ant_path in pareto_set:
        path_df = pd.DataFrame(ant_path.flight_path, columns=["latitude", "longitude"])
        maps.show_path(path_df, map_axs[2], color="gray", linewidth=0.5)

    maps.show_contrails(fp_cocip, map_axs[0])
    maps.show_contrails(rand_cocip, map_axs[1])
    maps.show_contrails(aco_cocip, map_axs[2])

    return fig
