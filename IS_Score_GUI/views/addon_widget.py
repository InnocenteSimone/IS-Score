import numpy as np

import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QLabel, QDialog, QProgressBar


class EmitQLineEdit(QLineEdit):
    focusIn = pyqtSignal()
    focusOut = pyqtSignal()

    def __init__(self):
        super().__init__()

    def focusInEvent(self, event):
        self.focusIn.emit()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.focusOut.emit()
        super().focusOutEvent(event)

    #TODO: Remove it
    def toPlainText(self):
        return self.text()


# Chart
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class PlotWidget(QWidget):
    def __init__(self, title="", width=5, height=4):
        super().__init__()

        self.canvas = MplCanvas(self, width=width, height=height, dpi=100)
        if title != "":
            self.canvas.axes.set_title(title)

        self.canvas.figure.tight_layout()

        self.layout = QVBoxLayout()

        self._setupToolBar()

        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

    def _setupToolBar(self):
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setFixedHeight(25)
        self.toolbar.layout().setSpacing(2)
        for action in self.toolbar.actions():
            if action.text() in ["Back", "Forward", "Subplots", "Customize"]:
                self.toolbar.removeAction(action)

# TODO: Remove
class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.size, self.labels = None, None

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def draw(self, sizes, labels):
        self.size, self.labels = sizes, labels

        self.ax.clear()

        sizes = [size for size in self.size if size != 0]
        labels = [label for label, size in zip(self.labels, self.size) if size != 0]

        sizes_log = np.log10(np.array(sizes) + 1)
        sizes_log_normalized = sizes_log / np.sum(sizes_log)

        wedges, texts, autotexts = self.ax.pie(sizes_log_normalized, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})

        # Add the donut effect
        circle = plt.Circle((0, 0), 0.7, color='white')
        self.ax.add_artist(circle)

        # Adding the legend
        self.ax.legend(wedges, self.labels, title="Categories", fontsize=8)

        self.ax.set_aspect('equal')  # Keep the pie circular
        self.canvas.draw()


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setFixedSize(300, 100)

        # Layout and widgets
        layout = QVBoxLayout(self)
        self.label = QLabel("Please wait while the process completes.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

