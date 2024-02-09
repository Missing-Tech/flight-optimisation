import os
import glob
import math
from datetime import datetime
from lxml import etree as ET

# From https://github.com/aleiby/kml2g1000

# Download path for FlightAware KML files.
srcDir = r""


# Returns an array containing the texts of all the specified child nodes of root.
def getAll(root, node):
    return [_.text for _ in root.iterfind(".//" + node, namespaces=root.nsmap)]


# Calculates the groundspeed given two lat/long coordinates and associated start/end datetimes.
def calcSpeed(fm, to, start, end):
    dx = math.hypot(*[b - a for a, b in zip(fm, to)]) * 60.0  # nautical miles
    dt = (end - start).total_seconds() / 3600.0  # hours
    return round(dx / dt) if dt else 0


# Converts a kml tracklog exported from flightaware.com to G1000 csv format.
def export(kml):

    # Skip if already exported
    base = os.path.splitext(kml)[0]
    fileName = base + ".csv"
    if os.path.exists(fileName):
        return

    print("Exporting " + fileName)

    # G1000 header, format, and trailing commas for data we do not set.
    hdr = "DateTime,Latitude,Longitude,AltMSL,GndSpd"
    fmt = "{datetime},{lat},{lng},{alt},{gspd}"

    tree = ET.parse(kml)
    root = tree.getroot()

    # Collect all the timestamps and breadcrumbs.
    whens = getAll(root, "when")
    coords = getAll(root, "gx:coord")

    # Export the csv header.
    csv = [hdr]

    # Export the csv data.
    fm = None
    start = None
    for when, coord in zip(whens, coords):
        # Parse data (e.g. 2022-06-09T15:42:34Z)
        date, time = when.split("T")
        time = time[:-1]  # strip Z
        lng, lat, alt = coord.split(" ")

        # Calculate ground speed.
        # ForeFlight will not accept a G1000 file without valid data here.
        # This is a very rough estimate based on the reported breadcrumbs.
        # FlightAware appears to collect actual data from ADS-B, but does not include it in the kml unfortuantely.
        to = (float(lat), float(lng))
        end = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
        gspd = calcSpeed(fm, to, start, end) if fm and start else 0
        fm = to
        start = end

        # FlightAware KLM altitude is in meters, while G1000 wants feet.
        alt = round(float(alt) * 3.28084)

        # Append data with trailing commas for unset values.
        csv.append(fmt.format(datetime=end, lat=lat, lng=lng, alt=alt, gspd=gspd))

    # Write file to disk.
    with open(fileName, "w") as f:
        f.writelines("\n".join(csv))


# Convert all files in source directory.
files = glob.glob(os.path.join(srcDir, "*.kml"))
for fileName in files:
    export(fileName)
