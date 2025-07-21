import numpy as np
from IS_Score.utils import DebugCollector

def getSinglePeakPenalty(sp: np.array, baseline: np.array, peaks: list, prominences: list):
    """
    Return the single peak penalization.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    baseline : np.array
        The baseline spectrum.
    peaks : list
        The list of peaks.
    prominences : list
        The list of prominences for each peach.

    Returns
    -------
    single_peak_penalization: float
        The single peak penalization.
    """
    point_for_penalization, peak_to_penalize = [], []

    for peak, prom, baseline_val in zip(peaks, prominences, baseline[peaks]):
        prom_75 = prom[0][0] * 0.75

        if baseline_val > sp[peak] - prom_75:
            point_for_penalization.append(sp[peak] - prom_75)
            peak_to_penalize.append(peak)
        elif baseline_val > sp[peak] - prom[0][0]:
            # IDEA: check how far is the baseline with the original prominence
            # And use half of that difference to add it to the previous prominence (75)
            # and see if the baseline is greater than the new prominence
            diff = baseline_val - (sp[peak] - prom[0][0])
            prom_85 = prom_75 + diff / 2
            if baseline_val > sp[peak] - prom_85:
                point_for_penalization.append(sp[peak] - prom_85)
                peak_to_penalize.append(peak)
            else:
                # If the peak is not penalized, I store the point for penalization as prom_v75
                point_for_penalization.append(sp[peak] - prom_75)
        else:
            # If the peak is not penalized, I store the point for penalization as prom_v75
            point_for_penalization.append(sp[peak] - prom_75)

    if DebugCollector.enabled:
        DebugCollector.log("SINGLE_PEAK_PENALIZATION", "point_for_penalization", point_for_penalization)
        DebugCollector.log("SINGLE_PEAK_PENALIZATION", "peak_penalized", peak_to_penalize)
        DebugCollector.log("SINGLE_PEAK_PENALIZATION", "single_peak_penalization", 0)

    if len(peaks) == 0 or len(peak_to_penalize) == 0:
        return 0

    ratio = len(peak_to_penalize) / len(peaks)
    beta = max(1, len(peaks) * (1 - ratio))
    # Adjust weight to grow more slowly for small total_peaks
    w = np.sqrt(len(peaks)) / (np.sqrt(len(peaks)) + beta)
    log_term = np.log(1.5 + ratio ** 2)
    single_peak_penalization = w * log_term

    if DebugCollector.enabled:
        DebugCollector.log("SINGLE_PEAK_PENALIZATION", "single_peak_penalization", single_peak_penalization)

    return single_peak_penalization

def getSingleDipPenalty(sp: np.array, baseline: np.array, dips: list, prominences: list):
    """
    Return the single dip penalization.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    baseline : np.array
        The baseline spectrum.
    dips : list
        The list of dips.
    prominences : list
        The list of prominences for each dip.

    Returns
    -------
    single_dip_penalization: float
        The single dip penalization.
    """
    dips_to_penalize = []

    for dip, prom, baseline_val in zip(dips, prominences, baseline[dips]):
        # if (baseline_val < sp[dip] - prom[0][0]) or (baseline_val > sp[dip] + (prom[0][0] / 2)):
        #     dips_to_penalize += 1
        if baseline_val < sp[dip] - prom[0][0]:
            dips_to_penalize.append(dip)
        elif baseline_val > sp[dip] + (prom[0][0] / 2):
            dips_to_penalize.append(dip)

    if DebugCollector.enabled:
        lower_point_for_penalization = [sp[index_dip] - prom for index_dip, prom in
                                        zip(dips, [el[0][0] for el in prominences])]
        upper_point_for_penalization = [sp[index_dip] + (prom / 2) for index_dip, prom in
                                        zip(dips, [el[0][0] for el in prominences])]

        DebugCollector.log("SINGLE_DIP_PENALIZATION", "dip_penalized", dips_to_penalize)
        DebugCollector.log("SINGLE_DIP_PENALIZATION", "upper_point_for_penalization", upper_point_for_penalization)
        DebugCollector.log("SINGLE_DIP_PENALIZATION", "lower_point_for_penalization", lower_point_for_penalization)
        DebugCollector.log("SINGLE_DIP_PENALIZATION", "single_dip_penalization", 0)

    if len(dips) == 0 or len(dips_to_penalize) == 0:
        return 0

    ratio = len(dips_to_penalize) / len(dips)
    beta = max(1, len(dips) * (1 - ratio))
    # Adjust weight to grow more slowly for small total_peaks
    w = np.sqrt(len(dips)) / (np.sqrt(len(dips)) + beta)
    log_term = np.log(1.5 + (ratio ** 2))
    single_dip_penalization = w * log_term

    if DebugCollector.enabled:
        DebugCollector.log("SINGLE_DIP_PENALIZATION", "single_dip_penalization", single_dip_penalization)

    return single_dip_penalization