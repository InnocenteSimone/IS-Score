import numpy as np
import matplotlib.pyplot as plt
from IS_Score.utils import normalizeSpectraBaseline, normalizeProminence, printOutputTable, _checkInput, DebugCollector
from IS_Score.band_edges_detection.band_detection import findBands, getBandEdges, _validateBands, getWlenProminences
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
    is_score : float
        A numerical value that assess the baseline fit.
    """
    success = _checkInput(raw_sp, baseline_corrected_sp, sp_axis)

    if not success:
        return -1

    PEAKS_DIPS_TOL = kwargs.pop("peaks_dips_tolerance", {"peaks": 5, "dips": 5})
    custom_peaks = kwargs.get("custom_peaks", None)
    custom_dips = kwargs.get("custom_dips", None)


    raw_sp, baseline_corrected_sp, sp_axis = np.array(raw_sp), np.array(baseline_corrected_sp), np.array(sp_axis)
    baseline = raw_sp - baseline_corrected_sp

    # Normalize only the spectra for peaks/dips detection
    raw_sp_norm = (raw_sp - np.min(raw_sp)) / (np.max(raw_sp) - np.min(raw_sp))

    # Normalize both spectra and baseline for comparison
    raw_sp_norm_bas, baseline_sp_norm = normalizeSpectraBaseline(raw_sp, baseline)
    combined_min, combined_max = min(np.min(raw_sp_norm_bas), np.min(baseline_sp_norm)), max(np.max(raw_sp_norm_bas), np.max(baseline_sp_norm))

    if custom_peaks is not None:
        peaks = custom_peaks
    else:
        peaks = findBands(raw_sp_norm, tolerance=PEAKS_DIPS_TOL["peaks"])
    peak_edges = getBandEdges(raw_sp_norm, peaks)

    # Sanity Check for bands and edges
    peaks, peak_edges = _validateBands(peaks, peak_edges)
    peaks_prominences = getWlenProminences(raw_sp_norm, peaks, peak_edges)

    # Normalize the prominences for good comparison with the baseline
    peaks_prominences = normalizeProminence(peaks_prominences, combined_max, combined_min)

    peaks_penalization = getSinglePeakPenalty(raw_sp_norm_bas, baseline_sp_norm, peaks, peaks_prominences)
    peak_region_penalization = getRegionPeakPenalty(raw_sp_norm_bas, baseline_sp_norm, peaks, peak_edges, peaks_prominences)

    neg_sp = (-raw_sp_norm - min(-raw_sp_norm)) / (max(-raw_sp_norm) - min(-raw_sp_norm))
    if custom_dips is not None:
        dips = custom_dips
    else:
        dips = findBands(neg_sp, tolerance=PEAKS_DIPS_TOL["dips"])
    dips_edges = getBandEdges(neg_sp, dips)
    dips, dips_edges = _validateBands(dips, dips_edges)

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

    is_score = round(1 - min(final_penalization, 1), 4)

    if DebugCollector.enabled:
        DebugCollector.log("GENERAL", "sp_norm", raw_sp_norm_bas)
        DebugCollector.log("GENERAL", "baseline_norm", baseline_sp_norm)
        DebugCollector.log("GENERAL", "peaks", peaks)
        DebugCollector.log("GENERAL", "peaks_edges", peak_edges)
        DebugCollector.log("GENERAL", "dips", dips)
        DebugCollector.log("GENERAL", "dips_edges", dips_edges)
        DebugCollector.log("GENERAL", "IS-Score", is_score)

        # region Single Peak and Dip plot
        peaks_penalized = DebugCollector.collected_data['SINGLE_PEAK_PENALIZATION']['peak_penalized']
        dips_penalized = DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['dip_penalized']

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(sp_axis, raw_sp_norm, color='tab:blue', label="Normalized Spectra", alpha=0.4)
        ax.plot(sp_axis, baseline_sp_norm, color='tab:orange', label="Normalized Baseline", alpha=0.4)
        ax.scatter(sp_axis[dips], raw_sp_norm[dips], color='blue', marker='x', s=100, label="Dips")
        ax.scatter(sp_axis[dips_penalized], raw_sp_norm[dips_penalized], color='darkorange', marker='x', s=100,
                   label="Dips Penalized")
        ax.scatter(sp_axis[peaks], raw_sp_norm[peaks], color='green', marker='x', s=100, label="Peaks")
        ax.scatter(sp_axis[peaks_penalized], raw_sp_norm[peaks_penalized], color='red', marker='x', s=100,
                   label="Peaks Penalized")
        if len(DebugCollector.collected_data['SINGLE_PEAK_PENALIZATION']['point_for_penalization']) > 0:
            ax.scatter(sp_axis[peaks],
                       DebugCollector.collected_data['SINGLE_PEAK_PENALIZATION']['point_for_penalization'],
                       color='tab:green', marker='o', alpha=0.4)
        if len(DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['upper_point_for_penalization']) > 0:
            ax.scatter(sp_axis[dips],
                       DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['upper_point_for_penalization'],
                       color='tab:blue', marker='^', alpha=0.4)
        if len(DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['lower_point_for_penalization']) > 0:
            ax.scatter(sp_axis[dips],
                       DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['lower_point_for_penalization'],
                       color='tab:blue', marker='^', alpha=0.4)
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Norm. Intensity")
        ax.grid(alpha=0.4)
        ax.legend()
        peaks_penalty = round(DebugCollector.collected_data['SINGLE_PEAK_PENALIZATION']['single_peak_penalization'], 4)
        dips_penalty = round(DebugCollector.collected_data['SINGLE_DIP_PENALIZATION']['single_dip_penalization'], 4)
        ax.set_title(f"Peaks and Dips Penalized\n Peaks Value: {peaks_penalty}, Dips Value: {dips_penalty}")
        # endregion
        DebugCollector.logPlot("SINGLE_PEAKS_DIPS_PENALIZATION", "plot", fig)
        plt.close(fig)
        # region Intensity Penalization plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(sp_axis, raw_sp_norm, color='tab:blue', label="Normalized Spectra", alpha=0.4)
        ax.plot(sp_axis, baseline_sp_norm, color='tab:orange', label="Normalized Baseline", alpha=0.4)
        ax.scatter(sp_axis[DebugCollector.collected_data["INTENSITY_PENALIZATION"]["filtered_indexes"]],
                   raw_sp_norm[DebugCollector.collected_data["INTENSITY_PENALIZATION"]["filtered_indexes"]],
                   c='red', s=25, label="Unsound intensities", alpha=0.5)

        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Norm. Intensity")
        ax.grid(alpha=0.4)
        ax.legend()
        ax.set_title(
            f"Intensity Penalty Value: {round(DebugCollector.collected_data['INTENSITY_PENALIZATION']['intensity_penalization'], 4)}")
        # endregion
        DebugCollector.logPlot("INTENSITY_PENALIZATION", "plot", fig)
        plt.close(fig)
        # region AUC Penalization plot
        interp = DebugCollector.collected_data['AUC_PENALIZATION']['interpolation']
        min_ref = min([min(raw_sp), min(baseline), min(interp)])
        max_ref = max([max(raw_sp), max(baseline), max(interp)])

        spectra_plot = (raw_sp - min_ref) / (max_ref - min_ref)
        baseline_plot = (baseline - min_ref) / (max_ref - min_ref)
        interp_plot = (interp - min_ref) / (max_ref - min_ref)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(sp_axis, spectra_plot, color='tab:blue', label="Normalized Spectra")
        ax.fill_between(sp_axis, spectra_plot, where=(spectra_plot > 0), alpha=0.3, color='tab:blue')
        ax.plot(sp_axis, baseline_plot, color='tab:orange', label="Normalized Baseline")
        ax.fill_between(sp_axis, baseline_plot, where=(baseline_plot > 0), alpha=0.3, color='tab:orange')
        ax.plot(sp_axis, interp_plot, color='tab:red', label="Interpolation")
        ax.fill_between(sp_axis, interp_plot, where=(interp_plot > 0), alpha=0.3, color='tab:red')
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Intensity")
        ax.grid(alpha=0.4)
        ax.legend()
        ax.set_title(
            f"AUC Penalty Value: {round(DebugCollector.collected_data['AUC_PENALIZATION']['auc_penalization'], 4)}")
        # endregion
        DebugCollector.logPlot("AUC_PENALIZATION", "plot", fig)
        plt.close(fig)
        # region Peak Region plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(sp_axis, raw_sp_norm_bas, color='tab:blue', alpha=0.4)
        ax.plot(sp_axis, baseline_sp_norm, color='tab:orange')
        ax.scatter(sp_axis[peaks], raw_sp_norm_bas[peaks], color='green', s=100, marker='x')
        fake_prominences = DebugCollector.collected_data["REGION_PEAK_PENALIZATION"]["raman_shift_prominences"]

        for (s, e), fp_band in zip(peak_edges, fake_prominences):
            ax.plot(sp_axis[s:e], raw_sp_norm_bas[s:e], color='m')
            for i, fp in enumerate(fp_band):
                ax.vlines(sp_axis[s:e][i], ymin=raw_sp_norm_bas[s:e][i] - fp, ymax=raw_sp_norm_bas[s:e][i],
                          color="lightblue", alpha=0.4)

        for i, (left_edge, right_edge) in enumerate(peak_edges):
            index_overfitting = DebugCollector.collected_data["REGION_PEAK_PENALIZATION"]["overfitting_index"][i]
            overfitting = DebugCollector.collected_data["REGION_PEAK_PENALIZATION"]["overfitting"][i]

            index_underfitting = DebugCollector.collected_data["REGION_PEAK_PENALIZATION"]["underfitting_index"][i]
            underfitting = DebugCollector.collected_data["REGION_PEAK_PENALIZATION"]["underfitting"][i]
            if len(overfitting) > 0:
                ax.vlines(x=sp_axis[left_edge:right_edge][index_overfitting],
                          ymin=baseline_sp_norm[left_edge:right_edge][index_overfitting],
                          ymax=baseline_sp_norm[left_edge:right_edge][index_overfitting] - overfitting, color='red',
                          alpha=0.4)

            if len(underfitting) > 0:
                ax.vlines(x=sp_axis[left_edge:right_edge][index_underfitting],
                          ymin=baseline_sp_norm[left_edge:right_edge][index_underfitting],
                          ymax=baseline_sp_norm[left_edge:right_edge][index_underfitting] + underfitting,
                          color='tab:orange',
                          alpha=0.4)
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Intensity")
        ax.grid(alpha=0.4)
        ax.set_title(
            f"Peak Region Penalty value {DebugCollector.collected_data['REGION_PEAK_PENALIZATION']['peak_region_penalization']}")
        ax.legend()
        # endregion
        DebugCollector.logPlot("REGION_PEAK_PENALIZATION", "plot", fig)
        plt.close(fig)
        # region Dip Region plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(sp_axis, raw_sp_norm_bas, color='tab:blue', alpha=0.4)
        ax.plot(sp_axis, baseline_sp_norm, color='tab:orange')
        ax.scatter(sp_axis[dips], raw_sp_norm_bas[dips], color='blue', s=100, marker='x')
        fake_prominences = DebugCollector.collected_data["REGION_DIP_PENALIZATION"]["raman_shift_prominences"]

        for (s, e), fp_band in zip(dips_edges, fake_prominences):
            ax.plot(sp_axis[s:e], raw_sp_norm_bas[s:e], color='m')
            for i, fp in enumerate(fp_band):
                ax.vlines(sp_axis[s:e][i], ymin=raw_sp_norm_bas[s:e][i] - fp, ymax=raw_sp_norm_bas[s:e][i],
                          color="lightblue", alpha=0.4)

        for i, (left_edge, right_edge) in enumerate(dips_edges):
            indexes = DebugCollector.collected_data["REGION_DIP_PENALIZATION"]["indexes"][i]
            overfitting = DebugCollector.collected_data["REGION_DIP_PENALIZATION"]["overfitting"][i]
            underfitting = DebugCollector.collected_data["REGION_DIP_PENALIZATION"]["underfitting"][i]

            if len(overfitting) > 0:
                ax.vlines(x=sp_axis[left_edge:right_edge][indexes],
                          ymin=baseline_sp_norm[left_edge:right_edge][indexes],
                          ymax=baseline_sp_norm[left_edge:right_edge][indexes] + overfitting, color='red',
                          alpha=0.4)

            if len(underfitting) > 0:
                ax.vlines(x=sp_axis[left_edge:right_edge][indexes],
                          ymin=baseline_sp_norm[left_edge:right_edge][indexes],
                          ymax=baseline_sp_norm[left_edge:right_edge][indexes] - underfitting,
                          color='tab:orange',
                          alpha=0.4)
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Intensity")
        ax.grid(alpha=0.4)
        ax.set_title(
            f"Dip Region Penalty value {round(DebugCollector.collected_data['REGION_DIP_PENALIZATION']['dip_region_penalization'], 4)}")
        ax.legend()
        # endregion
        DebugCollector.logPlot("REGION_DIP_PENALIZATION", "plot", fig)
        plt.close(fig)


    data = [
        ["Intensity Penalty", round(intensity_penalty,4)],
        ["Single Peak Penalty", round(peaks_penalization,4)],
        ["Peak Region Penalty", round(peak_region_penalization, 4)],
        ["Single Dip Penalty", round(dips_penalization, 4)],
        ["Dip Region Penalty", round(dips_region_penalization, 4)],
        ["AUC Penalty", round(auc_penalization, 4)],
        ["Mean Ratio Penalty", round(mean_ratio_penalization,4)],
        ["IS-Score", round(is_score,4)],
    ]

    printOutputTable(data)

    return is_score