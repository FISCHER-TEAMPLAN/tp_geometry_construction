from .abstract.GcBase import GcBase
from .abstract.GcCurve import GcCurve
from .GcPoint import GcPoint
from .GcLine import GcLine
from .GcDirection import GcDirection
from qgis.core import QgsCircularString, QgsGeometry
from .GcCircle import GcCircle
import math
from typing import Tuple
from qgis.core import QgsGeometryUtils

from qgis.core import QgsMessageLog, Qgis

class GcArc(GcCurve):
    """A 2D arc segment. The Z coordinate of Points is keept but ignored for most operations"""

    qgs_layer_signature = "CircularStringZ"

    def __init__(self, start: GcPoint, mid: GcPoint, end: GcPoint, attributes = {}) -> None:
        super().__init__()
        self.start = start.clone()
        self.mid = mid.clone()
        self.end = end.clone()
        self.replaceAttributesSelf(attributes)

    def clone(self) -> "GcArc":
        return GcArc(self.start, self.mid, self.end,self.attributes)

    @property
    def points(self) -> list[GcPoint]:
        return [
            self.start,
            self.mid,
            self.end
        ]
    
    @property
    def children(self) -> list[GcPoint]:
        return self.points

    @staticmethod
    def fromPoints(points: list[GcPoint], attributes = {}) -> "GcArc":
        """constructs an arc segment from an array of three points (start point, point on arc, endpoint)"""
        return GcArc(points[0], points[1], points[2], attributes)

    def toQgs(self) -> QgsCircularString:
        return QgsCircularString(self.start.toQgsPoint(), self.mid.toQgsPoint(), self.end.toQgsPoint())
    
    @staticmethod
    def fromQgs(circular_string: QgsCircularString, attributes = {}) -> "GcArc":
        """constructs an arc segment from the given QGIS arc"""
        if not isinstance(circular_string, QgsCircularString) or circular_string.numPoints() < 3:
            raise ValueError
        
        p = circular_string.points()
        
        return GcArc(GcPoint.fromQgs(p[0]), GcPoint.fromQgs(p[1]), GcPoint.fromQgs(p[2]), attributes)

    @property
    def lengthXY(self) -> float:
        """The 2D Length of this curve in XY direction"""
        return self.toQgs().length()
    
    @property
    def angle(self) -> float:
        """Returns the angle that the arc inscribes"""
        return self.lengthXY / self.radius
    
    @property
    def circle(self) -> GcCircle:
        return GcCircle.from3Points(self.start, self.mid, self.end, attributes=self.attributes)
    
    @property
    def center(self) -> GcPoint:
        return self.circle.center
    
    @property
    def radius(self) -> float:
        return self.circle.radius

    @property
    def lengthXYZ(self) -> float:
        """Curves are currently 2D only. they can have Z values, but they are considerd as lines in MZ direction - the z value of the mid Point is ignored"""
        l_xy = self.lengthXY
        l_mz = GcLine(
            GcPoint(0,self.start.z),
            GcPoint(l_xy,self.end.z)
        ).lengthXY
        return l_xy + (l_mz - l_xy)

    def interpolatePointFractionXY(self, fraction: float) -> GcPoint:
        """Interpolates a point on this Curve with a given fraction in 2D between 0 and 1. Values outside this bound will be clamped
        Z and M values will be interpolated Linearly between start and end, the mid value is ignored

        For this Primitve geometry XY and XYZ version of this function are identical
        """

        fraction = max(0, min(fraction, 1))

        p = GcPoint.fromQgsPoint(self.toQgs().interpolatePoint(fraction * self.lengthXY))
        p.m = self.start.m + (self.end.m - self.start.m ) * fraction
        p.z = self.start.z + (self.end.z - self.start.z ) * fraction
        return p

    def interpolatePointFractionXYZ(self, fraction: float) -> GcPoint:
        """Interpolates a point on this Curve with a given fraction in 3D between 0 and 1. Values outside this bound will be clamped
        Z and M values will be interpolated Linearly between start and end, the mid value is ignored

        For this Primitve geometry XY and XYZ version of this function are identical
        """
        return self.interpolatePointFractionXY(fraction)
    
    def invert(self) -> "GcArc":
        return GcArc(self.end, self.mid, self.start, self.attributes)
    
    def invertSelf(self):
        e = self.end 
        self.end  = self.start
        self.start = e

    def translateXYZ(self, direction: GcDirection, distance: float) -> "GcArc":
        """retuns a moved copy of the geometry about the given direction and distance. M dimension stays unmodifyed"""
        return GcArc(
            self.start.translateXYZ(direction, distance),
            self.mid.translateXYZ(direction, distance),
            self.end.translateXYZ(direction, distance),
            self.attributes
        )
    
    def rotateXY(self, origin: "GcPoint", angle: float) -> "GcArc":
        """returns a new object rotated around the center by the angle in radiants"""
        return GcArc(
            self.start.rotateXY(origin, angle),
            self.mid.rotateXY(origin, angle),
            self.end.rotateXY(origin, angle),
            self.attributes
        )

    def recalculateMXYSelf(self, start = 0.0):
        self.start.m = start
        self.mid.m = start + self.lineLocatePoint(self.mid)
        self.end.m = start + self.lengthXY

    def recalculateMXYZSelf(self, start = 0.0):
        partial_length = self.lineLocatePoint(self.mid)/self.lengthXY
        length = self.lengthXYZ
        self.start.m = start
        self.mid.m = start + partial_length * length
        self.end.m = start + length

    def debugString(self) -> str:
        return "Start: " + self.start.debugString() + "\nMid: " + self.mid.debugString() + "\nEnd: " + self.end.debugString()

    @staticmethod
    def fromLineAngleAndRadius(line: GcLine, angle: float, radius: float, invert_side = False):
        start = line.end.clone()
        dir = line.directionXY.normalXY()

        if invert_side:
            angle = -angle
            dir.invertSelf()

        origin = start.translateXYZ(dir, radius)
        mid = start.rotateXY(origin, -angle / 2)
        end = start.rotateXY(origin, -angle)
        return GcArc(start, mid, end)
    
    @staticmethod
    def getArc(circle: GcCircle, start: GcPoint, angle: float) -> "GcArc":
        """Given a start Point on this Circle an an angle in radiants, returns an arc from that Point along the given angle"""
        return GcArc(start, start.rotateXY(circle.center, angle/2), start.rotateXY(circle.center, angle), circle.attributes)

    @staticmethod
    def fromTwoLinesAndRadius(line_start: GcLine, line_end: GcLine, radius: float) -> "GcArc":
        """constructs an arc segment between the two lines. Lines must be given in the correct order"""
        ip = line_start.intersectionXY(line_end)
        p1, center, p2 = GcArc.arcCenter(line_start.start, ip, line_end.end, radius)
        return GcArc.fromTwoPointsAndCenter(p1, p2, center)
    
    @staticmethod
    def fromTwoPointsAndCenter(start: GcPoint, end: GcPoint, center: GcPoint, attributes = {}) -> "GcArc":
        """constructs an arc segment between the first two Points with the third point beeing used as the center of the arcs circle"""
        return GcArc.fromQgs(QgsCircularString.fromTwoPointsAndCenter(start.toQgsPoint(), end.toQgsPoint(), center.toQgsPoint()), attributes)
    

    @staticmethod
    def listFromQgsCircularString(circular_string: QgsCircularString) -> list["GcArc"]:
        points = circular_string.points()
        arc_segments = []

        if len(points) < 3:
            return arc_segments

        arc_segments.append(GcArc(
            GcPoint.fromQgs(points[0]),
            GcPoint.fromQgs(points[1]),
            GcPoint.fromQgs(points[2])
        ))

        if len(points) > 3:
            i = 2
            while i < (len(points) - 1):
                arc_segments.append(GcArc(
                    GcPoint.fromQgs(points[i]),
                    GcPoint.fromQgs(points[i + 1]),
                    GcPoint.fromQgs(points[i + 2])
                ))
                i = i + 2
            
        return arc_segments
    
    @staticmethod
    def arcCenter(
        start_point: GcPoint, corner: GcPoint, end_point: GcPoint, radius: float
    ) -> Tuple[GcPoint, GcPoint, GcPoint]:
        """Calculates the start point, Origin point an end Point of the Arc between the Edge described by the three given points
        Returns the start point of the arc, the Origin Point of the arcs circle and the end point of the arc
        """

        vector1 = GcDirection(start_point.x - corner.x, start_point.y - corner.y).normalize()
        vector2 = GcDirection(end_point.x - corner.x, end_point.y - corner.y).normalize()

        vector_sum = GcDirection(
            vector1.x + vector2.x, vector1.y + vector2.y
        ).normalize()

        vector_sum = GcDirection(vector_sum.x * radius, vector_sum.y * radius)

        # radians
        alpha = vector2.angleToXY(vector1) / 2

        if vector_sum.y < 0:
            alpha = -alpha

        circle_origin = GcPoint(corner.x + vector_sum.x, corner.y + vector_sum.y)

        result1 = GcPoint(
            corner.x + (vector1.x * radius / math.tan(alpha)),
            corner.y + (vector1.y * radius / math.tan(alpha)),
        )
        result2 = GcPoint(
            corner.x + (vector2.x * radius / math.tan(alpha)),
            corner.y + (vector2.y * radius / math.tan(alpha)),
        )

        return result1, circle_origin, result2
      

    def sliceFractionXY(self, start: float, end: float) -> "GcArc":
        return GcArc(self.interpolatePointFractionXY(start), self.interpolatePointFractionXY(start + (end - start) / 2), self.interpolatePointFractionXY(end), self.attributes)

    def sliceDistanceXY(self, start: float, end: float) -> "GcArc":
        return GcArc(self.interpolatePointDistanceXY(start), self.interpolatePointDistanceXY(start + (end - start) / 2), self.interpolatePointDistanceXY(end), self.attributes)

    def sliceFractionXYZ(self, start: float, end: float) -> "GcArc":
        return GcArc(self.interpolatePointFractionXYZ(start), self.interpolatePointFractionXYZ(start + (end - start) / 2), self.interpolatePointFractionXYZ(end), self.attributes)

    def sliceDistanceXYZ(self, start: float, end: float) -> "GcArc":
        return GcArc(self.interpolatePointDistanceXYZ(start), self.interpolatePointDistanceXYZ(start + (end - start) / 2), self.interpolatePointDistanceXYZ(end), self.attributes)
