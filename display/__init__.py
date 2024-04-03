from .maps import Map, Map3D
import matplotlib.pyplot as plt
from .blank import Blank, Blank3D


class Display:
    def __init__(self):
        self.maps = Map()
        self.maps3d = Map3D()
        self.blank = Blank()
        self.blank3d = Blank3D()

    def show(self):
        plt.show()
