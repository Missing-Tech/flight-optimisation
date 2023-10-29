import util
import math 

# Equations from Wikipedia https://en.wikipedia.org/wiki/Great-circle_navigation

def __calculate_alpha1(phi1, phi2, delta):

    numerator = math.cos(phi2) * math.sin(delta)
    denominator = (math.cos(phi1) * math.sin(phi2)) - (math.sin(phi1) * math.cos(phi2) * math.cos(delta))

    alpha1 = math.atan2(numerator, denominator)

    return alpha1

def __calculate_central_angle(phi1, phi2, delta):
    numerator = math.sqrt(pow(((math.cos(phi1) * math.sin(phi2)) - math.sin(phi1)*math.cos(phi2) * math.cos(delta)),2) + pow((math.cos(phi2) * math.sin(delta)),2))
    denominator = ((math.sin(phi1) * math.sin(phi2)) + math.cos(phi1) * math.cos(phi2) * math.cos(delta))

    central_angle = math.atan2(numerator, denominator)
    return central_angle

# azimuth = alpha0
def __calculate_azimuth(alpha1, phi1):
    numerator = math.sin(alpha1) * math.cos(phi1)
    denominator = math.sqrt(math.cos(alpha1)**2 + (math.sin(alpha1)**2 * math.sin(phi1)**2))
    azimuth = math.atan2(numerator, denominator)
    return azimuth

def __calculate_angle_1(alpha1, phi1):
    if phi1 == 0 and alpha1 == math.pi / 2:
        return 0
    numerator = math.tan(phi1)
    denominator = math.cos(alpha1) 
    angle1 = math.atan2(numerator, denominator)
    return angle1

def __calculate_equator_longitude(azimuth, angle1, lamda1):
    numerator = math.sin(azimuth) * math.sin(angle1)
    denominator = math.cos(angle1)
    equator_longitude = lamda1 - math.atan2(numerator, denominator)
    return equator_longitude

def __find_point_distance_along_great_circle(distance, azimuth, equator_longitude):
    phi_numerator = math.cos(azimuth) * math.sin(distance)
    phi_denominator = math.sqrt(pow(math.cos(distance), 2) + (pow(math.sin(azimuth), 2) * pow(math.sin(distance), 2)))
    phi = math.atan2(phi_numerator, phi_denominator)
    lambda_numerator = math.sin(azimuth) * math.sin(distance)
    lambda_denominator = math.cos(distance)
    lambda1 = math.atan2(lambda_numerator, lambda_denominator) + equator_longitude

    phi = math.degrees(phi)
    lambda1 = math.degrees(lambda1)

    azimuth_numerator = math.tan(azimuth)
    azimuth_denominator = math.cos(distance) 
    local_azimuth = math.atan2(azimuth_numerator, azimuth_denominator)

    return (util.reduce_angle(phi), util.reduce_angle(lambda1), local_azimuth)

def calculate_path(radius, no_of_points, p1, p2):
    
    lat0, lon0, a1 = p1
    lat1, lon1, a2 = p2

    phi1 = math.radians(lat0)  
    lambda1 = math.radians(lon0)  
    phi2 = math.radians(lat1) 
    lambda2 = math.radians(lon1) 

    delta = lambda2 - lambda1 
    delta = util.reduce_angle(delta)

    alpha1 = __calculate_alpha1(phi1, phi2, delta)

    azimuth = __calculate_azimuth(alpha1, phi1)

    central_angle = __calculate_central_angle(phi1, phi2, delta)

    angle1 = __calculate_angle_1(alpha1, phi1)
    equator_longitude = __calculate_equator_longitude(azimuth, angle1, lambda1)

    points = [(lat1,lon1, 0), (lat0, lon0, 0)]

    for i in range(no_of_points):
        total_distance = radius * central_angle
        step = total_distance / no_of_points
        distance = angle1 + ((i * step) / radius)
        points.append(__find_point_distance_along_great_circle(distance, azimuth, equator_longitude))

    return points


