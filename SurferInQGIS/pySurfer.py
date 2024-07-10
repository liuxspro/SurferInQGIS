from enum import Enum
from pathlib import Path

import win32com.client


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
        try:
            # 清除 gencache
            # gen_py_path = win32com.__gen_path__
            # if os.path.exists(gen_py_path):
            #     shutil.rmtree(gen_py_path)
            self.app = win32com.client.gencache.EnsureDispatch("Surfer.Application")
            self.Version = self.app.Version

        except Exception as e:
            # 如果创建 COM 对象时发生异常，打印错误消息
            print("无法绑定 COM 对象:", str(e))

    def grid(
        self,
        data_path: Path,
        algorithm: SrfGridAlgorithm,
        extend,
        app_visible: bool = False,
    ):
        plot = self.app.Documents.Add(1)
        self.app.Visible = app_visible
        datafile = str(data_path)
        grd_file = str(data_path.parent.joinpath("grid_data.grd"))
        self.app.GridData(
            DataFile=datafile,
            Algorithm=algorithm,
            NumRows=150,
            NumCols=150,
            ShowReport=False,
            OutGrid=grd_file,
        )
        map_frame = plot.Shapes.AddContourMap(GridFileName=grd_file)
        map_frame.SetLimits(
            xMin=extend["xmin"],
            xMax=extend["xmax"],
            yMin=extend["ymin"],
            yMax=extend["ymax"],
        )
        map_frame.xLength = 6
        map_frame.yLength = 4
        map_frame.Overlays(1)

    def quit(self):
        self.app.Quit()
