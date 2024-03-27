from collections import namedtuple

Point2D = namedtuple("Point2D", "lat lon")
Point3D = namedtuple("Point3D", "lat lon alt")
Point4D = namedtuple("Point4D", "lat lon alt time")
Path2D = list[Point2D]
Grid2D = list[list[Point2D]]
Grid3D = dict[list[Point2D]]
