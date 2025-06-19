import numpy as np


class DebugCollector:
    """
    Utility class for collecting debugging information during algorithm execution.

    This class allows logging and retrieving arbitrary debug information grouped by categories and subkeys.
    It supports separate storage for general data and plot-specific data. Logging can be enabled or disabled globally.

    Attributes
    ----------
    enabled : bool
        Indicates whether data collection is active.
    collected_data : dict
        Dictionary to store general debug data in the form {category: {subkey: value}}.
    plot_data : dict
        Dictionary to store plot-related debug data in the same format.
    """
    enabled = False
    collected_data = {}
    plot_data = {}

    @classmethod
    def activate(cls):
        """
        Enable the debug collector and reset previously collected data.
        """
        cls.enabled = True
        cls.collected_data = {}
        cls.plot_data = {}

    @classmethod
    def deactivate(cls):
        """
        Disable the debug collector and clear previously collected data.
        """
        cls.enabled = False
        cls.collected_data = {}
        cls.plot_data = {}

    @classmethod
    def log(cls, category, subkey, value):
        """
        Log a value into the general debug data under the specified category and subkey.

        Parameters
        ----------
        category : str
            The top-level key under which the data will be stored.
        subkey : str
            The secondary key under the category.
        value : Any
            The value to store.
        """
        if cls.enabled:
            if category not in cls.collected_data:
                cls.collected_data[category] = {}
            cls.collected_data[category][subkey] = value

    @classmethod
    def logPlot(cls, category, subkey, value):
        """
        Log a value into the plot-specific debug data under the specified category and subkey.

        Parameters
        ----------
        category : str
            The top-level key under which the plot data will be stored.
        subkey : str
            The secondary key under the category.
        value : Any
            The value to store.
        """
        if cls.enabled:
            if category not in cls.plot_data:
                cls.plot_data[category] = {}
            cls.plot_data[category][subkey] = value

    @classmethod
    def get(cls, category, subkey=None):
        """
        Retrieve a value or sub-dictionary from the general debug data.

        Parameters
        ----------
        category : str
            The category to retrieve.
        subkey : str, optional
            If provided, returns the specific value under the subkey.

        Returns
        -------
        Any or dict or None
            The requested value, dictionary of subkeys, or None if not found.
        """
        if category not in cls.collected_data:
            return None
        if subkey:
            return cls.collected_data[category].get(subkey)
        return cls.collected_data[category]

    @classmethod
    def getPlot(cls, category, subkey=None):
        """
        Retrieve a value or sub-dictionary from the plot debug data.

        Parameters
        ----------
        category : str
            The category to retrieve.
        subkey : str, optional
            If provided, returns the specific value under the subkey.

        Returns
        -------
        Any or dict or None
            The requested value, dictionary of subkeys, or None if not found.
        """
        if category not in cls.plot_data:
            return None
        if subkey:
            return cls.plot_data[category].get(subkey)
        return cls.plot_data[category]

    @classmethod
    def all(cls):
        """
        Return the full dictionary of collected general debug data.

        Returns
        -------
        dict
            The collected general debug data.
        """
        return cls.collected_data

    @classmethod
    def allPlot(cls):
        """
        Return the full dictionary of collected plot debug data.

        Returns
        -------
        dict
            The collected plot debug data.
        """
        return cls.plot_data

def normalizeSpectraBaseline(raw_sp: np.array, baseline: np.array) -> tuple:
    """
    Normalize the spectra and baseline in the range 0-1.

    Parameters
    ----------
    raw_sp : np.array
        The raw Raman spectra spectrum.
    baseline : np.array
        The baseline spectrum.

    Returns
    -------
    spectra_norm, baseline_norm : tuple
        A tuple containing the normalized spectra and baseline.
    """
    min_val, max_val = min(raw_sp.min(), baseline.min()), max(raw_sp.max(), baseline.max())

    spectra_norm = (raw_sp - min_val) / (max_val - min_val)
    baseline_norm = (baseline - min_val) / (max_val - min_val)

    return spectra_norm, baseline_norm


def normalizeProminence(prominences, max_val, min_val):
    """
    Normalize the prominence so they match the combined max and min.

    Parameters
    ----------
    prominences : list
        The list of the prominences.
    min_val : float
        The minimum value for the normalization.
    max_val : float
        The maximum value for the normalization.

    Returns
    -------
    new_prom : list
        A list containing the normalized prominences.
    """
    new_prom = []
    for prom, l, r in prominences:
        new_p = prom[0] * (max_val - min_val)
        new_prom.append(([new_p], l, r))
    return new_prom



def printOutputTable(data):
    HEADERS_TABLE = ["Information", "Value"]
    col_widths = [max(len(str(item)) for item in col) for col in zip(HEADERS_TABLE, *data)]

    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

    header = "|" + "|".join(f" {h:<{w}} " for h, w in zip(HEADERS_TABLE, col_widths)) + "|"

    rows = []
    for row in data:
        rows.append("|" + "|".join(f" {str(item):<{w}} " for item, w in zip(row, col_widths)) + "|")

    print("\n".join([border, header, border] + rows + [border]))

def _checkInput(raw_sp: np.array, baseline_corrected_sp: np.array, sp_axis: np.array):
    """
    Check if the input data is valid.

    Parameters
    ----------
    raw_sp: np.array
        The raw Raman spectrum.

    baseline_corrected_sp : np.array
        The baseline-corrected spectrum.

    sp_axis : np.array
        The spectral axis, which represents the frequency or wavelength values corresponding to each data point in `raw_sp`.

    Returns
    -------
    bool
        True if the input data is valid, False otherwise.

    """
    if len(raw_sp) == 0 or len(baseline_corrected_sp) == 0 or len(sp_axis) == 0:
        return False
    if len(raw_sp) != len(baseline_corrected_sp) or len(raw_sp) != len(sp_axis) or len(baseline_corrected_sp) != len(
            sp_axis):
        return False
    return True