import shutil
import tempfile
from pathlib import Path
from uuid import uuid1

import pandas as pd
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.PyQt.QtWidgets import QHeaderView, QTableWidgetItem
from qgis.core import (
    QgsFieldProxyModel,
    QgsMapLayerProxyModel,
    QgsProject,
    QgsRasterFileWriter,
    QgsRasterLayer,
    QgsRasterPipe,
)

from .pySurfer import Surfer
from .ui.Grid import Ui_Form

GridAlgorithm = {
    "Inverse Distance to a Power": 1,
    "Kriging": 2,
    "Minimum Curvature": 3,
    "Modified Shepard's Method": 4,
    "Natural Neighbor": 5,
    "Nearest Neighbor": 6,
    "Polynomial Regression": 7,
    "Radial Basis Function": 8,
    "Triangulation with Linear Interpolation": 9,
    "Moving Average": 10,
    "Data Metrics": 11,
    "Local Polynomial": 12,
}
temp_dir = tempfile.gettempdir()
project_dir = Path(temp_dir).joinpath(uuid1().hex)
project_dir.mkdir()


def add_raster_layer(uri, name, crs):
    # load grd file
    raster_layer = QgsRasterLayer(uri, name)
    raster_layer.setCrs(crs)

    data_provider = raster_layer.dataProvider()
    # TODO save to temp folder
    tif_path = str(project_dir.joinpath("grid.tif"))
    writer = QgsRasterFileWriter(tif_path)
    pipe = QgsRasterPipe()
    pipe.set(data_provider.clone())
    writer.writeRaster(
        pipe,
        raster_layer.width(),
        raster_layer.height(),
        raster_layer.extent(),
        raster_layer.crs(),
    )
    tif_raster_layer = QgsRasterLayer(tif_path, name)
    tif_raster_layer.setCrs(crs)
    QgsProject.instance().addMapLayer(tif_raster_layer)


class CheckSurfer(QThread):
    check_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        app = Surfer()
        self.check_finished.emit(app.Version)


def get_extent(data):
    return {
        "xmin": min(data["x"]),
        "xmax": max(data["x"]),
        "ymin": min(data["y"]),
        "ymax": max(data["y"]),
    }


class GridDialog(QtWidgets.QDialog, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.app = None
        self.grid_data = None
        self.check_surfer = None
        self.project_dir = project_dir
        # C:\Users\liuxs\AppData\Local\Temp\processing_ESHtVM\ef7ab229b96c4ee1abb8a4c3f20561f5
        # TODO 清理临时文件
        self.initUI()

    def initUI(self):
        # 在 Surfer 成功连接前禁用所有组件
        self.groupBox.setEnabled(False)
        self.groupBox_2.setEnabled(False)
        self.groupBox_3.setEnabled(False)
        self.pushButton_2.setEnabled(False)

        self.check_surfer_version()
        # 检查数据，放在另一个函数中吧
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.mMapLayerComboBox_2.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.mMapLayerComboBox.layerChanged.connect(self.set_layer)
        # self.pushButton.clicked.connect(self.preview_data)
        self.pushButton_2.clicked.connect(self.make_grid)
        self.set_layer()
        # set check false
        self.checkBox.setChecked(False)
        self.checkBox.stateChanged.connect(self.toggle_surfer_visible)
        # self.groupBox_3.setEnabled(False)
        # 字段变化时自动加载
        self.preview_data()
        self.mFieldComboBox.fieldChanged.connect(self.preview_data)
        # set grid method
        self.comboBox.addItems(GridAlgorithm.keys())

    def set_layer(self):
        pl = self.mMapLayerComboBox.currentLayer()
        self.mFieldComboBox.setLayer(pl)
        self.mFieldComboBox.setFilters(QgsFieldProxyModel.Double)
        fd = self.mFieldComboBox.currentField()

        if fd == "":
            # 没有数据的时候禁用 grid 按钮
            self.pushButton_2.setEnabled(False)
            return
        self.pushButton_2.setEnabled(True)
        # 优先选择 Z 高程 ELVE 等常见的表示高程的属性
        h_values = ["z", "Z", "ELVE"]
        for h in h_values:
            if h in self.mFieldComboBox.fields().names():
                self.mFieldComboBox.setField(h)

    def init_surfer(self):
        self.app = Surfer()

    def preview_data(self):
        pl = self.mMapLayerComboBox.currentLayer()
        fd = self.mFieldComboBox.currentField()
        if not pl or fd == "":
            # 没有数据的时候禁用 grid 按钮
            self.pushButton_2.setEnabled(False)
            return
        features = list(pl.getFeatures())
        self.grid_data = {
            "x": [f.geometry().asPoint().x() for f in features],
            "y": [f.geometry().asPoint().y() for f in features],
            "z": [f.attribute(fd) for f in features],
        }
        self.fill_data_table(self.grid_data)
        df = pd.DataFrame(self.grid_data)
        df.to_csv(self.project_dir.joinpath("grid_data.csv"), index=False)
        self.pushButton_2.setEnabled(True)

    def set_surfer(self, version):
        if version != "":
            self.label_surfer_connect_status.setText(f"Connected to Surfer {version}")
            self.init_surfer()
            self.groupBox.setEnabled(True)
            self.groupBox_2.setEnabled(True)
            self.groupBox_3.setEnabled(True)
        else:
            self.label_surfer_connect_status.setText("Filed to connect Surfer")

    def check_surfer_version(self):
        self.label_surfer_connect_status.setText("Connecting")

        self.check_surfer = CheckSurfer()
        self.check_surfer.check_finished.connect(self.set_surfer)
        self.check_surfer.start()

    def toggle_surfer_visible(self):
        # 是否显示 Surfer App 窗口
        if self.checkBox.isChecked():
            self.app.Visible = False
        else:
            self.app.Visible = True

    def fill_data_table(self, data):
        self.data_tableWidget.clear()
        row_count = len(data.get("x"))
        self.data_tableWidget.setRowCount(row_count)
        self.data_tableWidget.setColumnCount(3)
        self.data_tableWidget.setHorizontalHeaderLabels(
            [x.upper() for x in data.keys()]
        )
        self.data_tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        for row in range(row_count):
            x = data["x"][row]
            item_x = QTableWidgetItem(str(x))
            self.data_tableWidget.setItem(row, 0, item_x)
            y = data["y"][row]
            item_y = QTableWidgetItem(str(y))
            self.data_tableWidget.setItem(row, 1, item_y)
            z = data["z"][row]
            item_z = QTableWidgetItem(str(z))
            self.data_tableWidget.setItem(row, 2, item_z)
        self.data_tableWidget.resizeRowsToContents()

    def make_grid(self):
        # TODO 数据不满足插值算法要求的时候会报错
        grid_method_selected = GridAlgorithm[self.comboBox.currentText()]
        self.app.grid(
            self.project_dir.joinpath("grid_data.csv"),
            algorithm=grid_method_selected,
            extend=get_extent(self.grid_data),
            app_visible=self.checkBox.isChecked(),
        )
        grd_path = self.project_dir.joinpath("grid_data.grd")
        # make a copy file
        grd_path_tmp = self.project_dir.joinpath("grid_data_tmp.grd")
        shutil.copyfile(grd_path, grd_path_tmp)
        # self.app.quit()
        add_raster_layer(
            str(grd_path_tmp), "grid_data", self.mMapLayerComboBox.currentLayer().crs()
        )

    # def closeEvent(self, event):
    #     # 在对话框关闭时触发的事件
    #     print("close")
    #     self.app.quit()
    #     event.accept()  # 接受关闭事件，关闭对话框
