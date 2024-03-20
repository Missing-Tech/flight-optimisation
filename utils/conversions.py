class Conversions:
    def __init__(self):
        pass

    # From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
    def calculate_altitude_ft_from_pressure(self, pressure):
        pressure_pa = pressure * 100  # Convert to Pa
        # Use the international barometric formula
        altitude = 44331.5 - 4946.62 * pressure_pa ** (0.190263)
        return altitude * 3.28084

    # From https://pvlib-python.readthedocs.io/en/v0.2.2/_modules/pvlib/atmosphere.html
    def calculate_pressure_from_altitude_ft(self, altitude_ft):
        # convert altitude to meters
        altitude_m = altitude_ft / 3.28084
        pressure = ((44331.514 - altitude_m) / 11880.516) ** (1 / 0.1902632)

        return pressure

    def convert_altitude_to_pressure_bounded(
        self, altitude, max_pressure, min_pressure
    ):
        pressure = self.calculate_pressure_from_altitude_ft(altitude)
        return max(min_pressure, min(pressure, max_pressure))
