from qgis.PyQt.QtWidgets import QDialog, QHeaderView, QTableWidgetItem

from .ui.Preview import Ui_Form


class PreviewData(QDialog, Ui_Form):
    def __init__(self, data=None):
        super().__init__()
        self.setupUi(self)
        self.data = data
        self.initUI()

    def initUI(self):
        self.setWindowTitle("数据预览")
        if self.data:
            self.fill_data_table()

    def fill_data_table(self):
        """
        data = {"x":[...],"y":[...],"z":[...]
        """
        self.data_tableWidget.clear()
        row_count = len(self.data.get("x"))
        self.data_tableWidget.setRowCount(row_count)
        self.data_tableWidget.setColumnCount(3)
        self.data_tableWidget.setHorizontalHeaderLabels(
            [x.upper() for x in self.data.keys()]
        )
        self.data_tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        for row in range(row_count):
            x = self.data["x"][row]
            item_x = QTableWidgetItem(str(x))
            self.data_tableWidget.setItem(row, 0, item_x)
            y = self.data["y"][row]
            item_y = QTableWidgetItem(str(y))
            self.data_tableWidget.setItem(row, 1, item_y)
            z = self.data["z"][row]
            item_z = QTableWidgetItem(str(z))
            self.data_tableWidget.setItem(row, 2, item_z)
        self.data_tableWidget.resizeRowsToContents()
