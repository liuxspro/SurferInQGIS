from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .grid_dialog import GridDialog
from .utils import PLUGIN_DIR


class Surfer:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.toolbar = self.iface.addToolBar("Surfer Toolbar")
        self.initGui()

    def initGui(self):
        self.action = QAction(
            QIcon(str(PLUGIN_DIR.joinpath("images/icon.png"))),
            "Surfer",
        )
        self.action.triggered.connect(self.openGridDialog)
        self.toolbar.addAction(self.action)

    @staticmethod
    def openGridDialog():
        dlg = GridDialog()
        dlg.show()
        dlg.exec_()

    def unload(self):
        """Unload from the QGIS interface"""
        mw = self.iface.mainWindow()
        mw.removeToolBar(self.toolbar)
        self.toolbar.deleteLater()
