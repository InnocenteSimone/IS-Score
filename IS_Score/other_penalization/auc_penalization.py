import numpy as np
from copy import copy
from scipy import signal, interpolate


def linearInterpOverRegion(sp: np.array, peak_edges: list):
    """
    Interpolate the spectrum over the regions defined by the peak edges.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    peak_edges : list
        List of tuples defining the start and end indices of the peak edges.

    Returns
    -------
    sp : np.array
        The filtered spectrum with linear interpolation over the regions.
    """

    for start, end in peak_edges:
        linear_interp = np.interp(sp[start:end], [sp[start], sp[end]], [sp[start], sp[end]])
        sp[start:end] = linear_interp

    return sp


def _applyGaussianOffset(x, center, width, amplitude):
    """
    Apply a Gaussian offset to the spectrum.

    Parameters
    ----------
    x : np.array
        The x-axis values.
    center : float
        The center of the Gaussian.
    width : float
        The width of the Gaussian.
    amplitude : float
        The amplitude of the Gaussian.

    Returns:
    --------
    np.array
        The Gaussian offset applied to the x-axis values.
    """
    return amplitude * np.exp(-((x - center) ** 2) / (2 * width ** 2))


def getInterpolation(sp: np.array, peaks: list, peak_edges: list):
    """
    Get the interpolation of the spectrum using cubic splines and Gaussian offsets.
    This interpolation return a fake baseline that is mimic an overfitting behavior.

    Parameters
    ----------
    sp : np.array
        The Raman spectrum.
    peaks: list
        List of peak.
    peak_edges: list
        List of tuples defining the start and end indices of the peak edges.

    Returns
    -------
    mean_interp: np.array
        The fake overfitting baseline.
    """
    sp_filtered = copy(sp)
    sp_filtered = linearInterpOverRegion(sp_filtered, peak_edges)

    sp_axis = np.arange(len(sp))

    interpolation_list = []
    for i in [5, 10, 15, 20, 25, 30]:
        sp_den = signal.savgol_filter(sp_filtered, window_length=i, polyorder=4)

        # Find all the dips in the filtered denoised spectrum
        dips, _ = signal.find_peaks(-sp_den, prominence=(None, None))
        dips = np.insert(dips, 0, 0)
        dips = np.append(dips, len(sp) - 1)
        cubic_interp = interpolate.CubicSpline(sp_axis[dips], sp_filtered[dips], bc_type="clamped")

        interpolation = cubic_interp(sp_axis)
        # To avoid that the interpolation has values higher than the original spectrum
        interpolation = np.minimum(interpolation, sp_filtered)
        interpolation_list.append(interpolation)

    mean_interpolation = np.array(interpolation_list).mean(axis=0)
    mean_interpolation = np.minimum(mean_interpolation, sp)

    # Add offset to the interpolation to mimic overfitting behaviour
    norm_amp = 0.03 * (max(sp) - min(sp))
    offset = sum(_applyGaussianOffset(sp_axis, sp_axis[peak], (e - s) / 2, norm_amp) for peak, (s, e) in zip(peaks, peak_edges))
    mean_interpolation = np.minimum(mean_interpolation + offset, sp)

    neg_sp = (-sp - min(-sp)) / (max(-sp) - min(-sp))
    neg_sp_den = signal.savgol_filter(neg_sp, window_length=41, polyorder=3)
    dips_auc, _ = signal.find_peaks(neg_sp_den, prominence=(None, None))
    dips_auc = np.insert(dips_auc, 0, 0)
    dips_auc = np.append(dips_auc, len(sp) - 1)
    dips_auc = np.sort(dips_auc)

    cubic_interp = interpolate.CubicSpline(sp_axis[dips_auc], sp[dips_auc], bc_type="clamped")
    interp = cubic_interp(sp_axis)
    interp = np.minimum(interp, sp)

    mean_interp = np.maximum(mean_interpolation, interp)
    # Slightly lower the mean interpolation in all the points its equal to the spectrum
    mean_interp[mean_interp == sp] -= (0.005 * (max(sp) - min(sp)))
    mean_interp = signal.savgol_filter(mean_interp, 12, 3)

    return mean_interp


def getAUCPenalty(sp: np.array, baseline: np.array, peaks: list, peak_edges: list):
    """
    Return the AUC penalty.

    Parameters
    ---------
    sp : np.array
        The Raman spectrum.
    baseline: np.array
        The baseline spectrum.
    peaks: list
        List of peak.
    peak_edges: list
        List of tuples defining the start and end indices of the peak edges.

    Returns
    -------
    auc_penalization: float
        The AUC penalty.
    """

    interpolation = getInterpolation(sp, peaks, peak_edges)

    sp_area, sp_abs_corrected_area = np.trapz(sp), np.trapz(abs(sp - baseline))
    sp_corrected_area = np.trapz(sp - baseline)
    interp_corrected_area = np.trapz(abs(sp - interpolation))

    ratio_bc_sp = sp_abs_corrected_area / sp_area
    ratio_ic_sp = interp_corrected_area / sp_area

    interp_baseline_diff = interpolation - baseline
    diff_area = np.trapz(interp_baseline_diff)
    temporary_penalization = abs(ratio_bc_sp - ratio_ic_sp)
    if (sp_corrected_area < 0) or (diff_area < 0):
        temporary_penalization = ratio_bc_sp + ratio_ic_sp

    negative_area_diff = abs(np.trapz(interp_baseline_diff[interp_baseline_diff < 0]))
    positive_area_diff = np.trapz(interp_baseline_diff[interp_baseline_diff > 0])
    if (diff_area < 0) or (negative_area_diff / positive_area_diff > 0.7): # Overfitting
        auc_penalty = negative_area_diff / sp_abs_corrected_area
    else:
        auc_penalty = positive_area_diff / sp_area

    auc_penalization = temporary_penalization + auc_penalty
    auc_penalization = 0 if auc_penalization < 0.1 else np.round(auc_penalization, decimals=2)

    return auc_penalization



