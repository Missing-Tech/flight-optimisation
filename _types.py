from collections import namedtuple
from typing import TypedDict
import pandas as pd


class FlightPoint(TypedDict):
    longitude: float
    latitude: float
    altitude_ft: float
    altitude: float
    level: float
    thrust: float
    time: pd.Timestamp
    aircraft_mass: float


class Objectives(TypedDict):
    contrail: float
    co2: float
    time: float
    cocip: float


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
