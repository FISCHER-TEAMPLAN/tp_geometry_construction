from qgis.core import *
from typing import *

from qgis.core import QgsAbstractGeometry
from .abstract.GcBase import GcBase
import math
import numpy as np
from typing import Union, TYPE_CHECKING
from ..GcConfig import gc_config

if TYPE_CHECKING:
    from .GcDirection import GcDirection

class GcPoint(GcBase):
    """Represents a Single Point. The basic building block for all other Geometry"""

    qgs_layer_signature = "PointZ"

    def __init__(self, x: float, y: float, z = gc_config.default_z_value, m = gc_config.default_m_value, attributes = {}) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.m = m
        self.replaceAttributesSelf(attributes)

    def replaceWith(self, point: "GcPoint"):
        """Replaces all poperties of this point with the properties of the given point"""
        self.x = point.x
        self.y = point.y
        self.z = point.z
        self.m = point.m
        self.replaceAttributesSelf(point.attributes)

    @property
    def points(self) -> list["GcPoint"]:
        return [self]
    
    @property
    def children(self) -> list:
        """Returns an empty list, as points are always considerd leaves"""
        return []

    def clone(self) -> "GcPoint":
        return GcPoint(self.x, self.y, self.z, self.m, self.attributes)

    def translateXYZ(self, direction: "GcDirection", distance: float) -> "GcPoint":
        """retuns a moved copy of the point about the given direction and distance. M dimension stays unmodifyed"""
        return GcPoint(
            self.x + direction.x * distance,
            self.y + direction.y * distance,
            self.z + direction.z * distance,
            self.m,
            self.attributes
        )
    
    def rotateXY(self, origin: "GcPoint", angle: float) -> "GcPoint":
        """Returns a new Point Rotated Around the center with the given angle in radiants"""
        g = QgsGeometry(self.toQgsPoint())
        g.rotate(math.degrees(angle),origin.toQgsPointXY())
        gc = GcPoint.fromQgsPoint(g.get(), self.attributes)
        gc.z = self.z
        gc.m = self.m
        return gc
    
    def translateSelfXYZ(self, direction: "GcDirection", distance: float):
        """moves itself along the given direction and distance. M dimension stays unmodifyed"""
        self.x += direction.x * distance
        self.y += direction.y * distance
        self.z += direction.z * distance
        
    
    def rotateSelfXY(self, origin: "GcPoint", angle: float):
        """Returns a new Point Rotated Around the center with the given angle in radiants"""
        g = self.toQgsGeometry()
        g.rotate(math.degrees(angle),origin.toQgsPointXY())
        qp = g.get()
        self.x = qp.x()
        self.y = qp.y()

    @staticmethod
    def fromQgs(point: Union[QgsPoint, QgsPointXY], attributes = {}):
        if isinstance(point, QgsPoint):
            return GcPoint.fromQgsPoint(point, attributes)
        
        if isinstance(point, QgsPointXY):
            return GcPoint.fromQgsPointXY(point, attributes)

        raise ValueError

    
    def toQgs(self) -> QgsAbstractGeometry:
        return self.toQgsPoint()

    @staticmethod
    def fromQgsPoint(point: QgsPoint, attributes = {}) -> "GcPoint":
        return GcPoint(point.x(), point.y(), point.z(), point.m(), attributes)
    
    @staticmethod
    def fromQgsPointXY(point: QgsPointXY, attributes = {}) -> "GcPoint":
        return GcPoint(point.x(), point.y(), attributes=attributes)
    
    @staticmethod
    def fromArrayLike(list: Iterable, attributes = {}) -> "GcPoint":
        p = [0,0,0,0]
        i = 0
        for e in list:
            p[i] = e
            i+=1
        
        return GcPoint(p[0],p[1],p[2],p[3], attributes)
    
    @staticmethod
    def fromMZXY(point: "GcPoint", attributes = {}) -> "GcPoint":
        return GcPoint(point.z, point.m, point.y, point.x, attributes)
    
    @staticmethod
    def listFromQgisAbstractGeometry(geom: QgsAbstractGeometry, attributes = {}) -> list["GcPoint"]:
        list = []
        it = geom.vertices()
        while it.hasNext():
            list.append(GcPoint.fromQgs(it.next(), attributes))

        return list
    
    
    @property
    def xy(self) -> "GcPoint":
        """A Point with Z and M dropped"""
        return GcPoint(self.x, self.y, attributes=self.attributes)
    
    @property
    def xyz(self) -> "GcPoint":
        """A Point with M dropped"""
        return GcPoint(self.x, self.y, self.z, attributes=self.attributes)
    
    @property
    def mz(self) -> "GcPoint":
        """Point with this points MZ as XY"""
        return GcPoint(self.m, self.z, attributes=self.attributes)
    
    def toMZXY(self) -> "GcPoint":
        return GcPoint(self.m, self.z, self.x, self.y, attributes = self.attributes)
    
    def toQgsPoint(self) -> QgsPoint:
        return QgsPoint(self.x,self.y,self.z,self.m)
    
    def toQgsPointXY(self) -> QgsPointXY:
        return QgsPointXY(self.x,self.y)
    
    def distanceXY(self, point: "GcPoint") -> float:
        return self.toQgsPoint().distance(point.x, point.y)
    
    def distanceXYZ(self, point: "GcPoint") -> float:
        return self.toQgsPoint().distance3D(point.x, point.y, point.z)

    def toArrayXYZM(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z, self.m])

    def toArrayXYZ(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def toArrayXY(self) -> np.ndarray:
        return np.array([self.x, self.y])
    
    def spacialIdXY(self, precision = 3) -> str:
        """Generates a string based on the XY coordinates with the given Decimal precision.
        Can be used for Spacial Indexing"""
        return str(round(self.x, 3)) + "_" + str(round(self.y,3))
    
    def spacialIdXYZ(self, precision = 3) -> str:
        """Generates a string based on the XYZ coordinates with the given Decimal precision.
        Can be used for Spacial Indexing"""
        return str(round(self.x, 3)) + "_" + str(round(self.y,3)) + "_" + str(round(self.z,3))
    
    def equalsXY(self, target, precision = 0.0001):
        """Returns true if the target lies withing a Bounding Box around self with precision*2 with and length"""
        return (abs(target.x - self.x) < precision) and (abs(target.y - self.y) < precision)

    def equalsXYZ(self, target, precision = 0.0001):
        """Returns true if the target lies withing a Bounding Box around self with precision*2 with, length and height"""
        return (abs(target.x - self.x) < precision) and (abs(target.y - self.y) < precision) and (abs(target.z - self.z) < precision)
    
    def debugString(self) -> str:
        return "        x: " + str(self.x) + "\n      y: " + str(self.y) + "\n      z: " + str(self.z) + "\n      m: " + str(self.m)
