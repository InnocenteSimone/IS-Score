import numpy as np
from IS_Score.utils import DebugCollector

def getRamanShiftProminences(type: str, sp: np.array, baseline: np.array, bands: list, edges: list, prominences: list):
    """
    Retrieve the Raman Shift Prominences exploiting the baseline and the band prominence.
    Raman Shift Prominences are proportional value of the real peak prominence but computed on the band region.
    The distance between the baseline and the prominence is used to compute the proportional value, exploiting the
    difference between the baseline and each frequency in the band region.

    Parameters
    ----------
    sp: np.array
        The spectra data.
    baseline: np.array
        The baseline data.
    bands: list
        The list containing the bands.
    edges: list
        The list containing the edges for each peak.
    prominences: list
        The list containing the prominences for each peak.

    Returns
    -------
    raman_shift_prominences: list
        The list with the fake prominences.
    """

    raman_shift_prominences = []
    for band, prom, (left_edge, right_edge) in zip(bands, prominences, edges):
        region_diff = np.abs(sp[left_edge:right_edge] - baseline[left_edge:right_edge])

        if type == "peak":
            band_prominence = prom[0][0]
            band_diff = sp[band] - baseline[band]
        else:
            band_prominence = np.abs(prom[0][0] / 2)
            band_diff = np.abs(sp[band] - baseline[band])

        band_region_fake_prom = []
        for i, diff in enumerate(region_diff):
            prominence_freq = (diff * band_prominence) / band_diff

            if (type == "dip") and (sp[left_edge:right_edge][i] - prominence_freq < 0):
                prominence_freq = sp[left_edge:right_edge][i]

            band_region_fake_prom.append(prominence_freq)

        raman_shift_prominences.append(band_region_fake_prom)

    return raman_shift_prominences



def getRegionPeakPenalty(sp: np.array, baseline: np.array, peaks: list, edges: list, prominences: list):
    """
    Compute the peak region penalty.

    Parameters
    ----------
    sp: np.array
        The spectra data.
    baseline: np.array
        The baseline data.
    peaks: list
        The list containing the peaks.
    edges: list
        The list containing the edges for each peak.
    prominences: list
        The list containing the prominences for each peak.

    Returns
    -------
    peakRegionPenalization: float
        The final penalty for each peak region.
    """
    underfitting_penalties = []
    overfitting_penalties = []

    raman_shift_prominences = getRamanShiftProminences("peak", sp, baseline, peaks, edges, prominences)

    if DebugCollector.enabled:
        DebugCollector.log("REGION_PEAK_PENALIZATION", "overfitting", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "overfitting_penalties", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "overfitting_index", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "underfitting", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "underfitting_penalties", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "underfitting_index", [])
        DebugCollector.log("REGION_PEAK_PENALIZATION", "raman_shift_prominences", raman_shift_prominences)

    for peak, prom, (left_edge, right_edge), fp_band in zip(peaks, prominences, edges, raman_shift_prominences):
        freq_prom_baseline_distance_over = []
        freq_prom_baseline_distance_under = []

        overfitting_indexes_plot, underfitting_indexes_plot = [], []

        for i, fp in enumerate(fp_band):
            baseline_intensity = baseline[left_edge:right_edge][i]
            spectra_intensity = sp[left_edge:right_edge][i]

            # The penalty is computed by checking if the fake prominence is above or below the baseline
            if (spectra_intensity - fp) < baseline_intensity:
                freq_prom_baseline_distance_over.append(np.abs((spectra_intensity - fp) - baseline_intensity))
                overfitting_indexes_plot.append(i)

            if (spectra_intensity - fp) > baseline_intensity:
                freq_prom_baseline_distance_under.append(np.abs((spectra_intensity - fp) - baseline_intensity))
                underfitting_indexes_plot.append(i)

        # We defined an algorithm that finds many more peaks than before, we need to reduce this penalization
        # I exploit the percentile of the fake prominence distance to the baseline
        perc_over = np.percentile(freq_prom_baseline_distance_over, 75) if len(freq_prom_baseline_distance_over) > 0 else 0
        perc_under = np.percentile(freq_prom_baseline_distance_under, 75) if len(freq_prom_baseline_distance_under) > 0 else 0

        tmp = np.array(freq_prom_baseline_distance_over)
        tmp2 = np.array(freq_prom_baseline_distance_under)

        if len(tmp[tmp < perc_over]) > 0:
            # Round in order to set to zero elements too low
            mean_over = np.round(np.mean(tmp[tmp < perc_over]), decimals=3)
            overfitting_penalties.append(mean_over)
        else:
            overfitting_penalties.append(0)

        if len(tmp2[tmp2 < perc_under]) > 0:
            mean_under = np.round(np.mean(tmp2[tmp2 < perc_under]), 4)
            underfitting_penalties.append(mean_under)
        else:
            underfitting_penalties.append(0)

        if DebugCollector.enabled:
            DebugCollector.get("REGION_PEAK_PENALIZATION", "overfitting").append(freq_prom_baseline_distance_over)
            DebugCollector.get("REGION_PEAK_PENALIZATION", "overfitting_penalties").append(overfitting_penalties)
            DebugCollector.get("REGION_PEAK_PENALIZATION", "overfitting_index").append(overfitting_indexes_plot)
            DebugCollector.get("REGION_PEAK_PENALIZATION", "underfitting").append(freq_prom_baseline_distance_under)
            DebugCollector.get("REGION_PEAK_PENALIZATION", "underfitting_penalties").append(underfitting_penalties)
            DebugCollector.get("REGION_PEAK_PENALIZATION", "underfitting_index").append(underfitting_indexes_plot)

    peakRegionPenalization = np.sum(overfitting_penalties) + np.sum(underfitting_penalties)

    if DebugCollector.enabled:
        DebugCollector.log("REGION_PEAK_PENALIZATION", "peak_region_penalization", peakRegionPenalization)

    return peakRegionPenalization


