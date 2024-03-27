import pandas as pd

from pycontrails import Flight

from datetime import datetime


def convert_real_flight_path(flight_path):
    path = []
    for _, row in flight_path.iterrows():
        time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M:%S")
        path_point = {
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "altitude_ft": row["AltMSL"],
            "thrust": 0.83,
            "time": time,
        }

        path.append(path_point)

    return path


real_flight = pd.read_csv("data/jan-31.csv")
real_flight = real_flight[real_flight["AltMSL"] > 30000]
real_flight = convert_real_flight_path(real_flight)
real_flight = pd.DataFrame(real_flight)
flight = Flight(real_flight)

flight = flight.clean_and_resample(nominal_rocd=20)

fl_df = flight.dataframe
# convert altitude to ft
fl_df["altitude_ft"] = fl_df["altitude"] * 3.28084

# save csv
fl_df.to_csv("data/jan-31-cleaned.csv", index=False)
