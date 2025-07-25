import numpy as np
import pandas as pd
import ramanspy as rp
import matplotlib.pyplot as plt
import ramanspy.preprocessing as rpr
from IS_Score.IS_Score import getIS_Score
from IS_Score.utils import DebugCollector

df = pd.read_csv("bin/spectrum_example.csv", header=None)

sp = rp.Spectrum(spectral_axis=df.iloc[:, 0].values, spectral_data= df.iloc[:, 1].values)

sp_corrected = rpr.baseline.ASLS(lam=5000, p=0.007).apply(sp)

DebugCollector.activate()
is_score_val = getIS_Score(raw_sp=sp.spectral_data, baseline_corrected_sp=sp_corrected.spectral_data, sp_axis=sp.spectral_axis)

data = DebugCollector.all()
dataPlot = DebugCollector.allPlot()

sp_normalized = data['GENERAL']['sp_norm']
baseline_normalized = data['GENERAL']['baseline_norm']
peaks, dips = data['GENERAL']['peaks'], data['GENERAL']['dips']
peaks_edges, dips_edges = data['GENERAL']['peaks_edges'], data['GENERAL']['dips_edges']
is_score = data['GENERAL']['IS-Score']


fig = dataPlot['INTENSITY_PENALIZATION']['plot']
plt.figure(fig)
plt.show()

print(is_score)
