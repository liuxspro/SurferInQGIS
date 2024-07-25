from enum import Enum
from pathlib import Path

from win32com import client


class SrfGridAlgorithm(Enum):
    srfInverseDistance = 1
    srfKriging = 2
    srfMinCurvature = 3
    srfShepards = 4
    srfNaturalNeighbor = 5
    srfNearestNeighbor = 6
    srfRegression = 7
    srfRadialBasis = 8
    srfTriangulation = 9
    srfMovingAverage = 10
    srfDataMetrics = 11
    srfLocalPolynomial = 12


class Surfer:
    def __init__(self):
        self.app = None
        self.Version = None
        self.dispatch()

    def dispatch(self):
        # win32com.gen_py.54C3F9A2-980B-1068-83F9-0000C02A351Cx0x1x12.IApplication5
        try:
            self.app = client.gencache.EnsureDispatch("Surfer.Application")
            self.Version = self.app.Version
        except AttributeError as e:
            import os
            import re
            import sys
            import shutil

            # 如果创建 COM 对象时发生异常，打印错误消息
            print("无法绑定 COM 对象:", str(e))
            # 清除缓存并重试
            # see: https://stackoverflow.com/questions/33267002/
            # why-am-i-suddenly-getting-a-no-attribute-clsidtopackagemap-error-with-win32com
            # by @pelelter
            MODULE_LIST = [m.__name__ for m in sys.modules.values()]
            for module in MODULE_LIST:
                if re.match(r"win32com\.gen_py\..+", module):
                    del sys.modules[module]
            gen_py_path = client.gencache.GetGeneratePath()
            if os.path.exists(gen_py_path):
                print("尝试清除缓存")
                shutil.rmtree(gen_py_path)
            self.app = client.gencache.EnsureDispatch("Surfer.Application")
            self.Version = self.app.Version

    def grid(
        self,
        data_path: Path,
        algorithm: SrfGridAlgorithm,
        NumRows,  # number of nodes in the X direction
        NumCols,  # number of nodes in the Y direction
        app_visible: bool = False,
    ):
        plot = self.app.Documents.Add(1)
        self.app.Visible = app_visible
        datafile = str(data_path)
        grd_file = str(data_path.parent.joinpath("grid_data.grd"))
        # https://surferhelp.goldensoftware.com/auto_ah/link_application_GridData6.htm
        is_success_grid = self.app.GridData6(
            DataFile=datafile,
            Algorithm=algorithm,
            NumRows=NumRows,
            NumCols=NumCols,
            ShowReport=False,
            OutGrid=grd_file,
            # TODO set xMin xMax yMin yMax
        )
        if is_success_grid:
            # https://surferhelp.goldensoftware.com/autoobjects/link_mapframe.htm
            map_frame = plot.Shapes.AddContourMap(GridFileName=grd_file)
            map_frame.SetLimitsToData()
            map_frame.Overlays(1)

    def quit(self):
        self.app.Quit()
