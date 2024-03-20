from performance_model import (
    ContrailGrid,
    CocipManager,
    ContrailGridManager,
    WeatherGrid,
    AircraftPerformanceModel,
)


class PeformanceModel:
    def __init__(self, config):
        self.config = config
        self.apm = AircraftPerformanceModel(self.config)
        self.contrail_grid = ContrailGrid()

    def get_apm(self):
        return self.apm

    def get_weather_grid(self, altitude_grid):
        if self.weather_grid is None:
            self.weather_grid = WeatherGrid(altitude_grid)
        return self.weather_grid

    def get_cocip_manager(self):
        weather_grid = self.get_weather_grid()
        self.cocip_manager = CocipManager(weather_grid)
        return self.cocip_manager

    def get_contrail_grid(self, altitude_grid):
        contrail_manager = self.get_contrail_grid_manager(altitude_grid)
        self.contrail_grid = ContrailGrid(contrail_manager)
        return self.contrail_grid

    def get_contrail_grid_manager(self, altitude_grid):
        if self.contrail_manager is None:
            self.contrail_manager = ContrailGridManager(altitude_grid)
        return self.contrail_manager
