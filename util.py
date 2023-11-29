import numpy as np
import cfgrib

R = 6371  # Earth radius in km
ds = cfgrib.open_dataset("output.grib")


def reduce_angle(angle):
    while angle < -180:
        angle += 360
    while angle > 180:
        angle -= 360
    return angle


def calculate_normal_bearing(bearing):
    return (bearing + np.pi / 2) % (2 * np.pi)


# Formula from https://www.movable-type.co.uk/scripts/latlong.html
def calculate_bearing(p1, p2):
    lat1, lon1, _ = p1
    lat2, lon2, _ = p2
    delta_lon = lon2 - lon1

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    delta_lon = np.radians(delta_lon)

    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)
    y = np.sin(delta_lon) * np.cos(lat1)
    z = np.arctan2(y, x) % (2 * np.pi)  # Convert to range [0, 2pi]

    return z


# Formula from https://www.movable-type.co.uk/scripts/latlong.html
def calculate_new_coordinates(p1, distance, bearing):
    lat1, lon1, _ = p1

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.arcsin(
        np.sin(lat1) * np.cos(distance / R)
        + np.cos(lat1) * np.sin(distance / R) * np.cos(bearing)
    )
    lon2 = lon1 + np.arctan2(
        np.sin(bearing) * np.sin(distance / R) * np.cos(lat1),
        np.cos(distance / R) - np.sin(lat1) * np.sin(lat2),
    )

    return np.degrees(lat2), np.degrees(lon2), bearing


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_altitude_ft_from_pressure(pressure):
    # Use the international barometric formula
    altitude = 44331.5 - 4946.62 * pressure ** (0.190263)
    return altitude


# From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
def calculate_pressure_from_altitude_ft(altitude_ft):
    pressure = 100 * ((44331.514 - altitude_ft) / 11880.516) ** (1 / 0.1902632)

    return pressure


def get_nearest_value_from_list(value, list):
    return min(list, key=lambda x: abs(x - value))


def get_weather_data_at_point(point):
    nearest_point = ds.sel(
        latitude=point["latitude"], longitude=point["longitude"], method="nearest"
    )
    nearest_point = nearest_point.to_dataframe()
    return nearest_point


def get_pressure_levels():
    return ds["isobaricInhPa"].values


def get_wind_vector_at_point(point):
    weather_data = get_weather_data_at_point(point)
    pressure = calculate_pressure_from_altitude_ft(point["altitude_ft"])
    nearest_pressure = get_nearest_value_from_list(pressure, get_pressure_levels())
    u = weather_data.loc[nearest_pressure]["u"]
    v = weather_data.loc[nearest_pressure]["v"]

    return (u, v)


def get_temperature_at_point(point):
    weather_data = get_weather_data_at_point(point)
    pressure = calculate_pressure_from_altitude_ft(point["altitude_ft"])
    nearest_pressure = get_nearest_value_from_list(pressure, get_pressure_levels())

    temperature = weather_data.loc[nearest_pressure]["t"]
    return temperature
