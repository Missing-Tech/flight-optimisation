class Objective:
    def __init__(self, config, contrail_grid):
        self.weight = 1
        self.name = NotImplemented
        self.contrail_grid = contrail_grid

    def _run_objective_function(self, flight_path):
        return NotImplemented

    def calculate_objective(self, flight_path):
        return self._run_objective_function(flight_path) * self.weight

    def __str__(self):
        return self.name


class ContrailObjective(Objective):
    def __init__(self, config, contrail_grid):
        super().__init__(config, contrail_grid)
        self.name = "contrail"
        self.weight = config.CONTRAIL_WEIGHT

    def _run_objective_function(self, flight_path):
        contrail_ef = self.contrail_grid.interpolate_contrail_grid(flight_path)
        return contrail_ef


class CO2Objective(Objective):
    def __init__(self, config, contrail_grid):
        super().__init__(config, contrail_grid)
        self.name = "co2"
        self.weight = config.CO2_WEIGHT

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
    def __init__(self, config, contrail_grid):
        super().__init__(config, contrail_grid)
        self.name = "time"
        self.weight = config.TIME_WEIGHT

    def _run_objective_function(self, flight_path):
        flight_duration = (
            flight_path[-1]["time"] - flight_path[0]["time"]
        ).seconds / 3600
        return flight_duration
