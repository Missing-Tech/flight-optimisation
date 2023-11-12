import numpy as np
import util

class RoutingGrid:
    def __calculate_normal_bearing(self, bearing):
        return (bearing + np.pi/2) % (2 * np.pi)

    # Formula from https://www.movable-type.co.uk/scripts/latlong.html
    def __calculate_bearing(self, p1, p2):
        lat1, lon1, a1 = p1
        lat2, lon2, a2 = p2
        delta_lon = lon2 - lon1

        lat1 = np.radians(lat1)
        lat2 = np.radians(lat2)
        delta_lon = np.radians(delta_lon)

        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)
        y = np.sin(delta_lon) * np.cos(lat1)
        z = np.arctan2(y, x) % (2 * np.pi) # Convert to range [0, 2pi]

        return z
    
    # Formula from https://www.movable-type.co.uk/scripts/latlong.html
    def __calculate_new_coordinates(self, p1, distance, bearing):

        lat1, lon1, a1 = p1

        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)
        
        lat2 = np.arcsin(np.sin(lat1) * np.cos(distance / util.R) + np.cos(lat1) * np.sin(distance / util.R) * np.cos(bearing))
        lon2 = lon1 + np.arctan2(np.sin(bearing) * np.sin(distance / util.R) * np.cos(lat1), np.cos(distance / util.R) - np.sin(lat1) * np.sin(lat2))

        return np.degrees(lat2), np.degrees(lon2), bearing


    def calculate_routing_grid(self, grid_width, path, no_of_points):
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
                bearing = self.__calculate_normal_bearing(bearing)

                distance = 100 # distance in km
                new_point_positive = self.__calculate_new_coordinates(point, distance * i, bearing)
                new_point_negative = self.__calculate_new_coordinates(point, distance * i * -1, bearing)
                grid.append(new_point_positive)
                grid.append(new_point_negative)
        return grid
    
