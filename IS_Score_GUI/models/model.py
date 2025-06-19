import numpy as np
import pandas as pd
import ramanspy as rp
import ramanspy.preprocessing as rpr
from IS_Score_GUI.models.folder_models import FolderTreeModel
from IS_Score_GUI.models.baseline_algorithms import BaselineAlgorithm, BubbleFillAlgorithm
class Model:
    def __init__(self):
        self.treeFileModel = FolderTreeModel(None)

        self.spectral_axis = None
        self.spectral_data_raw = None

        self.currentBaseline = "BubbleFill"
        self.baselineCorrected = None
        self.baseline = None

        self.spectral_data_norm = None
        self.baseline_norm = None


        self.baselineAlgorithms = {
            "ASLS": BaselineAlgorithm("ASLS", rpr.baseline.ASLS(), params=["lam", "p"]),
            "IASLS": BaselineAlgorithm("IASLS", rpr.baseline.IASLS(), params=["lam", "p"]),
            "AIRPLS": BaselineAlgorithm("AIRPLS", rpr.baseline.AIRPLS(), params=["lam"]),
            "DRPLS": BaselineAlgorithm("DRPLS", rpr.baseline.DRPLS(), params=["lam"]),
            "ModPoly": BaselineAlgorithm("ModPoly", rpr.baseline.ModPoly(), params=["poly_order"]),
            "IModPoly": BaselineAlgorithm("IModPoly", rpr.baseline.IModPoly(), params=["poly_order"]),
            "Goldindec": BaselineAlgorithm("Goldindec", rpr.baseline.Goldindec()),
            "IRSQR": BaselineAlgorithm("IRSQR", rpr.baseline.IRSQR()),
            "BubbleFill": BubbleFillAlgorithm("BubbleFill", None, params=["min_bubble_widths"]),
        }


    def computeBaseline(self, **args):
        sp = rp.Spectrum(spectral_axis=self.spectral_axis, spectral_data=self.spectral_data_raw)

        self.baselineAlgorithms[self.currentBaseline].setParams(args)
        self.baselineCorrected = self.baselineAlgorithms[self.currentBaseline].apply(sp)
        self.baseline = self.spectral_data_raw - self.baselineCorrected


    def setCurrentBaseline(self, baseline_name):
        self.currentBaseline = baseline_name

    def setRawSpectra(self, spectral_axis, spectral_data):
        if spectral_axis is None or spectral_data is None:
            raise ValueError("Spectral axis and data cannot be None")

        self.spectral_axis = spectral_axis
        self.spectral_data_raw = spectral_data


    def loadSpectra(self, index):
        file_path = self.treeFileModel.filePath(index)

        if file_path.endswith(".txt"):
            tmp = np.loadtxt(file_path)
            self.setRawSpectra(tmp[:, 0], tmp[:, 1])
        elif file_path.endswith(".csv"):
            df = pd.read_csv(file_path, header=None)
            self.setRawSpectra(df[0].values, df[1].values)
        else:
            return False

        return True