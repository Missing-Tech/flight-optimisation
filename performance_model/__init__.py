from .apm import AircraftPerformanceModel
from .contrails import CocipManager, ContrailGridManager
from .weather import WeatherGrid


class PerformanceModel:
    def __init__(self, altitude_grid, config):
        self.config = config
        self.altitude_grid = altitude_grid

    def get_apm(self):
        if hasattr(self, "apm") is False:
            weather_grid = self.get_weather_grid()
            self.apm = AircraftPerformanceModel(weather_grid, self.config)
        return self.apm

    def get_weather_grid(self):
        if hasattr(self, "weather_grid") is False:
            self.weather_grid = WeatherGrid(self.altitude_grid, self.config)
            self.weather_grid.get_weather_grid()
        return self.weather_grid

    def get_cocip_manager(self):
        if hasattr(self, "cocip_manager") is False:
            weather_grid = self.get_weather_grid()
            self.cocip_manager = CocipManager(weather_grid, self.config)
        return self.cocip_manager

    def get_contrail_grid(self):
        if hasattr(self, "contrail_grid") is False:
            contrail_manager = self.get_contrail_grid_manager()
            self.contrail_grid = contrail_manager.contrail_grid
        return self.contrail_grid

    def get_contrail_grid_manager(self):
        if hasattr(self, "contrail_manager") is False:
            self.contrail_manager = ContrailGridManager(self.altitude_grid, self.config)
        return self.contrail_manager
