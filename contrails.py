import pandas as pd
import pycontrails as pc
from pycontrails.models.cocip import Cocip
import ecmwf
from pycontrails.models.humidity_scaling import ConstantHumidityScaling


def calculate_ef_from_flight_path(flight_path):
    flight_path_df = pd.DataFrame(flight_path)

    attrs = {
        "flight_id": 123,
        "aircraft_type": "A320",
        "engine_uid": "CFM56-5B6",
        "engine_efficiency": 0.35,
        "nvpm_ei_n": 1.897462e15,
        "wingspan": 48,
        "n_engine": 2,
    }

    flight = pc.Flight(data=flight_path_df, flight_id=123, attrs=attrs)
    params = {
        "process_emissions": False,
        "verbose_outputs": True,
        "humidity_scaling": ConstantHumidityScaling(rhi_adj=0.98),
    }
    cocip = Cocip(ecmwf.met, ecmwf.rad, params=params)
    output_flight = cocip.eval(source=flight)

    df = output_flight.dataframe
    if not df['ef'].empty:
        ef = df['ef'].sum()
    else:
        ef = 0
    # return df
    return ef, df, cocip


# TODO: Implement 4D contrail formation fields for quicker lookup
