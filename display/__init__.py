from .maps import Maps
import matplotlib.pyplot as plt
from .blank import Blank


class Display:
    def __init__(self):
        self.maps = Maps()
        self.blank = Blank()

    def show(self):
        plt.show()
