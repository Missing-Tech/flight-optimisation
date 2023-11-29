import pandas as pd
import pycontrails as pc
from pycontrails.models.cocip import Cocip
import ecmwf


def calculate_ef_from_flight_path(flight_path):
    flight_path_df = pd.DataFrame(flight_path)

    attrs = {
        "flight_id": 123,
        "aircraft_type": "E190",
        "engine_uid": "CF34-10E5",
        "engine_efficiency": 0.35,
        "nvpm_ei_n": 1.897462e15,
        "wingspan": 48,
        "n_engine": 2,
    }

    flight = pc.Flight(data=flight_path_df, flight_id=123, attrs=attrs)

    cocip = Cocip(ecmwf.met, ecmwf.rad)
    output_flight = cocip.eval(source=flight)
    df = output_flight.dataframe
    return df
