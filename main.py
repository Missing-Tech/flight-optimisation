import display
import flight_path as fp
import fiona
import config
import contrails as ct
import warnings
import geodesic_path as gp
import routing_grid as rg
import altitude_grid as ag
import ecmwf
import util
import aco
import routing_graph as rgraph
from cartopy import crs as ccrs
from dotenv import load_dotenv
import pandas as pd
from openap import FuelFlow

load_dotenv()

warnings.filterwarnings("ignore")

lat0, lon0 = config.DEPARTURE_AIRPORT
lat1, lon1 = config.DESTINATION_AIRPORT
distance_between_points = gp.calculate_distance_between_points(
    config.NO_OF_POINTS, (lat0, lon0, 0), (lat1, lon1, 0)
)

points = gp.calculate_path(config.NO_OF_POINTS, (lat0, lon0, 0), (lat1, lon1, 0))
grid = rg.calculate_routing_grid(points)
altitude_grid = ag.calculate_altitude_grid(grid)
weather_data = ecmwf.MetAltitudeGrid(altitude_grid)
contrail_grid = ct.download_contrail_grid(altitude_grid)
routing_graph = rgraph.calculate_routing_graph(altitude_grid, distance_between_points)

df = pd.read_csv("flight.csv")

fig1, ax1 = display.create_map_ax()
da = contrail_grid["ef_per_m"]
display.display_contrail_grid(da, ax1)

ax1.plot(
    df["Longitude"],
    df["Latitude"],
    color="red",
    linewidth=1,
    transform=ccrs.PlateCarree(),
)

ant_paths, best_path = aco.run_aco_colony(
    config.NO_OF_ITERATIONS,
    config.NO_OF_ANTS,
    routing_graph,
    altitude_grid,
    distance_between_points,
)

real_flight_path = util.convert_real_flight_path(df)
real_flight_path = fp.calculate_flight_characteristics(real_flight_path, weather_data)

ef1, contrails, cocip = ct.calculate_ef_from_flight_path(best_path)
display.display_contrails(contrails, cocip, ax=ax1)

ef2, contrails, cocip = ct.calculate_ef_from_flight_path(real_flight_path)
display.display_contrails(contrails, cocip, ax=ax1)


# for path in ant_paths:
#     display.display_optimised_path(path, ax1, linewidth=0.5)

display.display_optimised_path(best_path, ax1)


display.show()
