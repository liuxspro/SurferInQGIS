from .plugin import Surfer


def classFactory(iface):
    """QGIS Plugin"""
    return Surfer(iface)
