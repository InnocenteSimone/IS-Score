import sys
import qtmodern.styles

from PyQt5.QtWidgets import QApplication
from IS_Score_GUI.views.main_view import IS_Score_GUI
from IS_Score_GUI.models.model import Model
from IS_Score_GUI.controller import Controller

def runGUI():

    app = QApplication(sys.argv)

    view = IS_Score_GUI()
    model = Model()
    controller = Controller(model, view)

    qtmodern.styles.light(app)
    view.showMaximized()
    sys.exit(app.exec_())
