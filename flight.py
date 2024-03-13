import util
import config


class Flight:
    def __init__(self, altitude_grid, routing_graph, performance_model):
        self.altitude_grid = altitude_grid
        self.routing_graph = routing_graph
        self.performance_model = performance_model
        self.flight_path = []
        self.indices = []
        self.objectives = None

    def set_departure(self, departure):
        self.indices.append(departure)
        point = util.convert_index_to_point(
            departure, self.altitude_grid, self.routing_graph
        )
        point["time"] = config.DEPARTURE_DATE
        point["aircraft_mass"] = config.STARTING_WEIGHT
        self.flight_path.append(point)

    def add_point_from_index(self, index):
        self.indices.append(index)
        point = util.convert_index_to_point(
            index, self.altitude_grid, self.routing_graph
        )

        point["course"] = 0
        point["climb_angle"] = 0

        self.flight_path = (
            self.performance_model.calculate_flight_characteristics_for_next_point(
                self.flight_path, point
            )
        )

    def set_objective_value(self, objective_values):
        self.objectives = objective_values
