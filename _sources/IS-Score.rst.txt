IS-Score
===============

Introduction
------------
The IS-Score module provides an algorithm to generate a numerical assessment that quantifies the quality of the baseline fitting, avoiding the
need for manual inspection.

Installation
------------
.. code-block:: python

    pip install IS-Score

Usage
-----
1. **Import the package**

.. code-block:: python

    from IS_Score import getIS_Score

2. **Prepare your data:** Ensure you have your Raman spectrum, the corresponding baseline corrected spectrum and the spectral axis ready. These should be in form of arrays or lists.
.. code-block:: python

    raw_spectrum = [...]  # Your Raman spectrum data
    baseline_corrected_spectrum = [...]  # Your baseline data
    spectral_axis = [...]  # The spectral axis data

3. **Calculate the IS-Score:** Call the getIS_Score function with the necessary parameters

.. code-block:: python

    is_score = getIS_Score(raw_sp=raw_spectrum, baseline_corrected_sp=baseline_corrected_spectrum, sp_axis=spectral_axis)
    print(f"IS-Score Value: {is_score}")

4. **Optional parameters:** The getIS_Score function has optional parameters that allow you to customize the baseline metric calculation.
All the details about the optional parameters can be found in the API Reference section and the paper.

.. code-block:: python

    args = {
        "peaks_dips_tolerance": {"peaks": 5, "dips": 5}, # For automatic peak detection
        "custom_peaks": [...],
        "custom_dips": [...]
    }
    is_score = getIS_Score(raw_sp=raw_spectrum, baseline_corrected_sp=baseline_corrected_spectrum, sp_axis=spectral_axis, **args)

If you want to use the custom peaks and dips instead of using the automatic detection of the bands, you can pass them as lists in the `args` dictionary.

API Reference
-------------

.. automodule:: IS_Score.IS_Score
   :members:
