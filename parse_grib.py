import xarray as xr

ds = xr.open_dataset("output.grib", engine="cfgrib")

# Using https://spire.com/tutorial/spire-weather-tutorial-intro-to-processing-grib2-data-with-python/

# Access wind vector data
u_component = ds["u"]
v_component = ds["v"]
w_component = ds["w"]

# Access temperature data
temperature = ds["t"]

# Access relative humidity
relative_humidity = ds["r"]

ds = ds.get(["u", "v", "w", "t", "r", "latitude", "longitude", "isobaricInhPa"])

df = ds.to_dataframe()

latitudes = df.index.get_level_values("latitude")
longitudes = df.index.get_level_values("longitude")
pressures = df.index.get_level_values("isobaricInhPa")


def center_longitudes(lon):
    return lon - 360 if lon > 180 else lon


remapped_longitudes = longitudes.map(center_longitudes)

df["longitude"] = remapped_longitudes
df["latitude"] = latitudes
df["pressure"] = pressures

df.to_csv("output_data.csv", index=False)
