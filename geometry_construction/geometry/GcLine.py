from qgis.core import QgsAbstractGeometry, QgsLineString, QgsGeometryUtils, QgsVectorLayer, QgsRectangle
from .GcPoint import GcPoint
from .GcDirection import GcDirection
from .abstract.GcCurve import GcCurve
from decimal import *
from typing import Optional
from .GcCollection import GcCollection
from typing import TypeVar, TYPE_CHECKING, Tuple

T = TypeVar('T', bound=GcCurve)

import math

class GcLine(GcCurve):
    """A straight line from the start point to the endpoint"""

    qgs_layer_signature = "LineStringZ"

    def __init__(self, start: GcPoint, end: GcPoint, attributes = {}) -> None:
        super().__init__()
        self.start = start.clone()
        self.end = end.clone()
        self.replaceAttributesSelf(attributes)

    def clone(self) -> "GcLine":
        return GcLine(self.start.clone(), self.end.clone(), self.attributes)
    
    @property
    def children(self) -> list[GcPoint]:
        return self.points

    @property
    def lengthXY(self) -> float:
        """The 2D Length of this line in XY direction"""
        return self.start.distanceXY(self.end)
    
    @property
    def lengthXYZ(self) -> float:
        """The 3D Length of this line in XYZ direction"""
        return self.start.distanceXYZ(self.end)

    @property
    def incline_angle(self) -> float:
        """The Incline in Radiants - positive value for Upward slopes, negative value for downward slopes. Compares Z value to line length"""
        if self.start.z == self.end.z:
            return 0.0
        
        incline = (self.end.z - self.start.z) / self.lengthXY

        angle = abs(math.atan(incline))
        
        if self.start.z > self.end.z:
            return -angle
        
        return angle
    
    @property
    def incline_angleXY(self) -> float:
        """The Incline in Radiants - positive value for Upward slopes, negative value for downward slopes. Compares Y value to line length X"""
        if self.start.y == self.end.y:
            return 0.0
        
        incline = (self.end.y - self.start.y) / (self.end.x - self.start.x)

        angle = abs(math.atan(incline))
        
        if self.start.y > self.end.y:
            return -angle
        
        return angle
    
    @property
    def directionXYZ(self) -> GcDirection:
        return GcDirection(
            self.end.x - self.start.x,
            self.end.y - self.start.y,
            self.end.z - self.start.z
        ).normalize()
    
    @property
    def directionXY(self) -> GcDirection:
        return GcDirection(
            self.end.x - self.start.x,
            self.end.y - self.start.y
        ).normalize()
    
    @staticmethod
    def fromMZXY(line: "GcLine") -> "GcLine":
        return GcLine(GcPoint.fromMZXY(line.start), GcPoint.fromMZXY(line.end), line.attributes)
    
    def toMZXY(self) -> "GcLine":
        return GcLine(self.start.toMZXY(), self.end.toMZXY(), self.attributes)
    
    def intersectionXY(self, target: "GcLine") -> Optional[GcPoint]:
        """Calculates the 2D Intersection of two given lines. The z coordinate is ignored during calculation and the resulting point 'has no z value' (z = 0)
        the lines are also treated, as if they are infinitly long"""

        def preprocess(line: "GcLine"):
            """Weird 2D math stuff needed for S curve creation, intersection calculation, etc."""
            getcontext().prec = 30
            A = (Decimal(line.start.y) - Decimal(line.end.y))
            B = (Decimal(line.end.x) - Decimal(line.start.x))
            C = (Decimal(line.start.x)*Decimal(line.end.y) - Decimal(line.end.x)*Decimal(line.start.y))
            return A, B, -C


        def intersection(L1: tuple[Decimal, Decimal, Decimal], L2: tuple[Decimal, Decimal, Decimal]):
            """Weird 2D math stuff needed for S curve creation, intersection calculation, etc."""
            getcontext().prec = 30
            D = Decimal(L1[0]) * Decimal(L2[1]) - Decimal(L1[1]) * Decimal(L2[0])
            Dx = Decimal(L1[2]) * Decimal(L2[1]) - Decimal(L1[1]) * Decimal(L2[2])
            Dy = Decimal(L1[0]) * Decimal(L2[2]) - Decimal(L1[2]) * Decimal(L2[0])
            if D != 0:
                x = Decimal(Dx) / Decimal(D)
                y = Decimal(Dy) / Decimal(D)
                return GcPoint(float(x), float(y))
            else:
                return None

        return intersection(preprocess(self), preprocess(target))
    
    def translateXYZ(self, direction: GcDirection, distance: float) -> "GcLine":
        return GcLine(
            self.start.translateXYZ(direction, distance),
            self.end.translateXYZ(direction, distance),
            self.attributes
        )
    
    def rotateXY(self, origin: "GcPoint", angle: float) -> "GcLine":
        return GcLine(
            self.start.rotateXY(origin, angle),
            self.end.rotateXY(origin, angle),
            self.attributes
        )

    def invert(self) -> "GcLine":
        """Returns a Copy of the Line, Pointing in the Opposite Direction"""
        l = self.clone()
        l.invertSelf()
        return l
    
    def invertSelf(self):
        e = self.end 
        self.end  = self.start
        self.start = e

    @property
    def points(self) -> list[GcPoint]:
        return [self.start, self.end]
    
    @staticmethod
    def fromPoints(points: list[GcPoint], attributes = {}) -> "GcLine":
        """constructs a Line from an array of two points"""
        return GcLine(points[0], points[1], attributes)
    
    @staticmethod
    def fromStartAngleAndLength(start: GcPoint, angle: float, length: float, attributes = {}) -> "GcLine":
        start = start.clone()
        end = start.translateXYZ(GcDirection(1, 0), length)
        end.rotateSelfXY(start, angle)

        return GcLine(start, end, attributes)
    
    @staticmethod
    def listFromQgsLineString(line_string: QgsLineString) -> list["GcLine"]:
        point_num = line_string.numPoints()
        line_segments = []

        for vertex_index in range(0, point_num-1):
            line_segments.append(GcLine(
                    GcPoint.fromQgs(line_string.pointN(vertex_index)),
                    GcPoint.fromQgs(line_string.pointN(vertex_index + 1))
            ))
        return line_segments
    
    def interpolatePointFractionXY(self, fraction: float) -> GcPoint:
        """Interpolates a point on a line with a given fraction in 2D between 0 and 1. Values outside this bound will be clamped
            M values are not dropeed and Interpolated Linearly
        """

        #in the case of a single line the two functions are equivalent, as every value is interpolated linearly by definition
        return self.interpolatePointFractionXYZ(fraction)


    def interpolatePointFractionXYZ(self, fraction: float) -> GcPoint:
        """Interpolates a point on a line with a given fraction in 3D between 0 and 1. Values outside this bound will be clamped
            Z and M values are not dropeed and Interpolated Linearly
        """
        fraction = max(0, min(fraction, 1))

        return GcPoint(
            self.start.x + (self.end.x - self.start.x) * fraction,
            self.start.y + (self.end.y - self.start.y) * fraction,
            self.start.z + (self.end.z - self.start.z) * fraction,
            self.start.m + (self.end.m - self.start.m) * fraction
        )
    

    def toQgs(self) -> QgsLineString:
        lst = QgsLineString()
        lst.addVertex(self.start.toQgsPoint())
        lst.addVertex(self.end.toQgsPoint())
        return lst
    
    def clockwiseAngleBetweenPointXY(self, target: GcPoint):
        """returns the clockwhise angle between this line and the line formed by (self.end -> target), only considering XY coordinates in radians"""
        return QgsGeometryUtils.angleBetweenThreePoints(self.start.x, self.start.y, self.end.x, self.end.y, target.x, target.y)

    def angleToXY(self, target: "GcLine") -> float:
        """Returns the XY angle to the given line in Radiants (the angle that self needs to be rotated with, to be parralel to target)"""
        return self.directionXY.angleToXY(target.directionXY)
    
    def smallestAngleToXY(self, target: "GcLine") -> float:
        """Returns the XY angle to the given line in Radiants. Always the smallest angle is returned"""
        return self.directionXY.smallestAngleToXY(target.directionXY)
    
    @staticmethod
    def fromQgs(line: QgsLineString, attributes = {}) -> "GcLine":
        return GcLine(GcPoint.fromQgs(line.startPoint()), GcPoint.fromQgs(line.endPoint()), attributes)
    
    def sliceFractionXY(self, start: float, end: float) -> "GcLine":
        return GcLine(self.interpolatePointFractionXY(start), self.interpolatePointFractionXY(end), self.attributes)

    def sliceDistanceXY(self, start: float, end: float) -> "GcLine":
        return GcLine(self.interpolatePointDistanceXY(start), self.interpolatePointDistanceXY(end), self.attributes)

    def sliceFractionXYZ(self, start: float, end: float) -> "GcLine":
        return GcLine(self.interpolatePointFractionXYZ(start), self.interpolatePointFractionXYZ(end), self.attributes)

    def sliceDistanceXYZ(self, start: float, end: float) -> "GcLine":
        return GcLine(self.interpolatePointDistanceXYZ(start), self.interpolatePointDistanceXYZ(end), self.attributes)
    
    def debugString(self) -> str:
        return "Startpoint: " + self.start.debugString() + "\n Endpoint: " + self.end.debugString()
    
    def rayCastXY(self, targets: list[GcCollection[T]], max_ray_length: float = -1, offset_start = 0.000001) -> Optional[tuple[GcPoint,T]]:
        """Perfroms a raycast from start along this line until max_ray_length is reached or an object is hit.
        Hits will returnd as tuple (hitpoint, hit geometry)
        If max raylength is smaller than 0, the length of the geometry will be used as Raylength
        """

        endpoint = self.end
        if max_ray_length > 0:
            endpoint = self.start.translateXYZ(self.directionXY, max_ray_length)

        test_geom = GcLine(self.start.translateXYZ(self.directionXY, offset_start), endpoint)
        test_qgis_geom = test_geom.toQgsGeometry()
        test_qgis_geom.boundingBox()
        test_gqis_startpoint = test_geom.start.toQgsPointXY()

        best_hit = None
        best_hit_point = None
        best_hit_distance = -1

        for target in targets:
            if target.spacial_index is None:
                target.updateSpacialIndex()

            for t_id in target.spacial_index.intersects(test_qgis_geom.boundingBox()):
                t = target.parts[t_id]

                if t == self:
                    continue

                intersection = test_qgis_geom.intersection(target.spacial_index.geometry(t_id))

                ints_res = intersection.closestVertex(test_gqis_startpoint)
                if ints_res[4] < 0:
                    continue

                hit_dist = ints_res[4]

                # hit = test_geom.intersectionXY(t)
                # if not hit:
                #     continue

                # t_len = t.lengthXY
                # if hit.distanceXY(t.start) > t_len or hit.distanceXY(t.end) > t_len:
                #     continue

                # t_len = test_geom.lengthXY
                # hit_dist = test_geom.start.distanceXY(hit)
                # if hit_dist > t_len or hit.distanceXY(test_geom.end) > t_len:
                #     continue

                if hit_dist < best_hit_distance or best_hit_distance == -1:
                    best_hit_distance = hit_dist
                    best_hit = t
                    best_hit_point = ints_res[0]

        if best_hit:
            return (GcPoint.fromQgs(best_hit_point), best_hit)
        return None