import geodesic_path as gp
import math
import util

class RoutingGrid:
    def __calculate_normal_vector(self, latitude, longitude, azimuth):
        # Convert latitude, azimuth, and longitude from degrees to radians
        latitude = math.radians(latitude)
        longitude = math.radians(longitude)
        azimuth = math.radians(azimuth)
        
        # Calculate the components of the normal vector
        x = math.cos(latitude) * math.cos(azimuth)
        y = math.cos(latitude) * math.sin(azimuth)
        z = math.sin(latitude)

        return (x,y,z)

    # Formula from https://www.movable-type.co.uk/scripts/latlong.html
    def __calculate_bearing(self, p1, p2):
        lat1, lon1, a1 = p1
        lat2, lon2, a2 = p2
        delta_lon = lon2 - lon1

        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        delta_lon = math.radians(delta_lon)

        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        y = math.sin(delta_lon) * math.cos(lat1)
        z = math.atan2(y, x) % (2 * math.pi) # Convert to range [0, 2pi]

        return z
    
    # Formula from https://www.movable-type.co.uk/scripts/latlong.html
    def __calculate_new_coordinates(self, p1, distance, bearing):

        lat1, lon1, a1 = p1

        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        
        lat2 = math.asin(math.sin(lat1) * math.cos(distance / util.R) + math.cos(lat1) * math.sin(distance / util.R) * math.cos(bearing))
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance / util.R) * math.cos(lat1), math.cos(distance / util.R) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2), bearing


    def calculate_routing_grid(self, grid_width, p1, p2, radius, no_of_points):
        path = gp.calculate_path(radius, no_of_points, p1, p2)
        grid = []
        for point in path:
            for i in range(1, grid_width + 1):
                index = path.index(point)

                if (index - i <= 0):
                    continue

                if (index + i > no_of_points):
                    continue

                if index+1 > no_of_points:
                    continue

                bearing = self.__calculate_bearing(path[index], path[index + i]) 
                bearing = (bearing + math.pi/2) % (2 * math.pi)


                distance = 100 # distance in km
                new_point_positive = self.__calculate_new_coordinates(point, distance * i, bearing)
                new_point_negative = self.__calculate_new_coordinates(point, distance * i * -1, bearing)
                grid.append(new_point_positive)
                grid.append(new_point_negative)
        return grid
