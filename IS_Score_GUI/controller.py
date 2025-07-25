import os
import itertools

import numpy as np
import pandas as pd

from scipy.signal import find_peaks
from PyQt5.QtCore import Qt, QDir, QThreadPool
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from IS_Score_GUI.config import *
from IS_Score.utils import DebugCollector
from IS_Score.IS_Score import getIS_Score
from IS_Score_GUI.thread import PlotTask, WorkerThread
import matplotlib.collections as mcoll

class Controller:

    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.view.loadFolderAction.triggered.connect(self.loadFolderData)
        self.view.treeFileView.clicked.connect(self.loadSpectra)

        baselines = [(k, v.getBaselineParamsWithPlaceholders()) for k, v in self.model.baselineAlgorithms.items()]
        self.view.addBaselines(baselines)

        self.view.baselineComboBox.currentIndexChanged.connect(self.changeBaselineAlgorithm)
        self.view.computeISScoreButton.clicked.connect(self.computeISScore)

        #region Custom Peak and Dips

        self.view.customPeaksCheckBox.stateChanged.connect(lambda state, t='peak': self.allowCustomBands(state, t))
        self.view.customDipsCheckBox.stateChanged.connect(lambda state, t='dip': self.allowCustomBands(state, t))

        self.view.sliderPeaks.valueChanged.connect(lambda value, t='peak': self.searchBands(value, t))
        self.view.sliderDips.valueChanged.connect(lambda value, t='dip': self.searchBands(value, t))

        self.view.sliderPeaks.sliderReleased.connect(lambda t='peak': self.storeBands(t))
        self.view.sliderDips.sliderReleased.connect(lambda t='dip': self.storeBands(t))

        self.view.customPeaksList.itemClicked.connect(lambda item, t='peak': self.highlightBand(item, t))
        self.view.customDipsList.itemClicked.connect(lambda item, t='dip': self.highlightBand(item, t))

        #endregion

        self.view.treeFolderView.clicked.connect(self.selectFolder)

        for baselineName, (checkBox, params) in self.view.baselineWidgetFolderTab.items():
            checkBox.toggled.connect(lambda checked, b=baselineName, p=params: self.allowParametersFolder(b, p, checked))

            for param in params:
                param.focusOut.connect(lambda bn=baselineName, p=param: self.updateParam(bn, p))

        self.view.computeISScoreOnFolderBtn.clicked.connect(self.callWorkerISScoreFolder)
        self.view.outliersTable.cellDoubleClicked.connect(self.checkOutlier)

        self.view.allowMultipleHyperparametersCheckBox.stateChanged.connect(self.allowMultipleParameters)

        #self.autoLoad()

    def allowMultipleParameters(self, state):
        regex = "[a-zA-Z0-9,.]*" if state == Qt.Checked else "[a-zA-Z0-9.]*"
        self.view.allowMultipleParameters(regex, state)

    def selectFolder(self, index):
        filepath = self.model.treeFolderModel.filePath(index)
        self.model.selectedFolder = filepath
        self.view.currentFolderLabel.setText(f"Selected Folder: {filepath}")

        self.plotFolderData()

    def plotFolderData(self):
        spectra_sum = None
        n_files = 0
        for root, dirs, files in os.walk(self.model.selectedFolder):
            for f in files:
                filepath = f"{self.model.selectedFolder}/{f}"
                sp_axis, sp_data = self.model.loadSpectraFromFile(filepath)
                spectra_sum = sp_data if spectra_sum is None else spectra_sum + sp_data
            n_files = len(files)
        mean_spectra = spectra_sum / n_files

        self.model.meanSpectra = mean_spectra
        self.model.folderAxis = sp_axis

    def callWorkerISScoreFolder(self):
        if self.model.selectedFolder is None:
            QMessageBox.critical(self.view, "Error", "No folder selected.")
            return

        self.view.startLoadingDialog()
        self.worker = WorkerThread(self.computeISScoreFolder)
        self.worker.progress.connect(self.view.loadingDlg.update_progress)
        self.worker.finished_signal.connect(lambda: self.view.loadingDlg.close())
        self.worker.start()

    def updateParam(self, baselineName, paramWidget):
        args = self.model.getBaselineParams(baselineName)
        text = paramWidget.toPlainText()
        if "[" in text:
            text = text.replace("[", "").replace("]", "")
            args[paramWidget.objectName()] = [[eval(el) for el in text.split(",") if el != ""]]
        elif "," in text:
            # Multiple values
            args[paramWidget.objectName()] = [eval(el) for el in text.split(",") if el != ""]
        else:
            args[paramWidget.objectName()] = "" if text == "" else eval(text)

        self.model.setBaselineArguments(baselineName, args)


    def allowParametersFolder(self, baselineName, params, checked):
        for param in params:
            param.setEnabled(checked)

        if checked:
            self.model.enableBaseline(baselineName)
        else:
            self.model.disableBaseline(baselineName)


    def highlightBand(self, item, band_type):
        bandList = self.view.getCustomList(band_type)
        band_to_highlight = int(bandList.itemWidget(item).layout().itemAt(1).widget().objectName())

        ax = self.view.spectrumPlot.canvas.axes

        color = 'tab:green' if band_type == "peak" else 'blue'
        scatter_plots = [col for col in ax.collections if isinstance(col, mcoll.PathCollection)]
        for plot in scatter_plots:
            if len(plot.get_label().split(" ")) > 1 and plot.get_label().split(" ")[1].lower()[:-1] == band_type:
                plot.remove()
                all_indexes = self.model.getCustomBandIndexList(band_type)
                ax.scatter(self.model.spectral_axis[all_indexes], self.model.spectral_data_raw[all_indexes], color=color, marker='x', s=100,
                           label='Custom ' + band_type.capitalize() + 's')
                ax.scatter(self.model.spectral_axis[band_to_highlight], self.model.spectral_data_raw[band_to_highlight], s=100, color='tab:red', marker='x')
            elif "Selected" in plot.get_label():
                plot.remove()

        ax.figure.canvas.draw()
        ax.legend()

    def storeBands(self, band_type):
        self.model.clearCustomBands(band_type)
        listWidget = self.view.getCustomList(band_type)

        for item in listWidget.findItems("*", Qt.MatchWildcard):
            item_layout = listWidget.itemWidget(item).layout()
            index = int(item_layout.itemAt(1).widget().objectName())
            raman_shift = item_layout.itemAt(0).widget().text().split(" ")[2]
            customBand = self.model.createCustomBand(index, raman_shift)
            self.model.addCustomBand(customBand, band_type)

    def searchBands(self, value, band_type):
        self.model.clearCustomBands(band_type)
        self.view.clearCustomBandList(band_type)

        prom_value = value / 1000.0

        peaks, dips = [], []
        if band_type == "peak":
            peaks, _ = find_peaks(self.model.spectral_data_norm_alone, prominence=(prom_value, None))
            self.plotLoadedSpectra(custom_peaks=peaks, custom_dips=self.model.getCustomBandIndexList("dip"))
        else:
            dips, _ = find_peaks(-self.model.spectral_data_norm_alone, prominence=(prom_value, None))
            self.plotLoadedSpectra(custom_peaks=self.model.getCustomBandIndexList("peak"),custom_dips=dips)

        bands = peaks if band_type == "peak" else dips
        for band in bands:
            item, removeButton = self.view.addCustomBandWidget(band_type, band, self.model.spectral_axis[band])
            removeButton.clicked.connect(lambda _, it=item, t=band_type: self.onRemoveButtonClicked(it, t))

    def onRemoveButtonClicked(self, item, band_type):
        bandList = self.view.getCustomList(band_type)
        bandListLayout = bandList.itemWidget(item).layout()
        index = int(bandListLayout.itemAt(1).widget().objectName())
        self.model.removeCustomBand(index, band_type)
        bandList.takeItem(bandList.row(item))
        self.plotLoadedSpectra(custom_peaks=self.model.getCustomBandIndexList("peak"),custom_dips= self.model.getCustomBandIndexList("dip"))

    def allowCustomBands(self, state, band_type):
        widget = self.view.customPeaksCheckBox if band_type == "peak" else self.view.customDipsCheckBox

        if self.model.spectral_axis is None:
            widget.setChecked(False)
            QMessageBox.critical(self.view, "Error", "Spectra not loaded.")
            return

        # Allow the custom band
        if state == Qt.Checked:
            self.view.showCustomBandWidget(band_type)
            self.model.enableCustomBands(band_type)
        else:
            self.view.hideCustomBandWidget(band_type)
            self.model.disableCustomBands(band_type)
            self.plotLoadedSpectra()

    def getBaselineCorrectionAlgorithms(self):
        algs = []
        for alg_name, param in self.model.enabledBaselines.items():
            if len(param.items()) == 0:
                val = ({}, alg_name)
            else:
                if any(isinstance(v, list) for v in param.values()):
                    # Construct a dictionary for a product
                    tmp = [[v] if not isinstance(v, list) else v for v in param.values()]
                    val = []
                    for el in itertools.product(*tmp):
                        d = dict(zip(param.keys(), el))
                        param_string = ",".join([f'{k}={v}' for k, v in d.items()])

                        value = (d, f"{alg_name}({param_string})")
                        val.append(value)
                else:
                    param_string = ",".join([f'{k}={v}' for k, v in param.items()])
                    val = (param, f"{alg_name}({param_string})")

            if isinstance(val, list):
                algs.extend(val)
            else:
                algs.append(val)
        return algs

    def computeISScoreFolder(self, progress_callback):
        baselineAlgs = self.getBaselineCorrectionAlgorithms()

        self.model.metricValDict = {key: [] for key in [el[1] for el in baselineAlgs]}
        filenames = []

        spectra_sum = None

        for root, dirs, files in os.walk(self.model.selectedFolder):
            cur_it, total_iteration = 0, len(files) * len(baselineAlgs)
            for f in files:
                filepath = f"{self.model.selectedFolder}/{f}"
                filenames.append(filepath)

                sp_axis, sp_data = self.model.loadSpectraFromFile(filepath)
                sp = self.model.getSpectrum(sp_axis, sp_data)

                spectra_sum = sp.spectral_data if spectra_sum is None else spectra_sum + sp.spectral_data

                for params, alg_name in baselineAlgs:
                    alg_func = self.model.baselineAlgorithms[alg_name.split("(")[0]]
                    alg_func.setParams(params)

                    sp_corrected = alg_func.apply(sp)
                    #DebugCollector.activate()
                    is_score_args = {}
                    is_score = getIS_Score(raw_sp=sp_data,
                                           baseline_corrected_sp=sp_corrected,
                                           sp_axis=sp_axis, **is_score_args)

                    #info = DebugCollector.all()
                    #DebugCollector.deactivate()

                    self.model.metricValDict[alg_name].append(is_score)
                    cur_it += 1

                    progress_percentage = int((cur_it / total_iteration) * 100)
                    if progress_callback is not None:
                        progress_callback(progress_percentage)

        df_res = pd.DataFrame(self.model.metricValDict).melt()
        df_res['filename'] = filenames * len(baselineAlgs)

        mean_spectra = spectra_sum / len(filenames)

        self.plotBoxplot(df_res)

        self.plotMeanSpectra(sp_axis, mean_spectra, baselineAlgs)
        self.updateOutliersTable(df_res)

    def checkOutlier(self, row):
        row_data = [self.view.outliersTable.item(row, col).text() for col in range(self.view.outliersTable.columnCount())]
        folder = self.view.currentFolderLabel.text().replace("Selected Folder: ", "")
        file_index = self.model.treeFileModel.index(f"{folder}/{row_data[0]}")

        self.loadSpectra(file_index)

        self.view.treeFileView.setCurrentIndex(file_index)
        self.view.treeFileView.scrollTo(file_index)

        alg_name = row_data[1].split("(")[0]
        params = row_data[1].replace("(", "").replace(")", "").replace(alg_name, "")
        self.view.baselineComboBox.setCurrentText(alg_name)

        for el in params.split(","):
            name_param, value = el.split("=")[0], eval(el.split("=")[1])
            for w in self.view.hyperparametersWidgetFileTab:
                if w[0] == name_param:
                    w[1].setText(str(value))

        self.view.customPeaksCheckBox.setChecked(False)
        self.view.customDipsCheckBox.setChecked(False)

        self.computeISScore()
        self.view.tabs.setCurrentIndex(0)


    def updateOutliersTable(self, df_res):
            self.view.outliersTable.setRowCount(0)
            self.view.outliersTable.setColumnCount(3)
            for baseline_alg in df_res['variable'].unique():
                df_alg = df_res[df_res['variable'] == baseline_alg]
                Q1, Q3 = np.percentile(df_alg['value'], [25,75])
                IQR = Q3 - Q1
                lower_bound, upper_bound = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                outliers = df_alg[(df_alg['value'] < lower_bound) | (df_alg['value'] > upper_bound)]

                self.view.showOutliers(outliers)

    def plotMeanSpectra(self, sp_axis, mean_spectra, baselineAlgs):
        baselines = []

        for params, alg_name in baselineAlgs:
            alg_func = self.model.baselineAlgorithms[alg_name.split("(")[0]]
            alg_func.setParams(params)

            sp_corrected = alg_func.apply(mean_spectra, sp_axis)
            baselines.append(mean_spectra - sp_corrected)

        self.view.showMeanSpectra(sp_axis, mean_spectra, baselines, baselineAlgs)




    def plotBoxplot(self, df_res):
        self.view.showBoxplot(df_res)


    def computeISScore(self):
        hyperparameters = {}
        if len(self.view.hyperparametersWidgetFileTab) > 0:
            for param, widget in self.view.hyperparametersWidgetFileTab:
                try:
                    hyperparameters[param] = eval(widget.text())
                except Exception as e:
                    QMessageBox.critical(self.view, "Error", f"Invalid value for {param}: {e}")
                    return

        self.model.computeBaseline(**hyperparameters)

        is_score_args = {}

        if self.model.customPeaks is not None:
            is_score_args['custom_peaks'] = self.model.getCustomBandIndexList("peak")
        if self.model.customDips is not None:
            is_score_args['custom_dips'] = self.model.getCustomBandIndexList('dip')


        DebugCollector.activate()

        is_score = getIS_Score(raw_sp=self.model.spectral_data_raw,
                               baseline_corrected_sp=self.model.baselineCorrected,
                               sp_axis=self.model.spectral_axis, **is_score_args)

        info = DebugCollector.all()
        DebugCollector.deactivate()

        self.model.spectral_data_norm = info['GENERAL']['sp_norm']
        self.model.baseline_norm = info['GENERAL']['baseline_norm']

        self.plotBaselineCorrected()
        self.view.showBaselineMetricResults(info)

        pool = QThreadPool.globalInstance()
        plot_tasks = [
            PlotTask(self.plotIntensityPenalization, info),
            PlotTask(self.plotSinglePeakDipPenalization, info),
            PlotTask(self.plotAUCpenalization, info),
            PlotTask(self.plotPeakRegionPenalization, info),
            PlotTask(self.plotDipRegionPenalization, info)
        ]

        for task in plot_tasks:
            pool.start(task)

    def plotPeakRegionPenalization(self, info):
        self.view.plotPeakRegionPenalization(spectral_axis=self.model.spectral_axis,
                                             spectral_data_norm=self.model.spectral_data_norm,
                                             baseline_norm=self.model.baseline_norm,
                                             peaks=info['GENERAL']['peaks'],
                                             peaks_edges=info['GENERAL']['peaks_edges'],
                                             freq_prom=info['REGION_PEAK_PENALIZATION']['raman_shift_prominences'],
                                             overfitting=info["REGION_PEAK_PENALIZATION"]["overfitting"],
                                             overfitting_index=info["REGION_PEAK_PENALIZATION"]["overfitting_index"],
                                             underfitting=info["REGION_PEAK_PENALIZATION"]["underfitting"],
                                             underfitting_index=info["REGION_PEAK_PENALIZATION"]["underfitting_index"],
                                             peak_region_penalty=info["REGION_PEAK_PENALIZATION"]["peak_region_penalization"]
                                             )

    def plotDipRegionPenalization(self, info):
        self.view.plotDipRegionPenalization(spectral_axis=self.model.spectral_axis,
                                            spectral_data_norm=self.model.spectral_data_norm,
                                            baseline_norm=self.model.baseline_norm,
                                            dips=info['GENERAL']['dips'],
                                            dips_edges=info['GENERAL']['dips_edges'],
                                            freq_prom=info['REGION_DIP_PENALIZATION']['raman_shift_prominences'],
                                            overfitting=info["REGION_DIP_PENALIZATION"]["overfitting"],
                                            underfitting=info["REGION_DIP_PENALIZATION"]["underfitting"],
                                            indexes=info["REGION_DIP_PENALIZATION"]["indexes"],
                                            dip_region_penalty=info["REGION_DIP_PENALIZATION"]["dip_region_penalization"]
                                            )

    def plotAUCpenalization(self, info):
        self.view.plotAUCpenalization(spectral_axis=self.model.spectral_axis,
                                      spectral_data=self.model.spectral_data_raw,
                                      baseline=self.model.baseline,
                                      interp=info['AUC_PENALIZATION']['interpolation'],
                                      auc_penalty=info["AUC_PENALIZATION"]["auc_penalization"])

    def plotSinglePeakDipPenalization(self, info):
        self.view.plotSinglePeakDipPenalization(spectral_axis=self.model.spectral_axis,
                                                spectral_data_norm=self.model.spectral_data_norm,
                                                baseline_norm=self.model.baseline_norm,
                                                peaks=info['GENERAL']['peaks'],
                                                peak_penalized=info['SINGLE_PEAK_PENALIZATION']['peak_penalized'],
                                                peak_points=info['SINGLE_PEAK_PENALIZATION']['point_for_penalization'],
                                                peak_penalization=info["SINGLE_PEAK_PENALIZATION"]["single_peak_penalization"],
                                                dips=info['GENERAL']['dips'],
                                                dip_penalized=info["SINGLE_DIP_PENALIZATION"]["dip_penalized"],
                                                dip_upper_points=info["SINGLE_DIP_PENALIZATION"]["upper_point_for_penalization"],
                                                dip_lower_points=info["SINGLE_DIP_PENALIZATION"]["lower_point_for_penalization"],
                                                dip_penalization=info["SINGLE_DIP_PENALIZATION"]["single_dip_penalization"])

    def plotIntensityPenalization(self, info):
        self.view.plotIntensityPenalization(spectral_axis=self.model.spectral_axis,
                                            spectral_data_norm=self.model.spectral_data_norm,
                                            baseline_norm=self.model.baseline_norm,
                                            intensity_indexes=info['INTENSITY_PENALIZATION']['filtered_indexes'],
                                            penalty_value=info["INTENSITY_PENALIZATION"]["intensity_penalization"])

    def changeBaselineAlgorithm(self):
        baseline_name = self.view.baselineComboBox.currentText()
        self.view.removeHyperparameterWidgets()

        params = self.model.baselineAlgorithms[baseline_name].getBaselineParams()

        if params is not None:
            for param in params:
                self.view.addHyperparameterWidget(param_name=param, placeholder=PLACEHOLDERS[param])

        self.model.setCurrentBaseline(baseline_name)


    def plotBaselineCorrected(self):
        self.view.plotBaselineCorrected(spectral_axis=self.model.spectral_axis,
                                        spectral_data_norm=self.model.spectral_data_norm,
                                        baseline_norm=self.model.baseline_norm)

    def _setupTreeModel(self, folder_path, modelTree, viewTree):
        modelTree.setModelRootPath(folder_path)
        viewTree.setModel(modelTree)
        viewTree.setRootIndex(modelTree.index(folder_path))
        viewTree.setColumnHidden(1, True)
        viewTree.setColumnWidth(0, 300)


    def loadFolderData(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        folder_path = dlg.getExistingDirectory(None, "Select Folder", "")

        # First Tab
        self._setupTreeModel(folder_path, self.model.treeFileModel, self.view.treeFileView)
        # Second Tab
        self._setupTreeModel(folder_path, self.model.treeFolderModel, self.view.treeFolderView)

        self.view.treeFolderView.model().setFilter(QDir.Dirs | QDir.NoDotAndDotDot)

    def plotLoadedSpectra(self, custom_peaks=None, custom_dips=None):
        self.view.plotLoadedSpectra(spectral_axis=self.model.spectral_axis,
                                    spectral_data=self.model.spectral_data_raw,
                                    custom_peaks=custom_peaks,
                                    custom_dips=custom_dips)

    def loadSpectra(self, index):
        success = self.model.loadSpectra(index)

        if not success:
            QMessageBox.critical(self.view, "Error", "Invalid File Format")
            return

        self.plotLoadedSpectra()

        self.view.customPeaksCheckBox.setChecked(False)
        self.view.customDipsCheckBox.setChecked(False)

        self.view.clearBaselineResultsTable()


    def autoLoad(self):
        folder_path = "bin/dataset/35days"
        self.model.treeFileModel.setModelRootPath(folder_path)

        self.view.treeFileView.setModel(self.model.treeFileModel)
        self.view.treeFileView.setRootIndex(self.model.treeFileModel.index(folder_path))  # Set the root index
        self.view.treeFileView.setColumnHidden(1, True)
        self.view.treeFileView.setColumnWidth(0, 300)  # Adjust column width