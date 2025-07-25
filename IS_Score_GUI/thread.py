from PyQt5.QtCore import QThread, pyqtSignal, QRunnable

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, algorithm_function):
        super().__init__()
        self.algorithm_function = algorithm_function

    def run(self):
        self.algorithm_function(self.report_progress)
        self.finished_signal.emit()

    def report_progress(self, value):
        self.progress.emit(value)

class PlotTask(QRunnable):
    def __init__(self, plot_function, *args):
        super().__init__()
        self.plot_function = plot_function
        self.args = args

    def run(self):
        self.plot_function(*self.args)