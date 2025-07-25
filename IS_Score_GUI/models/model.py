import numpy as np
import pandas as pd
import ramanspy as rp
import ramanspy.preprocessing as rpr
from IS_Score_GUI.models.folder_models import FolderTreeModel
from IS_Score_GUI.models.baseline_algorithms import BaselineAlgorithm, BubbleFillAlgorithm
from IS_Score_GUI.models.custom_band import CustomBand

class Model:
    def __init__(self):
        self.treeFileModel = FolderTreeModel(None)
        self.treeFolderModel = FolderTreeModel(None)

        self.spectral_axis = None
        self.spectral_data_raw = None
        self.spectral_data_norm_alone = None

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

        self.customPeaks = None
        self.customDips = None

        # Folder Analysis
        self.selectedFolder = None
        self.enabledBaselines = {}
        self.metricValDict = {}
        self.meanSpectra = None
        self.folderAxis = None



    #region Folder
    def enableBaseline(self, baseline):
        self.enabledBaselines[baseline] = {}

    def disableBaseline(self, baseline):
        self.enabledBaselines.pop(baseline, None)

    def getBaselineParams(self, baseline):
        return self.enabledBaselines.get(baseline, {})

    def setBaselineArguments(self, baseline, args):
        if baseline in self.enabledBaselines:
            self.enabledBaselines[baseline] = args
        else:
            raise ValueError(f"Baseline {baseline} is not enabled.")

    #endregion

    def createCustomBand(self, band_index, raman_shift):
        return CustomBand(band_index, raman_shift)

    def addCustomBand(self, custom_band, band_type):
        if band_type == "peak" and self.customPeaks is not None:
            self.customPeaks.append(custom_band)
        elif band_type == "dip" and self.customDips is not None:
            self.customDips.append(custom_band)

    def removeCustomBand(self, band, type):
        if type == "peak" and self.customPeaks is not None:
            self.customPeaks.remove(CustomBand(band))
        elif type == "dip" and self.customDips is not None:
            self.customDips.remove(CustomBand(band))

    def clearCustomBands(self, band_type):
        if band_type == "peak":
            self.customPeaks = []
        else:
            self.customDips = []

    def enableCustomBands(self, band_type):
        if band_type == "peak":
            self.customPeaks = []
        else:
            self.customDips = []

    def disableCustomBands(self, band_type):
        if band_type == "peak":
            self.customPeaks = None
        else:
            self.customDips = None

    def storeCustomBands(self):
        peak_data = self.getCustomBandIndexList("peak")
        dip_data = self.getCustomBandIndexList("dip")

        np.savetxt("custom_peaks.txt", peak_data, fmt="%d", header="Peak Data")
        np.savetxt("custom_dips.txt", dip_data, fmt="%d", header="Dip Data")

        print("Saved")


    def getCustomBandIndexList(self, band_type):
        if band_type == "peak" and self.customPeaks is None:
            return []
        elif band_type == "dip" and self.customDips is None:
            return []
        return [el.bandIndex for el in self.customPeaks] if band_type == "peak" else [el.bandIndex for el in self.customDips]

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

        min_val, max_val = min(self.spectral_data_raw), max(self.spectral_data_raw)
        self.spectral_data_norm_alone = (self.spectral_data_raw - min_val) / (max_val - min_val)

    def loadSpectraFromFile(self, file_path):
        spectral_axis, spectral_data = None, None
        if file_path.endswith(".txt"):
            tmp = np.loadtxt(file_path)
            # The first column correspond to the spectral axis
            tmp = pd.Series(tmp[:, 1], index=tmp[:, 0]).sort_index()
            spectral_axis, spectral_data = tmp.index.values, tmp.values
        elif file_path.endswith(".csv"):
            df = pd.read_csv(file_path, header=None)
            spectral_axis, spectral_data = df[0].values, df[1].values

        return spectral_axis, spectral_data

    def getSpectrum(self, sp_axis, sp_data):
        return rp.Spectrum(spectral_axis=sp_axis, spectral_data=sp_data)


    def loadSpectra(self, index):
        file_path = self.treeFileModel.filePath(index)
        spectral_axis, spectral_data = self.loadSpectraFromFile(file_path)

        if spectral_axis is None or spectral_data is None:
            return False

        self.setRawSpectra(spectral_axis, spectral_data)
        return True