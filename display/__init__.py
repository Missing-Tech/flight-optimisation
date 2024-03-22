from .maps import Map, Map3D
import matplotlib.pyplot as plt
from .blank import Blank


class Display:
    def __init__(self):
        self.maps = Map()
        self.maps3d = Map3D()
        self.blank = Blank()

    def show(self):
        plt.show()
