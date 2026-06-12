from abc import abstractmethod
from ..GcPoint import GcPoint
from .GcBase import GcBase
from ..GcDirection import GcDirection
from qgis.core import QgsCurve
from typing import TypeVar, TYPE_CHECKING
from ...GcConfig import gc_config
from qgis.core import QgsGeometry, QgsAbstractGeometry
T = TypeVar('T', bound='GcCurve')

if TYPE_CHECKING:
    from ..GcCompoundCurve import GcCompoundCurve


class GcCurve(GcBase):
    """Abstrcat base class for all line-like geometries that have a direction"""

    start: GcPoint
    end: GcPoint

    @property
    @abstractmethod
    def lengthXY(self) -> float:
        """The 2D Length of this curve in XY direction"""
        pass
    
    @property
    @abstractmethod
    def lengthXYZ(self) -> float:
        """The 3D Length of this curve in XYZ direction"""
        pass

    @abstractmethod
    def invertSelf(self):
        """Inverts the current line direction in place"""
        pass

    @abstractmethod
    def interpolatePointFractionXY(self, fraction: float) -> GcPoint:
        """Interpolates a point on this Curve with a given fraction in 2D between 0 and 1. Values outside this bound will be clamped"""
        pass

    @abstractmethod
    def interpolatePointFractionXYZ(self, fraction: float) -> GcPoint:
        """Interpolates a point on this Curve with a given fraction in 3D between 0 and 1. Values outside this bound will be clamped"""
        pass

    @abstractmethod
    def sliceFractionXY(self, start: float, end: float) -> T:
        """Returns a part of this geometry form the start fraction to the end fraction, with the distance calculated in XY space, if start > end an inverted curve is returned"""
        pass

    @abstractmethod
    def sliceDistanceXY(self, start: float, end: float) -> T:
        """Returns a part of this geometry form the start distance to the end distance, with the distance calculated in XY space, if start > end an inverted curve is returned"""
        pass

    @abstractmethod
    def sliceFractionXYZ(self, start: float, end: float) -> T:
        """Returns a part of this geometry form the start fraction to the end fraction, with the distance calculated in XYZ space, if start > end an inverted curve is returned"""
        pass

    @abstractmethod
    def sliceDistanceXYZ(self, start: float, end: float) -> T:
        """Returns a part of this geometry form the start distance to the end distance, with the distance calculated in XYZ space, if start > end an inverted curve is returned"""
        pass


    @abstractmethod
    def invert(self) -> "GcCurve":
        """Returns a Copy of curve, Pointing in the Opposite Direction"""
        pass

    @abstractmethod
    def toQgs(self) -> QgsCurve:
        """Returns a Qgs Abstract geometry of this type"""
        pass

    def interpolatePointDistanceXY(self, distance: float) -> GcPoint:
        """Interpolates a point on this Curve with a given distance in 2D between 0 and lengthXY. Values outside this bound will be clamped"""
        fraction = distance/self.lengthXY
        return self.interpolatePointFractionXY(fraction)

    def interpolatePointDistanceXYZ(self, distance: float) -> GcPoint:
        """Interpolates a point on this Curve with a given distance in 3D between 0 and lengthXYZ. Values outside this bound will be clamped"""
        fraction = distance/self.lengthXYZ
        return self.interpolatePointFractionXYZ(fraction)
    
    def interpolateMissingZSelf(self, nodata_value: float = gc_config.default_z_value):
        #todo
        pass
    
    def lineLocatePoint(self, point: GcPoint) -> float:
        """Returns the distance along this line to the given point"""
        return self.toQgsGeometry().lineLocatePoint(point.toQgsGeometry())

    def recalculateMXY(self: T, start = 0.0) -> T:
        c = self.clone()
        c.recalculateMXY(start)
        return c

    def recalculateMXYSelf(self, start = 0.0):
        self.start.m = start
        self.end.m = start + self.lengthXY

    def recalculateMXYZ(self: T, start = 0.0) -> T:
        c = self.clone()
        c.recalculateMXYZ(start)
        return c

    def recalculateMXYZSelf(self, start = 0.0):
        self.start.m = start
        self.end.m = start + self.lengthXYZ

    def debugString(self) -> str:
        return "Startpoint: " + self.start.debugString() + "\n Endpoint: " + self.end.debugString()
    
    def offsetCurveXY(self, distance: float, segments: int = 8, join_style = QgsGeometry.JoinStyleRound, miter_limit: float = 0.2):
        """Returns a clone of this curve with its geometry offset by the qgis geometry engine. 
        Because qgis is used, attributes on points and geometry parts are removed, as well as curves in the geometry.

        distance: the distance the curve is offset by
        segments: the number of segments used to aproximate a curve
        join_style: must be a qgis join style enum from QgsGeometry. E.g: QgsGeometry.JoinStyleRound
        miter_limit: Miter Limit

        """
        geom = self.toQgsGeometry()

        offset_geom = geom.offsetCurve(
            distance,
            segments,
            join_style, 
            miter_limit
        )

        return self.fromQgs(offset_geom.get(), self.attributes)