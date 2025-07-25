import pandas as pd
import ramanspy as rp
import ramanspy.preprocessing as rpr
from IS_Score.IS_Score import getIS_Score

if __name__ == "__main__":

    df = pd.read_csv("bin/spectrum_example.csv", header=None)
    sp = rp.Spectrum(spectral_axis=df.iloc[:, 0].values, spectral_data=df.iloc[:, 1].values)

    sp_corrected = rpr.baseline.ASLS(lam=5000, p=0.007).apply(sp)

    is_score_val = getIS_Score(raw_sp=sp.spectral_data, baseline_corrected_sp=sp_corrected.spectral_data,
                               sp_axis=sp.spectral_axis)

    print(is_score_val)