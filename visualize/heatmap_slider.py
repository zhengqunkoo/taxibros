import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from daemons.models import Timestamp
from daemons.convert import ConvertHeatmap
from scipy.ndimage.morphology import grey_dilation


class HeatmapSlider:

    def __init__(self, coordinates):
        """
        @param coordinates: list of coordinates.
        """
        self._coordinates = coordinates
        self._fig = plt.figure()
        self._ax = self._fig.add_subplot(111)

        acolor = "lightgoldenrodyellow"
        axbins = self._fig.add_axes([0.25, 0.05, 0.65, 0.03], facecolor=acolor)
        aybins = self._fig.add_axes([0.25, 0, 0.65, 0.03], facecolor=acolor)
        asigma = self._fig.add_axes([0.25, 0.1, 0.65, 0.03], facecolor=acolor)

        self._sxbins = Slider(axbins, "xbins", 1, 10000, valinit=4450, valfmt="%0.0f")
        self._sybins = Slider(aybins, "ybins", 1, 10000, valinit=2655, valfmt="%0.0f")
        self._ssigma = Slider(asigma, "sigma", 0, 100, valinit=30, valfmt="%0.0f")

    def show(self):
        self._sxbins.on_changed(self._update)
        self._sybins.on_changed(self._update)
        self._ssigma.on_changed(self._update)
        self._draw(self._sxbins.valinit, self._sybins.valinit, self._ssigma.valinit)
        self._ax.invert_yaxis()  # Invert only works after imshow().
        # TODO
        # plt.show() allows you to slide the sliders.
        # Can plt.show() but:
        #   blocks program flow.
        #   raises exceptions on exit.
        #   subprocesses still run even after quitting server with C-C.
        # So, savefig instead.
        plt.savefig("heatmap_slider.png")

    def _update(self, val):
        self._draw(self._sxbins.val, self._sybins.val, self._ssigma.val)

    def _draw(self, xbins, ybins, sigma):
        # Convert np.float64 to int.
        xbins = int(xbins)
        ybins = int(ybins)
        sigma = int(sigma)
        coo = ConvertHeatmap(xbins, ybins).convert(self._coordinates)
        heatmap = coo.toarray()
        heatmap = grey_dilation(heatmap, size=(sigma, sigma))
        self._ax.clear()
        self._ax.imshow(heatmap.T, cmap="hot", interpolation="nearest")
        self._fig.canvas.draw()
