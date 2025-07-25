import numpy as np
from copy import copy
from scipy import signal
from IS_Score.utils import DebugCollector

def getSignalWithoutRegion(sp, baseline, peaks_edges, dips_edges):
    """
    Create a new signal without the regions defined by the peaks and dips edges.
    The new signal will have the baseline values in the regions defined by the peaks and dips edges.

    Parameters
    ----------
    sp : np.array
        The raw Raman spectra spectrum.
    baseline: np.array
        The baseline of the spectrum.
    peaks_edges : list
        The list containing the peak edges.
    dips_edges : list
        The list containing the dip edges.

    Returns
    -------
    sp_new: np.array
        The new signal.
    """

    sp_new = copy(sp)
    for (s, e), (s_d, e_d) in zip(peaks_edges, dips_edges):
        # Replace the signal values in the peak region with the baseline values
        sp_new[s:e + 1] = baseline[s:e + 1]
        # Replace the signal values in the dip region with the baseline values
        sp_new[s_d:e_d + 1] = baseline[s_d:e_d + 1]
    return sp_new

def addNoiseToSignal(sp, scale, peak_edges, dip_edges):
    """
    Add a gaussian noise over specific region of the signal. The regions are defined by the peaks and dips edges.

    Parameters
    ----------
    sp : np.array
        The raw Raman spectra spectrum.
    scale: float
        The scale of the noise.
    peaks_edges : list
        The list containing the peak edges.
    dips_edges : list
        The list containing the dip edges.

    Returns
    -------
    sp_new: np.array
        The new signal.
    """
    sp_new = copy(sp)

    for (s, e), (s_d, e_d) in zip(peak_edges, dip_edges):
        sp_new[s:e + 1] = sp_new[s:e + 1] + np.random.RandomState(42).normal(loc=0, scale=scale, size=e - s + 1)
        sp_new[s_d:e_d + 1] = sp_new[s_d:e_d + 1] + np.random.RandomState(42).normal(loc=0, scale=scale, size=e_d - s_d + 1)
    return sp_new

def getIntensityPenalization(sp: np.array, baseline: np.array, peaks_edges: list, dips_edges: list):
    """
    Return the intensity penalization.

    Parameters
    ----------
    sp : np.array
        The raw Raman spectra spectrum.
    baseline: np.array
        The baseline of the spectrum.
    peaks_edges : list
        The list containing the peak edges.
    dips_edges : list
        The list containing the dip edges.

    Returns
    -------
    intensity_penalization: float
        The value of the penalization.
    """

    # Create a new signal without the regions defined by the peaks and dips edges
    sp_no_region = getSignalWithoutRegion(sp, baseline, peaks_edges, dips_edges)
    den_sp = signal.savgol_filter(sp_no_region, window_length=13, polyorder=3)

    diff = np.abs(sp_no_region - den_sp)
    mean_val = np.mean(diff)

    # Add the noise to the created signal using the mean value of the difference
    diffWithNoise = addNoiseToSignal(diff, mean_val, peaks_edges, dips_edges)

    threshold = np.mean(diffWithNoise)

    # Get indexes where the baseline intensity is greater than the raw spectrum intensity
    greater_indexes = np.where(baseline > sp)[0]
    intensity_diff = baseline[greater_indexes] - sp[greater_indexes]

    # Filter the indexes where the difference is greater than the threshold
    filtered_indexes = greater_indexes[intensity_diff > threshold]

    intensity_penalization = len(filtered_indexes) / (len(sp) - len(filtered_indexes))

    if DebugCollector.enabled:
        DebugCollector.log("INTENSITY_PENALIZATION", "filtered_indexes", filtered_indexes)
        DebugCollector.log("INTENSITY_PENALIZATION", "intensity_penalization", intensity_penalization)

    return intensity_penalization



