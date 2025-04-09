import numpy as np

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