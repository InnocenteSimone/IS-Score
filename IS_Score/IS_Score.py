import numpy as np
from IS_Score.utils import normalizeSpectraBaseline, normalizeProminence, printOutputTable, _checkInput
from IS_Score.band_edges_detection.band_detection import findBands, getBandEdges, validateBands, getWlenProminences
from IS_Score.bands_penalization.single_band import getSinglePeakPenalty, getSingleDipPenalty
from IS_Score.bands_penalization.band_region import getRegionPeakPenalty, getRegionDipPenalty
from IS_Score.other_penalization.intensity_penalization import getIntensityPenalization
from IS_Score.other_penalization.auc_penalization import getAUCPenalty
from IS_Score.other_penalization.mean_ratio_penalization import getMeanDipsRatioPenalization


def getIS_Score(raw_sp: np.array, baseline_corrected_sp: np.array, sp_axis: np.array, **kwargs):
    """
    Compute the IS-Score for the given raw and baseline-corrected spectra.

    Parameters
    ----------
    raw_sp : np.array
        The Raman spectrum.
    baseline_corrected_sp : np.array
        The baseline corrected spectrum.
    sp_axis : np.array
        The spectral axis.

    Returns
    -------
    metric_value : float
        A numerical value that assess how good the baseline fit is.
    """
    success = _checkInput(raw_sp, baseline_corrected_sp, sp_axis)

    if not success:
        return -1

    PEAKS_DIPS_TOL = kwargs.pop("peaks_dips_tolerance", {"peaks": 5, "dips": 5})


    raw_sp, baseline_corrected_sp, sp_axis = np.array(raw_sp), np.array(baseline_corrected_sp), np.array(sp_axis)
    baseline = raw_sp - baseline_corrected_sp

    # Normalize only the spectra for peaks/dips detection
    raw_sp_norm = (raw_sp - np.min(raw_sp)) / (np.max(raw_sp) - np.min(raw_sp))

    # Normalize both spectra and baseline for comparison
    raw_sp_norm_bas, baseline_sp_norm = normalizeSpectraBaseline(raw_sp, baseline)
    combined_min, combined_max = min(np.min(raw_sp_norm_bas), np.min(baseline_sp_norm)), max(np.max(raw_sp_norm_bas), np.max(baseline_sp_norm))

    peaks = findBands(raw_sp_norm, tolerance=PEAKS_DIPS_TOL["peaks"])
    peak_edges = getBandEdges(raw_sp_norm, peaks)

    # Sanity Check for bands and edges
    peaks, peak_edges = validateBands(peaks, peak_edges)
    peaks_prominences = getWlenProminences(raw_sp_norm, peaks, peak_edges)

    # Normalize the prominences for good comparison with the baseline
    peaks_prominences = normalizeProminence(peaks_prominences, combined_max, combined_min)

    peaks_penalization = getSinglePeakPenalty(raw_sp_norm_bas, baseline_sp_norm, peaks, peaks_prominences)
    peak_region_penalization = getRegionPeakPenalty(raw_sp_norm_bas, baseline_sp_norm, peaks, peak_edges, peaks_prominences)

    neg_sp = (-raw_sp_norm - min(-raw_sp_norm)) / (max(-raw_sp_norm) - min(-raw_sp_norm))
    dips = findBands(neg_sp, tolerance=PEAKS_DIPS_TOL["dips"])
    dips_edges = getBandEdges(neg_sp, dips)
    dips, dips_edges = validateBands(dips, dips_edges)

    dips_prominences = getWlenProminences(neg_sp, dips, dips_edges)
    dips_prominences = normalizeProminence(dips_prominences, combined_max, combined_min)

    dips_penalization = getSingleDipPenalty(raw_sp_norm_bas, baseline_sp_norm, dips, dips_prominences)
    dips_region_penalization = getRegionDipPenalty(raw_sp_norm_bas, baseline_sp_norm, dips, dips_edges, dips_prominences)

    intensity_penalty = getIntensityPenalization(raw_sp_norm_bas, baseline_sp_norm, peak_edges, dips_edges)
    auc_penalization = getAUCPenalty(raw_sp, baseline, peaks, peak_edges)
    mean_ratio_penalization = getMeanDipsRatioPenalization(raw_sp, baseline)

    final_penalization = (intensity_penalty +
                          peaks_penalization + dips_penalization +
                          peak_region_penalization + dips_region_penalization +
                          auc_penalization + mean_ratio_penalization)

    metric_value = round(1 - min(final_penalization, 1), 2)

    data = [
        ["Intensity", round(intensity_penalty,2)],
        ["Single Peak", round(peaks_penalization,2)],
        ["Peak Region", round(peak_region_penalization, 2)],
        ["Single Dip", round(dips_penalization, 2)],
        ["Dip Region", round(dips_region_penalization, 2)],
        ["AUC", round(auc_penalization, 2)],
        ["Mean Ratio", round(mean_ratio_penalization,2)],
        ["IS-Score", round(metric_value,2)],
    ]

    printOutputTable(data)
    return metric_value