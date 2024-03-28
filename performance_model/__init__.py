import xarray as xr
import typing

from .apm import AircraftPerformanceModel
from .contrails import CocipManager, ContrailGridManager, PSGridManager, ContrailGrid
from .weather import WeatherGrid
from .flight import RealFlight, Flight

if typing.TYPE_CHECKING:
    from config import Config
    from routing_graph import RoutingGraphManager, AltitudeGrid
    from _types import FlightPath


class PerformanceModel:
    def __init__(self, routing_graph_manager: "RoutingGraphManager", config: "Config"):
        """
        Wrapper for all the performance model classes
        """
        self.config: "Config" = config
        self.altitude_grid: "AltitudeGrid" = routing_graph_manager.get_altitude_grid()
        self.routing_graph_manager: "RoutingGraphManager" = routing_graph_manager
        self.get_apm()
        self.get_weather_grid()
        self.get_ps_grid()
        self.get_cocip_manager()
        self.get_contrail_grid_manager()
        self.get_contrail_grid()

    def run_apm(self, flight_path: "FlightPath") -> "FlightPath":
        """
        Runs the Aircraft Performance Model on a flight path
        """
        return self.apm.calculate_flight_characteristics(flight_path)

    def get_contrail_polys(self) -> xr.Dataset:
        """
        Gets contrail polygons
        """
        return self.contrail_manager.contrail_polys

    def get_ps_grid(self) -> PSGridManager:
        """
        Gets the PS grid
        """
        if hasattr(self, "ps_grid") is False:
            weather_grid = self.get_weather_grid()
            self.ps_grid = PSGridManager(weather_grid, self.config)
        return self.ps_grid

    def get_apm(self) -> AircraftPerformanceModel:
        """
        Gets the Aircraft Performance model
        """
        if hasattr(self, "apm") is False:
            weather_grid = self.get_weather_grid()
            self.apm = AircraftPerformanceModel(weather_grid, self.config)
        return self.apm

    def get_weather_grid(self) -> WeatherGrid:
        """
        Gets the weather grid
        """
        if hasattr(self, "weather_grid") is False:
            self.weather_grid = WeatherGrid(self.altitude_grid, self.config)
            self.weather_grid.get_weather_grid()
        return self.weather_grid

    def get_cocip_manager(self) -> CocipManager:
        """
        Gets the CoCiP manager
        """
        if hasattr(self, "cocip_manager") is False:
            weather_grid = self.get_weather_grid()
            self.cocip_manager = CocipManager(weather_grid, self.config)
        return self.cocip_manager

    def get_contrail_grid(self) -> ContrailGrid:
        """
        Gets the contrail grid
        """
        if hasattr(self, "contrail_grid") is False:
            contrail_manager = self.get_contrail_grid_manager()
            self.contrail_grid = contrail_manager.contrail_grid
        return self.contrail_grid

    def get_contrail_grid_manager(self) -> ContrailGridManager:
        """
        Gets the contrail grid manager
        """
        if hasattr(self, "contrail_manager") is False:
            self.contrail_manager = ContrailGridManager(self.altitude_grid, self.config)
        return self.contrail_manager
