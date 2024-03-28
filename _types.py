from collections import namedtuple
from typing import TypedDict
import pandas as pd


class FlightPoint(TypedDict):
    longitude: float
    latitude: float
    altitude_ft: float
    altitude: float or None
    level: float or None
    thrust: float or None
    time: pd.Timestamp or None
    aircraft_mass: float or None
    segment_length: float or None
    course: float or None
    climb_angle: float or None
    true_airspeed: float or None
    heading: float or None
    ground_speed: float or None
    fuel_flow: float or None
    CO2: float or None


class Objectives(TypedDict):
    contrail: float or None
    co2: float or None
    time: float or None
    cocip: float or None


FlightPath = list[FlightPoint]

WindVector = namedtuple("WindVector", "u v")

IndexPoint3D = namedtuple("IndexPoint3D", "lat lon alt")
IndexPath = list[IndexPoint3D]

Point2D = namedtuple("Point2D", "lat lon")
Point3D = namedtuple("Point3D", "lat lon alt")
Point4D = namedtuple("Point4D", "lat lon alt time")

Path2D = list[Point2D]
Grid2D = list[list[Point2D]]
Grid3D = dict[int, Grid2D]
