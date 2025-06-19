from IS_Score_GUI.views.addon_widget import EmitQLineEdit, PlotWidget, PieChartWidget, LoadingDialog
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator, QBrush, QColor

from PyQt5.QtWidgets import QMainWindow, QMenuBar, QWidget, QCheckBox, QListWidget, QSlider, QSizePolicy, \
    QAbstractItemView, QLabel, QTableWidgetItem

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QListWidgetItem

from PyQt5.QtWidgets import QTabWidget, QTreeView, QComboBox, QPushButton, QTableWidget
from IS_Score_GUI.config import *

class IS_Score_GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IS-Score GUI")

        self.hyperparametersWidgetFileTab = []
        self.baselineWidgetFolderTab = {}

        self._setupMenuBar()

        self.tabs = QTabWidget()

        self.fileTab = self._setupUI_FileTab()
        self.ISScoreAnalysisTab = self._setupUI_ISScoreAnalysisTab()

        self.tabs.addTab(self.fileTab, "Single File Analysis")
        self.tabs.addTab(self.ISScoreAnalysisTab, "IS-Score Analysis")
        self.setCentralWidget(self.tabs)
        self.show()


    def _setupUI_FileTab(self):
        # View of files
        self.treeFileView = QTreeView()
        self.treeFileView.setFixedHeight(300)
        self.treeFileView.setFixedWidth(250)

        #region Baseline algorithm choice layout
        self.baselineChoiceLayout = QVBoxLayout()
        self.baselineComboBox = QComboBox()

        self.baselineComboBox.setFixedHeight(25)
        self.baselineComboBox.setFixedWidth(250)

        minBubbleTextEdit = EmitQLineEdit()
        minBubbleTextEdit.setPlaceholderText("Min Bubble Width")
        minBubbleTextEdit.setFixedHeight(25)
        minBubbleTextEdit.setFixedWidth(250)

        self.hyperparametersWidgetFileTab.append(("min_bubble_widths", minBubbleTextEdit))

        self.computeISScoreButton = QPushButton("Compute IS-Score")
        self.computeISScoreButton.setFixedHeight(25)
        self.computeISScoreButton.setFixedWidth(250)

        self.baselineMetricResultsTable = QTableWidget()
        self.baselineMetricResultsTable.setColumnCount(2)
        self.baselineMetricResultsTable.setHorizontalHeaderLabels(["Property", "Value"])
        self.baselineMetricResultsTable.setFixedWidth(250)

        self.baselineChoiceLayout.addWidget(self.baselineComboBox)
        self.baselineChoiceLayout.addWidget(minBubbleTextEdit)
        self.baselineChoiceLayout.addWidget(self.computeISScoreButton)
        self.baselineChoiceLayout.addWidget(self.baselineMetricResultsTable)
        #endregion

        #region Custom Peaks and Dips
        self.customPeaksCheckBox = QCheckBox("Custom Peaks")
        self.customPeaksCheckBox.setChecked(False)

        self.customDipsCheckBox = QCheckBox("Custom Dips")
        self.customDipsCheckBox.setChecked(False)
        #endregion

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.treeFileView)
        leftLayout.addLayout(self.baselineChoiceLayout)
        leftLayout.addWidget(self.customPeaksCheckBox)
        leftLayout.addWidget(self.customDipsCheckBox)

        #region Spectra Sliders
        bandsLayout = QHBoxLayout()

        self.customPeaksList = QListWidget()
        self.customPeaksList.hide()
        self.customPeaksList.setFixedWidth(250)

        self.customDipsList = QListWidget()
        self.customDipsList.hide()
        self.customDipsList.setFixedWidth(250)

        bandsLayout.addWidget(self.customPeaksList)
        bandsLayout.addWidget(self.customDipsList)

        self.spectrumPlot = PlotWidget()

        spectraBandsPieLayout = QHBoxLayout()
        spectraBandsPieLayout.addWidget(self.spectrumPlot)

        self.sliderPeaks = self.createSlider()
        self.sliderDips = self.createSlider()
        #endregion

        spectraSliderLayout = QVBoxLayout()
        spectraSliderLayout.addLayout(spectraBandsPieLayout)
        spectraSliderLayout.addWidget(self.sliderPeaks)
        spectraSliderLayout.addWidget(self.sliderDips)

        mainLayout = QHBoxLayout()

        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(spectraSliderLayout)

        widget = QWidget()
        widget.setLayout(mainLayout)

        return widget

    def showBaselineMetricResults(self, results):
        table_results = [
            ('Intensity Penalization (total intensity penalized) - [Total Frequencies]',
             f"{round(results['INTENSITY_PENALIZATION']['intensity_penalization'], 4)} ({len(results['INTENSITY_PENALIZATION']['filtered_indexes'])}) - [{len(results['GENERAL']['sp_norm'])}]"),
            ('Peaks Region Penalization', round(results['REGION_PEAK_PENALIZATION']['peak_region_penalization'], 4)),
            ('Dips Region Penalization', round(results['REGION_DIP_PENALIZATION']['dip_region_penalization'], 4)),
            ('Peaks Penalized (Norm. and weighted) - [Total Peaks]',
             f"{len(results['SINGLE_PEAK_PENALIZATION']['peak_penalized'])} ({round(results['SINGLE_PEAK_PENALIZATION']['single_peak_penalization'], 4)}) - [{len(results['GENERAL']['peaks'])}]"),
            ('Dips Penalized (Norm. and weighted) - [Total Dips]',
             f"{len(results['SINGLE_DIP_PENALIZATION']['dip_penalized'])} ({round(results['SINGLE_DIP_PENALIZATION']['single_dip_penalization'], 4)}) - [{len(results['GENERAL']['dips'])}]"),
            ('Underfitting Penalization', round(results['AUC_PENALIZATION']['auc_penalization'], 4)),
            ('Mean Ratio Penalization', round(results['MEAN_RATIO_PENALIZATION']['mean_ratio_penalty'],4)),
            ('IS-Score', results['GENERAL']['IS-Score'])
        ]

        self.baselineMetricResultsTable.setRowCount(0)
        for name, res in table_results:
            row_pos = self.baselineMetricResultsTable.rowCount()
            self.baselineMetricResultsTable.insertRow(row_pos)
            self.baselineMetricResultsTable.setItem(row_pos, 0, QTableWidgetItem(name))

            item = QTableWidgetItem(str(res))
            if name == "IS-Score":
                if res < 0.7:
                    item.setBackground(QBrush(QColor(255, 0, 0)))
                elif res >= 0.7 and res < 0.8:
                    item.setBackground(QBrush(QColor(255, 255, 0)))
                else:
                    item.setBackground(QBrush(QColor(0, 153, 0)))
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            self.baselineMetricResultsTable.setItem(row_pos, 1, item)

    def plotBaselineCorrected(self, spectral_axis, spectral_data_norm, baseline_norm):
        ax = self.spectrumPlot.canvas.axes
        ax.clear()

        ax.plot(spectral_axis, spectral_data_norm, label='Normalized Spectra', color='tab:blue')
        ax.plot(spectral_axis, baseline_norm, label='Normalized Baseline', color='tab:orange')
        ax.plot(spectral_axis, spectral_data_norm - baseline_norm,label='Normalized Spectra Corrected', color='tab:green', alpha=0.4)
        ax.set_ylabel("Normalized Intensity")
        ax.set_xlabel("Raman shift (cm-1)")
        ax.legend()
        ax.grid(True)

        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.spectrumPlot.toolbar.update()


    def plotDipRegionPenalization(self, spectral_axis, spectral_data_norm, baseline_norm, **args):
        dips, dips_edges = args.get("dips", []), args.get("dips_edges", [])
        freq_prom = args.get("freq_prom", [])
        overfitting, underfitting = args.get("overfitting", []), args.get("underfitting", [])
        indexes = args.get("indexes", [])
        dip_region_penalty = args.get("dip_region_penalty", 0)

        ax = self.dipsRegionPenalizedPlot.canvas.axes

        ax.plot(spectral_axis, spectral_data_norm, color='tab:blue', alpha=0.4)
        ax.plot(spectral_axis, baseline_norm, color='tab:orange')
        ax.scatter(spectral_axis[dips], spectral_data_norm[dips], color='blue', s=100, marker='x')

        for (s, e), fp_band in zip(dips_edges, freq_prom):
            ax.plot(spectral_axis[s:e], spectral_data_norm[s:e], color='m')
            for i, fp in enumerate(fp_band):
                ax.vlines(spectral_axis[s:e][i], ymin=spectral_data_norm[s:e][i] - fp, ymax=spectral_data_norm[s:e][i],
                          color="lightblue", alpha=0.4)

        for i, (left_edge, right_edge) in enumerate(dips_edges):
            indexes_i = indexes[i]
            overfitting_i, underfitting_i = overfitting[i], underfitting[i]

            if len(overfitting_i) > 0:
                ax.vlines(x=spectral_axis[left_edge:right_edge][indexes_i],
                          ymin=baseline_norm[left_edge:right_edge][indexes_i],
                          ymax=baseline_norm[left_edge:right_edge][indexes_i] + overfitting_i, color='red',
                          alpha=0.4)

            if len(underfitting_i) > 0:
                ax.vlines(x=spectral_axis[left_edge:right_edge][indexes_i],
                          ymin=baseline_norm[left_edge:right_edge][indexes_i],
                          ymax=baseline_norm[left_edge:right_edge][indexes_i] - underfitting_i,
                          color='tab:orange',
                          alpha=0.4)
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Normalized Intensity")
        ax.grid(alpha=0.4)
        title = DIP_REGION_PLT if dip_region_penalty is None else DIP_REGION_PLT + f"\n VALUE: {round(dip_region_penalty, 4)}"

        ax.set_title(title)
        ax.legend()

    def plotPeakRegionPenalization(self, spectral_axis, spectral_data_norm, baseline_norm, **args):

        peaks, peak_edges = args.get("peaks", []), args.get("peaks_edges", [])
        freq_prom = args.get("freq_prom", [])
        overfitting_index, overfitting = args.get("overfitting_index", []), args.get("overfitting", [])
        underfitting_index, underfitting = args.get("underfitting_index", []), args.get("underfitting", [])
        peak_region_penalty = args.get("peak_region_penalty",0)

        ax = self.peaksRegionPenalizedPlot.canvas.axes
        ax.plot(spectral_axis, spectral_data_norm, color='tab:blue', alpha=0.4)
        ax.plot(spectral_axis, baseline_norm, color='tab:orange')
        ax.scatter(spectral_axis[peaks], spectral_data_norm[peaks], color='green', s=100, marker='x')

        for (s, e), fp_band in zip(peak_edges, freq_prom):
            ax.plot(spectral_axis[s:e], spectral_data_norm[s:e], color='m')
            for i, fp in enumerate(fp_band):
                ax.vlines(spectral_axis[s:e][i], ymin=spectral_data_norm[s:e][i] - fp, ymax=spectral_data_norm[s:e][i],
                          color="lightblue", alpha=0.4)

        for i, (left_edge, right_edge) in enumerate(peak_edges):
            overfitting_index_i, overfitting_i = overfitting_index[i], overfitting[i]
            underfitting_index_i, underfitting_i = underfitting_index[i], underfitting[i]

            if len(overfitting_i) > 0:
                ax.vlines(x=spectral_axis[left_edge:right_edge][overfitting_index_i],
                          ymin=baseline_norm[left_edge:right_edge][overfitting_index_i],
                          ymax=baseline_norm[left_edge:right_edge][overfitting_index_i] - overfitting_i, color='red',
                          alpha=0.4)

            if len(underfitting_i) > 0:
                ax.vlines(x=spectral_axis[left_edge:right_edge][underfitting_index_i],
                          ymin=baseline_norm[left_edge:right_edge][underfitting_index_i],
                          ymax=baseline_norm[left_edge:right_edge][underfitting_index_i] + underfitting_i,
                          color='tab:orange',
                          alpha=0.4)
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Normalized Intensity")
        ax.grid(alpha=0.4)
        title = PEAK_REGION_PLT if peak_region_penalty is None else PEAK_REGION_PLT + f"\n VALUE: {round(peak_region_penalty,4)}"
        ax.set_title(title)
        ax.legend()

    def plotIntensityPenalization(self, spectral_axis, spectral_data_norm, baseline_norm, intensity_indexes, penalty_value):
        ax = self.intensityPenalizedPlot.canvas.axes
        ax.clear()

        ax.plot(spectral_axis, spectral_data_norm, color='tab:blue', alpha=0.4)
        ax.plot(spectral_axis, baseline_norm, color='tab:orange')
        ax.scatter(spectral_axis[intensity_indexes], spectral_data_norm[intensity_indexes], c='red', s=25, alpha=0.5)
        ax.set_ylabel("Normalized Intensity")
        ax.set_xlabel("Raman Shift (cm-1)")
        title = INTENSITY_PLT if penalty_value is None else INTENSITY_PLT + f"\n VALUE: {round(penalty_value, 4)}"
        ax.set_title(title)
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.intensityPenalizedPlot.toolbar.update()

    def plotAUCpenalization(self, spectral_axis, spectral_data, baseline, **args):
        interp = args.get('interp', [])
        auc_penalty = args.get('auc_penalty', None)

        min_ref = min([min(spectral_data), min(baseline), min(interp)])
        max_ref = max([max(spectral_data), max(baseline), max(interp)])

        spectra = (spectral_data - min_ref) / (max_ref - min_ref)
        baseline = (baseline - min_ref) / (max_ref - min_ref)
        interp = (interp - min_ref) / (max_ref - min_ref)

        ax = self.aucPenalizationPlot.canvas.axes
        ax.clear()

        ax.plot(spectral_axis, spectra, color='tab:blue', label="Spectra")
        ax.fill_between(spectral_axis, spectra, where=(spectra > 0), alpha=0.3, color='tab:blue')
        ax.plot(spectral_axis, baseline, color='tab:orange', label="Baseline")
        ax.fill_between(spectral_axis, baseline, where=(baseline > 0), alpha=0.3, color='tab:orange')
        ax.plot(spectral_axis, interp, color='red', label="Interpolation")
        ax.fill_between(spectral_axis, interp, where=(interp > 0), alpha=0.3, color='tab:red')
        ax.set_ylabel("Normalized Intensity")
        ax.set_xlabel("Raman shift (cm-1)")
        title = UNDERFITTING_PLT if auc_penalty is None else UNDERFITTING_PLT + f"\n VALUE: {round(auc_penalty, 4)}"
        ax.set_title(title)
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.aucPenalizationPlot.toolbar.update()

    def plotSinglePeakDipPenalization(self, spectral_axis, spectral_data_norm, baseline_norm, **args):
        peaks, dips = args.get("peaks", None), args.get("dips", None)
        peaks_penalized, dips_penalized = args.get("peak_penalized", None), args.get("dip_penalized", None)

        peak_value, dip_value = args.get("peak_penalization", 0), args.get("dip_penalization", 0)
        peak_points = args.get("peak_points", [])

        dip_upper_points, dip_lower_points = args.get("dip_upper_points", []), args.get("dip_lower_points", [])
        ax = self.peaksDipsPenalizedPlot.canvas.axes
        ax.clear()
        ax.plot(spectral_axis, spectral_data_norm, color='tab:blue', alpha=0.4)
        ax.plot(spectral_axis, baseline_norm, color='tab:orange')
        ax.scatter(spectral_axis[peaks], spectral_data_norm[peaks], color='tab:green', marker='x', s=100)
        ax.scatter(spectral_axis[dips], spectral_data_norm[dips], color='blue', marker='x', s=100)
        ax.scatter(spectral_axis[peaks_penalized], spectral_data_norm[peaks_penalized], color='red', marker='x', s=100)
        ax.scatter(spectral_axis[dips_penalized], spectral_data_norm[dips_penalized], color='red', marker='x', s=100)
        if len(dip_upper_points) > 0:
            ax.scatter(spectral_axis[dips], dip_upper_points, color='tab:blue', marker='^', alpha=0.4)
        if len(dip_lower_points) > 0:
            ax.scatter(spectral_axis[dips], dip_lower_points, color='tab:blue', marker='v', alpha=0.4)
        if len(peak_points) > 0:
            ax.scatter(spectral_axis[peaks], peak_points, color='tab:green', marker='o', alpha=0.4)
        ax.set_ylabel("Normalized Intensity")
        ax.set_xlabel("Raman shift (cm-1)")
        title = PEAKS_DIPS_PLT if peak_value is None and dip_value is None else PEAKS_DIPS_PLT + f"\n Peaks Value: {round(peak_value,4)}, Dips Value: {round(dip_value,4)}"
        ax.set_title(title)

        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.peaksDipsPenalizedPlot.toolbar.update()




    def addBaselines(self, baselines):
        self.baselineComboBox.addItems(["BubbleFill"])
        self.baselineComboBox.addItems([baseline[0] for baseline in baselines if baseline[0] != "BubbleFill"])

    def removeHyperparameterWidgets(self):
        if len(self.hyperparametersWidgetFileTab) > 0:
            for widget in self.hyperparametersWidgetFileTab:
                self.baselineChoiceLayout.removeWidget(widget[1])
                widget[1].hide()
            self.hyperparametersWidgetFileTab = []

    def addHyperparameterWidget(self, param_name, placeholder):
        widget = EmitQLineEdit()
        widget.setPlaceholderText(placeholder)
        widget.setFixedHeight(25)
        widget.setFixedWidth(250)
        self.baselineChoiceLayout.insertWidget(self.baselineChoiceLayout.count() - 2, widget)
        self.hyperparametersWidgetFileTab.append((param_name, widget))


    def plotLoadedSpectra(self, spectral_axis, spectral_data):
        ax = self.spectrumPlot.canvas.axes
        ax.clear()
        ax.plot(spectral_axis, spectral_data, label='Raw Spectra')
        ax.set_xlabel("Raman shift (cm-1)")
        ax.set_ylabel("Intensity")
        ax.grid(True)
        ax.legend()
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.spectrumPlot.toolbar.update()


    def _setupUI_ISScoreAnalysisTab(self):
        self.intensityPenalizedPlot = PlotWidget(title="Intensity Penalized")
        self.peaksDipsPenalizedPlot = PlotWidget(title="Peaks and Dips Penalized")
        self.aucPenalizationPlot = PlotWidget(title="AUC Penalization")

        upperLayout = QHBoxLayout()
        upperLayout.addWidget(self.intensityPenalizedPlot)
        upperLayout.addWidget(self.peaksDipsPenalizedPlot)
        upperLayout.addWidget(self.aucPenalizationPlot)

        self.peaksRegionPenalizedPlot = PlotWidget(title="Peak Region Penalization")
        self.dipsRegionPenalizedPlot = PlotWidget(title="Dip Region Penalization")

        downLayout = QHBoxLayout()
        downLayout.addWidget(self.peaksRegionPenalizedPlot)
        downLayout.addWidget(self.dipsRegionPenalizedPlot)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(upperLayout)
        mainLayout.addLayout(downLayout)

        widget = QWidget()
        widget.setLayout(mainLayout)

        return widget



    def createSlider(self):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0,1000)
        slider.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        slider.setMaximumHeight(30)
        slider.hide()
        return slider

    def _setupMenuBar(self):
        self.menuBar = QMenuBar()
        self.fileMenu = self.menuBar.addMenu("File")
        self.loadFolderAction = self.fileMenu.addAction("Load Folder")
        self.setMenuBar(self.menuBar)