def getRegionDipPenalty(sp: np.array, baseline: np.array, dips: list, edges: list, prominences: list):
    """
    Compute the dips region penalty.

    Parameters
    ----------
    sp: np.array
        The spectra data.
    baseline: np.array
        The baseline data.
    dips: list
        The list containing the dips.
    edges: list
        The list containing the edges for each dip.
    prominences: list
        The list containing the prominences for each dip.

    Returns
    -------
    dipRegionPenalization: float
        The final penalty for each dip region.
    """

    lower_penalties, greater_penalties = [], []

    raman_shift_prominences = getRamanShiftProminences("dip", sp, baseline, dips, edges, prominences)

    if DebugCollector.enabled:
        DebugCollector.log("REGION_DIP_PENALIZATION", "overfitting", [])
        DebugCollector.log("REGION_DIP_PENALIZATION", "underfitting", [])
        DebugCollector.log("REGION_DIP_PENALIZATION", "indexes", [])
        DebugCollector.log("REGION_DIP_PENALIZATION", "raman_shift_prominences", raman_shift_prominences)

    for dip, prom, (left_edge, right_edge), fp_band in zip(dips, prominences, edges, raman_shift_prominences):
        freq_prom_baseline_distance_lower = []
        freq_prom_baseline_distance_greater = []
        indexes = []
        for i, fp in enumerate(fp_band):
            baseline_intensity = baseline[left_edge:right_edge][i]
            spectra_intensity = sp[left_edge:right_edge][i]

            penalty = 0
            if (spectra_intensity - fp) > baseline_intensity:
                penalty = np.abs((spectra_intensity - fp) - baseline_intensity)
            freq_prom_baseline_distance_lower.append(penalty)

            penalty_greater = 0
            if (spectra_intensity + fp) < baseline_intensity:
                penalty_greater = np.abs((spectra_intensity + fp) - baseline_intensity)
            freq_prom_baseline_distance_greater.append(penalty_greater)
            indexes.append(i)

        lower_penalties.append(np.mean(freq_prom_baseline_distance_lower))
        greater_penalties.append(np.mean(freq_prom_baseline_distance_greater))

        if DebugCollector.enabled:
            DebugCollector.get("REGION_DIP_PENALIZATION","overfitting").append(freq_prom_baseline_distance_lower)
            DebugCollector.get("REGION_DIP_PENALIZATION","underfitting").append(freq_prom_baseline_distance_greater)
            DebugCollector.get("REGION_DIP_PENALIZATION","indexes").append(indexes)


    dipRegionPenalization = np.sum(lower_penalties) + np.sum(greater_penalties)

    if DebugCollector.enabled:
        DebugCollector.log("REGION_DIP_PENALIZATION", "dip_region_penalization", dipRegionPenalization)

    return dipRegionPenalization
