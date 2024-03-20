class Objective:
    def __init__(self, weight):
        self.weight = weight
        self.name = NotImplemented

    def _run_objective_function(self, flight_path):
        return NotImplemented

    def calculate_objective(self, flight_path):
        return self._run_objective_function(flight_path) * self.weight

    def __str__(self):
        return self.name


class ContrailObjective(Objective):
    def __init__(self, contrail_grid, weight):
        super().__init__(weight)
        self.contrail_grid = contrail_grid
        self.name = "contrail"

    def _run_objective_function(self, flight_path):
        contrail_ef = self.contrail_grid.interpolate_contrail_grid(flight_path)
        return contrail_ef


class CO2Objective(Objective):
    def __init__(self, weight):
        super().__init__(weight)
        self.name = "co2"

    def _calculate_flight_duration(self, flight_path):
        return (flight_path[-1]["time"] - flight_path[0]["time"]).seconds / 3600

    def _run_objective_function(self, flight_path):
        co2_kg = (
            sum(point["CO2"] for point in flight_path)
            * self._calculate_flight_duration(flight_path)
            * 3600
            / 1000  # convert g/s to kg
        )
        return co2_kg


class TimeObjective(Objective):
    def __init__(self, weight):
        super().__init__(weight)
        self.name = "time"

    def _run_objective_function(self, flight_path):
        flight_duration = (
            flight_path[-1]["time"] - flight_path[0]["time"]
        ).seconds / 3600
        return flight_duration
