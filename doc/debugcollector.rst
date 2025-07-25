Debug Collector
===============

The `Utils` module contains an additional class called `DebugCollector` to retrieve all the information computed by the IS-Score algorithm.

Information collected included:
-------------------------------
The method ``DebugCollector.all()`` return a dictionary with all the information collected during the execution of the ``getIS_Score`` function, including:

    - `GENERAL`: Contains the general information about the Raman spectrum, such as the spectral axis, raw spectrum, and baseline corrected spectrum.
        - `sp_norm`: The normalized spectrum.
        - `baseline_norm`: The normalized baseline.
        - `peaks`: The peaks detected.
        - `peaks_edges`: The edges for each peak.
        - `dips`: The dips detected.
        - `dips_edges`: The edges for each dip.
        - `IS-Score`: the final IS-Score value.
    - `SINGLE_PEAK_PENALIZATION`: Contains the detected bands, the unsound frequencies, and the plot of the detected bands.
        - `point_for_penalization`: The list of point used as evaluation for each peak.
        - `peak_penalized`: The list of peak penalized.
        - `single_peak_penalization`: The single peak penalization value.
    - `REGION_PEAK_PENALIZATION`: Contains the penalized region peak values, the unsound frequencies, and the plot of the penalized spectrum.
        - `overfitting`: The list of distances between the frequency prominence and the baseline (if the frequency prominence is below the baseline).
        - `overfitting_penalties`: The list of overfitting penalties.
        - `overfitting_index`: The indexes where the overfitting happens.
        - `underfitting`: The list of distances between the frequency prominence and the baseline (if the frequency prominence is above the baseline)
        - `underfitting_penalties`: The list of underfitting penalties.
        - `underfitting_index`: The indexes where the underfitting happens.
        - `raman_shift_prominences`: The Raman Shift Prominences for each Raman shift in the peak region.
        - `peak_region_penalization`: The peak region penalization value.
    - `SINGLE_DIP_PENALIZATION`
        - `upper_point_for_penalization`: The list of upper point used as evaluation for each dip.
        - `lower_point_for_penalization`: The list of lower point used as evaluation for each dip.
        - `dip_penalized`: The list of dips penalized.
        - `single_dip_penalization`: The single dip penalization value.
    - `REGION_DIP_PENALIZATION`: Contains the penalized region peak values, the unsound frequencies, and the plot of the penalized spectrum.
        - `overfitting`: The list of distances between the frequency prominence and the baseline.
        - `underfitting`: The list of distances between the frequency prominence and the baseline.
        - `indexes`: The list of indexes for each dip region.
        - `raman_shift_prominences`: The Raman Shift Prominences for each Raman shift in the dip region.
        - `dip_region_penalization`: The dip region penalization value.
    - `INTENSITY_PENALIZATION`: Contains the penalized intensity values, the unsound frequencies, and the plot of the penalized spectrum.
        - `filtered_indexes`: The indexes of the spectrum where the intensity are penalized.
        - `intensity_penalization`: The intensity penalization value.
    - `AUC_PENALIZATION`: Contains the penalized AUC values, the unsound frequencies, and the plot of the penalized spectrum.
        - `interpolation`: The fake baseline that mimic an overfitting behavior (not normalized).
        - `auc_penalization`: The auc penalization value.
    - `MEAN_RATIO_PENALIZATION`: Contains the penalized mean ratio values, the unsound frequencies, and the plot of the penalized spectrum.
        - `mean_ratio_penalty`: The mean ratio penalization value.

The method ``DebugCollector.allPlot()`` return a dictionary with all the plot collected during the execution of the `getIS_Score` function, each dictionary contains a dictionary with key `plot`:

    - `SINGLE_PEAKS_DIPS_PENALIZATION`
    - `REGION_PEAK_PENALIZATION`
    - `REGION_DIP_PENALIZATION`
    - `INTENSITY_PENALIZATION`
    - `AUC_PENALIZATION`
    - `MEAN_RATIO_PENALIZATION`

Usage
-----

.. code-block:: python

    from IS_Score.IS_Score import getIS_Score
    from IS_Score.utils import DebugCollector
    import matplotlib.pyplot as plt

    spectral_axis = [...]  # Your spectral axis data
    raw_spectrum = [...]  # Your Raman spectrum data
    baseline_corrected_spectrum = [...]  # Your baseline corrected spectrum data

    DebugCollector.activate()  # Activate the debug collector
    is_score_val = getIS_Score(raw_sp=raw_spectrum, baseline_corrected_sp=baseline_corrected_spectrum, sp_axis=spectral_axis)

    data = DebugCollector.all() # Retrieve all the collected data
    dataPlot = DebugCollector.allPlot() # Retrieve all the plots generated during the process

    sp_norm = data['GENERAL']['sp_norm']
    baseline = data['GENERAL']['baseline_norm']
    peaks = data['GENERAL']['peaks']
    dips = data['GENERAL']['dips']

    fig = dataPlot['INTENSITY_PENALIZATION']['plot']
    plt.figure(fig)
    plt.show()

API Reference
-------------
.. automodule:: IS_Score.utils
    :members:
    :exclude-members: normalizeProminence, printOutputTable, normalizeSpectraBaseline



