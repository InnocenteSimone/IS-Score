import numpy as np

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

    peak_to_penalize = 0

    for peak, prom, baseline_val in zip(peaks, prominences, baseline[peaks]):
        prom_75 = prom[0][0] * 0.75

        if baseline_val > sp[peak] - prom_75:
            peak_to_penalize += 1
        elif baseline_val > sp[peak] - prom[0][0]:
            # IDEA: check how far is the baseline with the original prominence
            # And use half of that difference to add it to the previous prominence (75)
            # and see if the baseline is greater than the new prominence
            diff = baseline_val - (sp[peak] - prom[0][0])
            evalPoint = prom_75 + diff / 2
            if baseline_val > sp[peak] - evalPoint:
                peak_to_penalize += 1

    if len(peaks) == 0 or peak_to_penalize == 0:
        return 0

    ratio = peak_to_penalize / len(peaks)
    beta = max(1, len(peaks) * (1 - ratio))
    # Adjust weight to grow more slowly for small total_peaks
    w = np.sqrt(len(peaks)) / (np.sqrt(len(peaks)) + beta)
    log_term = np.log(1.5 + ratio ** 2)
    single_peak_penalization = w * log_term

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
    dips_to_penalize = 0

    for dip, prom, baseline_val in zip(dips, prominences, baseline[dips]):
        # if (baseline_val < sp[dip] - prom[0][0]) or (baseline_val > sp[dip] + (prom[0][0] / 2)):
        #     dips_to_penalize += 1
        if baseline_val < sp[dip] - prom[0][0]:
            dips_to_penalize += 1
        elif baseline_val > sp[dip] + (prom[0][0] / 2):
            dips_to_penalize += 1

    print(dips_to_penalize)
    if len(dips) == 0 or dips_to_penalize == 0:
        return 0

    ratio = dips_to_penalize / len(dips)
    beta = max(1, len(dips) * (1 - ratio))
    # Adjust weight to grow more slowly for small total_peaks
    w = np.sqrt(len(dips)) / (np.sqrt(len(dips)) + beta)
    log_term = np.log(1.5 + (ratio ** 2))
    single_dip_penalization = w * log_term

    return single_dip_penalization