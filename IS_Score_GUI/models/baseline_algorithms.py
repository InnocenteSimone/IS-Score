import ramanspy as rp
import ramanspy.preprocessing as rpr

from functools import partial
from orpl.baseline_removal import bubblefill

PLACEHOLDERS = {
    "lam": "Lambda",
    "p": "p",
    "poly_order": "Poly Order",
    "min_bubble_widths": "Min Bubble Width"
}

class BaselineAlgorithm:
    def __init__(self, name, algorithm, params=None):
        self.name = name
        self.algorithm = algorithm
        self.params = params

    def getBaselineParams(self):
        return self.params

    def getBaselineParamsWithPlaceholders(self):
        if self.params is None:
            return None
        return [(el, PLACEHOLDERS[el]) for el in self.params]

    def setParams(self, params):
        self.algorithm.kwargs.update(params)

    def apply(self, spectrum, axis=None):
        if axis is None:
            corr = self.algorithm.apply(spectrum)
        else:
            corr = self.algorithm.apply(rp.Spectrum(spectral_axis=axis, spectral_data=spectrum))
        return corr.spectral_data

    def getAlgorithm(self, params):
        self.algorithm.kwargs.update(params)
        return self.algorithm.apply

class BubbleFillAlgorithm(BaselineAlgorithm):
    def __init__(self, name, algorithm, params=None):
        super().__init__(name, algorithm, params)

    def setParams(self, params):
        self.algorithm = partial(bubblefill, **params)

    def apply(self, spectrum, axis=None):
        if axis is None:
            raman, _ = self.algorithm(spectrum.spectral_data)
        else:
            raman, _ = self.algorithm(spectrum)
        return raman

