import numpy as np
from IS_Score.IS_Score import getIS_Score

if __name__ == "__main__":

    sp = np.loadtxt("bin/example/spectrum.txt")
    sp_corr = np.loadtxt("bin/example/spectrum_corrected.txt")

    is_score_val = getIS_Score(raw_sp=sp[:, 1], baseline_corrected_sp=sp_corr[:, 1],
                               sp_axis=sp[:, 0])

    print(is_score_val)

