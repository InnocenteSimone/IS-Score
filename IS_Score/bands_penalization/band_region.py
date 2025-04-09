import numpy as np

def getFakeProminences(type: str, sp: np.array, baseline: np.array, bands: list, edges: list, prominences: list):
    """
    Retrieve the fake prominences exploiting the baseline and the peak prominence.
    Fake prominences are proportional value of the real peak prominence but computed on the peak region.
    The distance between the baseline and the prominence is used to compute the proportional value, exploiting the
    difference between the baseline and each frequency in the peak region.

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
    list
        The list with the fake prominences.
    """

    fake_prominences = []
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

        fake_prominences.append(band_region_fake_prom)

    return fake_prominences



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
    float
        The final penalty for each peak region.
    """
    underfitting_penalties = []
    overfitting_penalties = []

    fake_prominences = getFakeProminences("peak", sp, baseline, peaks, edges, prominences)
    for peak, prom, (left_edge, right_edge), fp_band in zip(peaks, prominences, edges, fake_prominences):
        freq_prom_baseline_distance_over = []
        freq_prom_baseline_distance_under = []

        for i, fp in enumerate(fp_band):
            baseline_intensity = baseline[left_edge:right_edge][i]
            spectra_intensity = sp[left_edge:right_edge][i]

            # The penalty is computed by checking if the fake prominence is above or below the baseline
            if (spectra_intensity - fp) < baseline_intensity:
                freq_prom_baseline_distance_over.append(np.abs((spectra_intensity - fp) - baseline_intensity))

            if (spectra_intensity - fp) > baseline_intensity:
                freq_prom_baseline_distance_under.append(np.abs((spectra_intensity - fp) - baseline_intensity))

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

        if len(tmp2[tmp2 < perc_under]) > 0:
            mean_under = np.round(np.mean(tmp2[tmp2 < perc_under]), 4)
            underfitting_penalties.append(mean_under)

    regionPenalization = np.sum(overfitting_penalties) + np.sum(underfitting_penalties)
    return regionPenalization


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
    float
        The final penalty for each dip region.
    """

    lower_penalties, greater_penalties = [], []

    fake_prominences = getFakeProminences("dip", sp, baseline, dips, edges, prominences)

    for dip, prom, (left_edge, right_edge), fp_band in zip(dips, prominences, edges, fake_prominences):
        freq_prom_baseline_distance_lower = []
        freq_prom_baseline_distance_greater = []

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

        lower_penalization = np.mean(freq_prom_baseline_distance_lower)
        lower_penalties.append(lower_penalization)

        greater_penalization = np.mean(freq_prom_baseline_distance_greater)
        greater_penalties.append(greater_penalization)

    regionPenalization = np.sum(lower_penalties) + np.sum(greater_penalties)
    return regionPenalization
