from pathlib import Path

import pandas as pd
from qgis import processing
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.core import (
    QgsFieldProxyModel,
    QgsMapLayerProxyModel,
    QgsProject,
    QgsRasterLayer,
    QgsProcessingUtils,
)

from .preview_data import PreviewData
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

SurferProcessing = QgsProcessingUtils()
qgis_temp_dir = SurferProcessing.tempFolder(context=None)
project_temp_dir = Path(SurferProcessing.generateTempFilename("SurferTempProject"))
project_temp_dir.mkdir()


def add_raster_layer(uri, name, crs):
    # load surfer grd file
    raster_layer = QgsRasterLayer(uri, name)
    raster_layer.setCrs(crs)

    # QgsProject.instance().addMapLayer() 使用此方法添加临时目录中的栅格图层不能识别为临时图层
    # 使用 processing 算法“按范围裁剪栅格”来生成临时图层

    # Can also try runAndLoadResults
    # `processing.runAndLoadResults("native:buffer", {parameters:values})`
    # https://docs.qgis.org/3.34/en/docs/user_manual/processing/console.html
    parms = {
        "INPUT": raster_layer,
        "CRS": crs,
        "PROJWIN": raster_layer.extent(),
        "OVERCRS": True,
        "OUTPUT": "TEMPORARY_OUTPUT",
    }
    result = processing.run("gdal:cliprasterbyextent", parms)
    output_layer = QgsRasterLayer(result["OUTPUT"], name, "gdal")
    if output_layer.isValid():
        QgsProject.instance().addMapLayer(output_layer)
    else:
        print("Failed to add raster layer")


class CheckSurfer(QThread):
    check_finished = pyqtSignal(str, name="check_finished")

    def __init__(self):
        super().__init__(parent=None)

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
        self.project_dir = project_temp_dir
        self.initUI()

    def initUI(self):
        # 在 Surfer 成功连接前禁用所有组件
        self.groupBox.setEnabled(False)
        self.groupBox_4.setEnabled(False)
        self.groupBox_3.setEnabled(False)
        self.pushButton_2.setEnabled(False)

        self.check_surfer_version()
        # 检查数据
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
        # self.preview_data()
        # self.mFieldComboBox.fieldChanged.connect(self.preview_data)
        # set grid method
        self.comboBox.addItems(GridAlgorithm.keys())
        #
        self.pushButton.clicked.connect(self.showDataPreview)

    def showDataPreview(self):
        self.get_grid_data()
        dlg = PreviewData(data=self.grid_data)
        # dlg.show()
        dlg.exec_()

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

    def get_grid_data(self):
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

    def set_surfer(self, version):
        if version != "":
            self.label_surfer_connect_status.setText(f"Connected to Surfer {version}")
            self.init_surfer()
            self.groupBox.setEnabled(True)
            self.groupBox_4.setEnabled(True)
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

    def make_grid(self):
        self.get_grid_data()
        if self.grid_data is None:
            print("no data")
            return
        df = pd.DataFrame(self.grid_data)
        df.to_csv(self.project_dir.joinpath("grid_data.csv"), index=False)
        # TODO 数据不满足插值算法要求的时候会报错
        grid_method_selected = GridAlgorithm[self.comboBox.currentText()]
        self.app.grid(
            self.project_dir.joinpath("grid_data.csv"),
            algorithm=grid_method_selected,
            app_visible=self.checkBox.isChecked(),
        )
        grd_path = self.project_dir.joinpath("grid_data.grd")
        add_raster_layer(
            str(grd_path), "grid_data", self.mMapLayerComboBox.currentLayer().crs()
        )

    # def closeEvent(self, event):
    #     # 在对话框关闭时触发的事件
    #     print("close")
    #     self.app.quit()
    #     event.accept()  # 接受关闭事件，关闭对话框
