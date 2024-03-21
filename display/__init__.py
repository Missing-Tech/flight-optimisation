from .maps import Map
import matplotlib.pyplot as plt
from .blank import Blank


class Display:
    def __init__(self):
        self.maps = Map()
        self.blank = Blank()

    def show(self):
        plt.show()
