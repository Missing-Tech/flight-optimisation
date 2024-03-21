import matplotlib.pyplot as plt


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
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
