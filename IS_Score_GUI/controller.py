import os
import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt, QDir, QThreadPool, QRegExp
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from IS_Score_GUI.config import *
from IS_Score.utils import DebugCollector
from IS_Score.IS_Score import getIS_Score
from IS_Score_GUI.thread import PlotTask, WorkerThread


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
        DebugCollector.activate()

        is_score = getIS_Score(raw_sp=self.model.spectral_data_raw,
                               baseline_corrected_sp=self.model.baselineCorrected,
                               sp_axis=self.model.spectral_axis)

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
                                             freq_prom=info['REGION_PEAK_PENALIZATION']['frequencies_prominence'],
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
                                            freq_prom=info['REGION_DIP_PENALIZATION']['frequencies_prominence'],
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

    def loadFolderData(self):

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        folder_path = dlg.getExistingDirectory(None, "Select Folder", "")

        self.model.treeFileModel.setModelRootPath(folder_path)

        self.view.treeFileView.setModel(self.model.treeFileModel)
        self.view.treeFileView.setRootIndex(self.model.treeFileModel.index(folder_path))
        self.view.treeFileView.setColumnHidden(1, True)
        self.view.treeFileView.setColumnWidth(0, 300)

    def plotLoadedSpectra(self):
        self.view.plotLoadedSpectra(spectral_axis=self.model.spectral_axis,
                                    spectral_data=self.model.spectral_data_raw)

    def loadSpectra(self, index):
        success = self.model.loadSpectra(index)

        if not success:
            QMessageBox.critical(self.view, "Error", "Invalid File Format")
            return

        self.plotLoadedSpectra()

