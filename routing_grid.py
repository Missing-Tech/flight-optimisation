import geodesic_path as gp
import math

class RoutingGrid:
    def __calculate_normal_vector(self, latitude, azimuth, longitude):
        # Convert latitude, azimuth, and longitude from degrees to radians
        latitude = math.radians(latitude)
        azimuth = math.radians(azimuth)
        longitude = math.radians(longitude)
        
        # Calculate the components of the normal vector
        x = math.cos(latitude) * math.cos(azimuth)
        y = math.cos(latitude) * math.sin(azimuth)
        z = math.sin(latitude)

        return (z,y,x)
        

    def calculate_routing_grid(self, grid_width, grid_width_step, p1, p2, radius, no_of_points):
        path = gp.calculate_path(radius, no_of_points, p1, p2)
        grid = []
        for point in path:
            for i in range(grid_width):
                normal_vector = self.__calculate_normal_vector(point[0], point[1], point[2]) 
                new_point_positive = (point[0] + normal_vector[0] * i, point[1] + normal_vector[1] * i, point[2] + normal_vector[2] * i)
                new_point_negative = (point[0] - normal_vector[0] * i, point[1] - normal_vector[1] * i, point[2] - normal_vector[2] * i)
                grid.append(new_point_positive)
                grid.append(new_point_negative)
        return grid
