class PerformanceModel:
    def __init__(self, config):
        from performance_model import AircraftPerformanceModel, ContrailGrid

        self.config = config
        self.apm = AircraftPerformanceModel(self.config)
        self.contrail_grid = ContrailGrid()

    def get_apm(self):
        return self.apm

    def get_weather_grid(self, altitude_grid):
        from weather_grid import WeatherGrid

        if self.weather_grid is None:
            self.weather_grid = WeatherGrid(altitude_grid, self.config)
        return self.weather_grid

    def get_cocip_manager(self):
        from cocip import CocipManager

        weather_grid = self.get_weather_grid()
        self.cocip_manager = CocipManager(weather_grid, self.config)
        return self.cocip_manager

    def get_contrail_grid(self, altitude_grid):
        from contrail_grid import ContrailGrid

        contrail_manager = self.get_contrail_grid_manager(altitude_grid)
        self.contrail_grid = ContrailGrid(contrail_manager)
        return self.contrail_grid

    def get_contrail_grid_manager(self, altitude_grid):
        from contrail_grid import ContrailGridManager

        if self.contrail_manager is None:
            self.contrail_manager = ContrailGridManager(altitude_grid, self.config)
        return self.contrail_manager
