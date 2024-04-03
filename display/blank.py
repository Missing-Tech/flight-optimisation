import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from itertools import cycle


class Blank:
    def __init__(self):
        pass

    def create_fig(self, grid_width, grid_height):
        fig = plt.figure()
        axs = []
        for i in range(1, grid_width * grid_height + 1):
            ax = self._create_plot(fig, f"{grid_height}{grid_width}{i}")
            axs.append(ax)
        return fig, axs

    def _create_plot(self, fig, grid_pos):
        ax = fig.add_subplot(int(grid_pos))
        return ax

    def show_plot(
        self,
        x,
        ax,
        color="k",
        linewidth=1,
        linestyle="solid",
        x_label=None,
        y_label=None,
        title=None,
    ):
        ax.plot(
            x,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
        )
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)


class Blank3D(Blank):
    def show_front(self, front, ax):
        ax.plot(front["co2"], front["contrail"], front["time"], "ro")
        ax.set_xlabel("CO2")
        ax.set_ylabel("Contrail EF")
        ax.set_zlabel("Time")
        ax.set_title("Pareto Front")

    def compare_fronts(self, fronts, ax):
        cycol = cycle(
            [
                "turquoise",
                "darkorchid",
                "coral",
                "greenyellow",
                "hotpink",
                "gold",
                "royalblue",
            ]
        )
        cysym = cycle("o^s*P")
        for front in fronts:
            ax.plot(
                front["co2"],
                front["contrail"],
                front["time"],
                next(cysym),
                color=next(cycol),
                label=front.name,
            )

        ax.set_xlabel("CO2")
        ax.set_ylabel("Contrail EF")
        ax.set_zlabel("Time")
        ax.set_xlim([5.6e6, 7e6])
        ax.set_ylim([0, 2.5e15])
        ax.set_zlim([6, 7])
        ax.set_title("Pareto Front")
        ax.legend()

    def _create_plot(self, fig, grid_pos):
        ax = fig.add_subplot(int(grid_pos), projection="3d")
        return ax
