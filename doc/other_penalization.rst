Other Penalization
==================
Introduction
------------

The `Other Penalization` module provides functionality to penalize irregularities in the baseline related to the other components such as:
- Intensity: Exploit the intensity values of Raman spectra and baseline;
- Area Under the Curve (AUC): Use the AUC of the baseline and Raman spectra to assess the baseline quality;
- Mean Ratio: Evaluates baseline fit by measuring how consistently spectral dips lie above it across multiple denoised versions, penalizing underfitting when less than 50% of dips are above the baseline.


Intensity
---------
.. automodule:: IS_Score.other_penalization.intensity_penalization
   :members:

Area Under the Curve (AUC)
--------------------------
.. automodule:: IS_Score.other_penalization.auc_penalization
   :members:

Mean Ratio
----------
.. automodule:: IS_Score.other_penalization.mean_ratio_penalization
   :members:
