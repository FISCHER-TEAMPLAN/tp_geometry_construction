from qgis.core import *

class GcPlugin:
    # Constructor
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface

   # Method to initialize the plugins toolbar
    def initGui(self) -> None:
        pass

    def unload(self) -> None:
        pass

def classFactory(iface):
    return GcPlugin(iface)