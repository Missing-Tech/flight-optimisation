import cartopy.crs as ccrs
from cartopy.feature import BORDERS, COASTLINE
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from cartopy.mpl.patch import geos_to_path
import itertools
import numpy as np


class Map:
    def __init__(self, crs=None):
        # self.crs = ccrs.NearsidePerspective(central_latitude=51, central_longitude=-35)
        self.crs = ccrs.PlateCarree()

    def create_fig(self, grid_width, grid_height):
        fig = plt.figure(figsize=(12.8, 9.6), dpi=100)
        fig.tight_layout()
        axs = []
        for i in range(1, grid_width * grid_height + 1):
            ax = self._create_map(fig, f"{grid_height}{grid_width}{i}")
            axs.append(ax)
        return fig, axs

    def _create_map(self, fig, grid_pos):
        ax = fig.add_subplot(int(grid_pos), projection=self.crs)
        ax.set_extent([10, -90, 25, 60])
        ax.add_feature(BORDERS, lw=0.5, color="gray")
        ax.gridlines(draw_labels=True, color="gray", alpha=0.5, ls="--")
        ax.coastlines(resolution="50m", lw=0.5, color="gray")
        return ax

    def show_path(self, path, ax, color="green", linewidth=1, linestyle="solid"):
        return ax.plot(
            path["longitude"],
            path["latitude"],
            transform=self.crs,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
        )

    def set_title(self, ax, title):
        ax.set_title(title)

    def show_contrails(self, cocip, ax):
        if cocip.contrail is None:
            return

        cocip.contrail.plot.scatter(
            "longitude",
            "latitude",
            c="ef",
            vmin=-1e12,
            vmax=1e12,
            transform=self.crs,
            cmap="coolwarm",
            ax=ax,
        )

    def show_contrail_grid(self, contrail_grid, ax):
        ax.pcolormesh(
            contrail_grid["longitude"],
            contrail_grid["latitude"],
            contrail_grid["ef_per_m"].transpose(),
            shading="gourard",
            vmin=-1e9,
            vmax=1e9,
            cmap="coolwarm",
            transform=ccrs.PlateCarree(),
        )

    def show_grid(self, grid, ax, color="blue", s=0.2):
        return ax.scatter(
            grid["longitude"],
            grid["latitude"],
            transform=ccrs.PlateCarree(),
            color=color,
            s=s,
        )


class Map3D(Map):
    def __init__(self, crs=None):
        pass

    def _create_map(self, fig, grid_pos):
        ax = fig.add_subplot(int(grid_pos), projection="3d")

        lc = self.extract_map_geometry()
        ax.add_collection3d(lc, zs=30_000, zdir="z")

        ax.set_zlim(30000, 40000)
        ax.set_xlim(-75, 10)
        ax.set_ylim(35, 65)

        return ax

    def extract_map_geometry(self):
        coastline_geoms = COASTLINE.geometries()

        target_projection = ccrs.PlateCarree()
        geoms = [
            target_projection.project_geometry(geom, COASTLINE.crs)
            for geom in coastline_geoms
        ]
        paths = list(
            itertools.chain.from_iterable(geos_to_path(geom) for geom in geoms)
        )

        segments = []
        for path in paths:
            vertices = [vertex for vertex, _ in path.iter_segments()]
            vertices = np.asarray(vertices)
            segments.append(vertices)

        lc = LineCollection(segments, color="black", linewidth=0.5)
        return lc

    # Function to display altitude grid as 3D scatter plot
    # Method from https://stackoverflow.com/questions/23785408/3d-cartopy-similar-to-matplotlib-basemap
    def show_3d_grid(self, grid, ax):
        ax.scatter(
            grid["latitude"],
            grid["longitude"],
            grid["altitude"],
            c=grid["altitude"],  # Use altitude for color gradient
            cmap="viridis",  # Choose colormap for altitude
            marker="o",  # Set marker style
            alpha=0.2,
            depthshade=True,  # Enable depth shading for better visualization
        )

        ax.set_zlim(bottom=28_000)

        # Set labels for axes
        ax.set_xlabel("longitude")
        ax.set_ylabel("latitude")
        ax.set_zlabel("altitude")

        return ax

    def show_3d_path(self, flight_path, ax, color="k", linewidth=1):
        return ax.plot(
            flight_path["longitude"],
            flight_path["latitude"],
            flight_path["altitude_ft"],
            color=color,
            linewidth=linewidth,
        )
