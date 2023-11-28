import pandas as pd
import pycontrails as pc


def calculate_ef_from_flight_path(flight_path):
    latitudes = [point[0] for point in flight_path]
    longitudes = [point[1] for point in flight_path]
    altitudes = [point[2] for point in flight_path]

    attrs = {
        "flight_id": "fid",
        "aircraft_type": "A359",
        "wingspan": 64.75,
    }

    df = pd.DataFrame(
        {
            "longitude": longitudes,
            "latitude": latitudes,
            "altitude_ft": altitudes,
            "time": pd.date_range("2021-01-01T10", "2021-01-01T15", periods=21),
        }
    )

    fl = pc.Flight(data=df, flight_id=123)
