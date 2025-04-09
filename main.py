import numpy as np
from IS_Score.IS_Score import getIS_Score

if __name__ == "__main__":

    spectral_axis = np.arange(1000, 2000, 1)
    spectral_data = np.random.rand(1000)
    spectral_data_corrected = spectral_data - np.random.rand(1000) * 0.1


    # Subtract baseline
    getIS_Score(raw_sp=spectral_data, baseline_corrected_sp=spectral_data_corrected, sp_axis=spectral_axis)
