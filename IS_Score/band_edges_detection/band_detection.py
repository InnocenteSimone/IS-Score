import io
import contextlib
import numpy as np
from scipy import signal
from findpeaks import findpeaks
from collections import Counter

def findBands(sp: np.array, tolerance: int) -> list:
    """
    Find the meaningful bands in a Raman spectrum

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    tolerance : int
        The tolerance value used to consider two bands as "common bands".

    Returns
    -------
    filtered_bands: list
        The list containing the detected band.
    """

    bands_raw, _ = signal.find_peaks(sp, prominence=(None, None))
    raw_prominences = signal.peak_prominences(sp, bands_raw)[0]

    """
    Exploit all the peaks available of the spectra to define a prominence filter for the computation
    of the meaningfull peaks
    """
    raw_prominence_filter = [(min(raw_prominences) + max(raw_prominences)) / 5, None]
    band_prominence_filter = [0.005, None]

    raw_bands_counter, common_bands_counter = Counter(), Counter()

    for wl in [20, 30, 40, 50, 60]:
        bands_raw, info_raw = signal.find_peaks(sp, prominence=raw_prominence_filter)

        sp_den = signal.savgol_filter(sp, window_length=wl, polyorder=4)
        bands_den, info_den = signal.find_peaks(sp_den, prominence=band_prominence_filter)

        # Find the common bands between the raw and denoised bands
        common_bands = [raw_band for raw_band in bands_raw if np.isclose(bands_den, raw_band, atol=tolerance).sum() > 0]

        # Count the number of times a peak appears in the common peaks
        for p in common_bands: common_bands_counter[p] += 1

        # Update the prominences filters
        raw_prominence_filter = [(min(raw_prominences) + max(raw_prominences)) / ((wl / 10) * 2), None]
        band_prominence_filter[0] += 0.001

    # Retrieve only the peaks common which appears at least 2 times
    bands = [key for key, value in common_bands_counter.items() if value > 1]

    # Filtering bands which are too close to each other
    filtered_bands = [bands[0]] if bands else []
    for band in bands[1:]:
        if abs(band - filtered_bands[-1]) > 3:
            filtered_bands.append(band)

    return filtered_bands


def _boundEdgesDetection(sp: np.array, bands: list) -> list:
    """
    Find the edges using the bound method.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    bands : list
        The list containing the bands of which edges need to be detected..

    Returns
    -------
    edges: list
        The list containing the detected edges.
    """

    MAX_ITER = 20
    ATOL = 0.01

    den_sp = signal.savgol_filter(sp, window_length=25, polyorder=3)
    den_rel_minima = signal.argrelmin(den_sp, order=5)[0]

    edges = []
    for band in bands:
        # Find the relative minima that is closest to the band
        index_min = np.argmin(np.abs(den_rel_minima - band))
        minima_index = den_rel_minima[index_min]

        # If the minima is greater then the band, the bound need to go backwards
        if minima_index > band:
            left_bound = band - (minima_index - band)
            # Sanity check
            left_bound = 0 if left_bound <= 0 else left_bound

            # Retrieve the previous minima index if available
            previous = den_rel_minima[index_min - 1] if index_min != 0 else -1

            it = 0
            while (not (np.isclose(sp[left_bound], sp[minima_index], atol=ATOL))) and (it < MAX_ITER) and (
                    left_bound != 0):
                # Adjust the bound based on the intensity value of the closest relative minima
                left_bound = left_bound + 1 if sp[left_bound] < sp[minima_index] else left_bound - 1

                if (left_bound <= 0) or (previous == left_bound):
                    break
                it += 1

            edges.append((left_bound, minima_index))

        else:
            right_bound = band + (band - minima_index)

            # If the bound is greater than the length of the spectra, there is not enough space to find the edge
            # Set the bound to the last element of the spectra
            right_bound = len(sp) - 1 if right_bound >= len(sp) else right_bound

            # Retrieve the next minima index if available
            next = den_rel_minima[index_min + 1] if index_min + 1 < len(den_rel_minima) else -1

            it = 0
            while (not (np.isclose(sp[minima_index], sp[right_bound], atol=ATOL))) and (it < MAX_ITER) and (
                    right_bound != len(sp) - 1):
                # Adjust the bound based on the intensity value of the closest relative minima
                right_bound = right_bound + 1 if sp[right_bound] > sp[minima_index] else right_bound - 1

                if (right_bound >= len(sp)) or (next == right_bound):
                    break
                it += 1
            edges.append((minima_index, right_bound))

    return edges


def getBandEdges(sp: np.array, bands: list) -> list:
    """
    Find the edges for each band in the list.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    bands : list
        The list containing the bands of which edges need to be detected.

    Returns
    -------
    edges: list
        The list containing the detected edges.
    """

    bound_edges = _boundEdgesDetection(sp, bands)

    den_sp = signal.savgol_filter(sp, window_length=25, polyorder=4)
    with contextlib.redirect_stdout(io.StringIO()):
        fp = findpeaks(method='peakdetect', lookahead=1, interpolate=5)
        bands_results = fp.fit(den_sp)

    mapped_bands = []
    band_df = bands_results['df']
    band_only_df = band_df[band_df['peak'] == True]

    # Filter the bands based on the distance to the closest peak of the additional find peaks methods
    for band in bands:
        closest_peak = min(band_only_df['x'], key=lambda x: abs(x - band))
        if abs(closest_peak - band) <= 8:
            mapped_bands.append(band)

    # Retrieve the edges with the new method
    new_edges = []
    vallyes = band_df[band_df['valley'] == True]
    for band in mapped_bands:
        left_edge = vallyes.loc[(vallyes.index < band)].iloc[-1]['x']
        right_edge = vallyes.loc[(vallyes.index > band)].iloc[0]['x']
        new_edges.append((left_edge, right_edge))

    # Based on the ratio of the length of the edges, chose to keep the old edges or use the new edges
    final_edges = []
    sp_axis = np.arange(len(sp))
    for band, (left_new, right_new), (left_old, right_old) in zip(mapped_bands, new_edges, bound_edges):
        ratio_new, ratio_old = 1, 1
        left_new_band_len, band_right_new_len = len(sp_axis[left_new:band]), len(sp_axis[band:right_new])
        left_old_band_len, band_right_old_len = len(sp_axis[left_old:band]), len(sp_axis[band:right_old])

        if left_new_band_len != 0 and band_right_new_len != 0:
            ratio_new = min(left_new_band_len, band_right_new_len) / max(left_new_band_len, band_right_new_len)
        if left_old_band_len != 0 and band_right_old_len != 0:
            ratio_old = min(left_old_band_len, band_right_old_len) / max(left_old_band_len, band_right_old_len)

        if left_new_band_len == 0 or band_right_new_len == 0:
            final_edges.append((left_old, right_old))
        elif left_old_band_len == 0 or band_right_old_len == 0:
            final_edges.append((left_new, right_new))
        elif (ratio_new < 0.3) or (ratio_old > ratio_new):
            final_edges.append((left_old, right_old))
        else:
            final_edges.append((left_new, right_new))

    return final_edges


def _validateBands(bands: list, edges: list) -> tuple:
    """
    Check if the bands and edges are valid.
    The edges which are closes to each other or to the band are removed.

    Parameters
    ----------
    bands : list
        The list containing the bands.
    edges : list
        The list containing the edges.

    Returns
    -------
    tuple
        The list with the valid bands and edges.
    """
    new_bands, new_edges = [], []
    for band, (left_edge, right_edge) in zip(bands, edges):
        if (left_edge == right_edge) or (left_edge == band) or (right_edge == band):
            continue
        new_bands.append(band)
        new_edges.append((left_edge, right_edge))

    return new_bands, new_edges


def getWlenProminences(sp, bands, edges):
    """
    Retrieve the bands prominence using the wlen parameters.
    The wlen parameter is set at twice the distance between the edges of the band.

    Parameters
    ----------
    bands : list
        The list containing the bands.
    edges : list
        The list containing the edges.

    Returns
    -------
    list
        The list with the prominences.
    """

    prominences = []

    for band, (left_edge, right_edge) in zip(bands, edges):
        # Find the prominence of the specific band using the wlen parameters
        prominence = signal.peak_prominences(sp, [band], wlen = (right_edge - left_edge)*2)
        prominences.append(prominence)

    return prominences
