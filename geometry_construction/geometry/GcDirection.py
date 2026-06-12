import numpy as np
from typing import TYPE_CHECKING
from qgis.core import QgsVector, QgsGeometryUtils
from .GcPoint import GcPoint
import math

if TYPE_CHECKING: 
    from .GcPoint import GcPoint

class GcDirection:
    """A threedimensional vector"""
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def invert(self) -> "GcDirection":
        return GcDirection(self.x * -1, self.y * -1, self.z * -1)

    def invertSelf(self):
        self.x = self.x * -1
        self.y = self.y * -1
        self.z = self.z * -1

    def normalize(self) -> "GcDirection":
        """Returns a normalized version of this direction"""
        d = np.array([self.x,self.y,self.z])
        n = d/np.linalg.norm(d)
        return GcDirection(n[0], n[1], n[2])
    
    def normalXY(self) -> "GcDirection":
        """Returns the Normal of this vector in 2D"""
        return GcDirection(-self.y, self.x)
    
    def toQgisVector(self) -> QgsVector:
        return QgsVector(self.x,self.y)

    def angleToXY(self, target: "GcDirection") -> float:
        """Returns the angle between two directions in radiants"""
        return self.toQgisVector().angle(target.toQgisVector()) 

    def smallestAngleToXY(self, target: "GcDirection") -> float:
        """Returns the angle between two directions in radiants. Always the smallest angle is returned"""
        angle = self.toQgisVector().angle(target.toQgisVector()) 
        if angle > math.pi:
            angle = math.pi*2 - angle

        return angle

    def add(self, direction: "GcDirection") -> "GcDirection":
        return GcDirection(self.x + direction.x, self.y + direction.y, self.z + direction.z)

    def angleXY(self) -> float:
        return self.toQgisVector().angle()
    
    def toGcPoint(self) -> GcPoint:
        """Returns the XYZ coordinates of this Vector as a point"""
        return GcPoint(self.x, self.y, self.z)
    
    @property
    def lengthXY(self) -> float:
        """The 2D Length of this Vecor in XY direction"""
        return GcPoint(0,0,0).distanceXY(self.toGcPoint())
    
    @property
    def lengthXYZ(self) -> float:
        """The 3D Length of this Vecor in XY direction"""
        return GcPoint(0,0,0).distanceXYZ(self.toGcPoint())
    
    @property
    def incline_angle(self) -> float:
        """The Incline in Radiants - positive value for Upward slopes, negative value for downward slopes"""
       
        incline = self.z / self.lengthXY

        angle = abs(math.atan(incline))
        
        if self.z < 0:
            return -angle
        
        return angle


    @staticmethod
    def fromPoints(start: "GcPoint", end: "GcPoint") -> "GcDirection":
        return GcDirection(
            end.x - start.x,
            end.y - start.y,
            end.z - start.z,
        )