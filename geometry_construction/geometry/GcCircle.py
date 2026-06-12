from .abstract.GcBase import GcBase
from .GcPoint import GcPoint
from qgis.core import QgsCircle
from .GcDirection import GcDirection
from .GcLine import GcLine
from typing import Optional


class GcCircle(GcBase):

    qgs_layer_signature = "CircularStringZ"

    def __init__(self, center: GcPoint, radius: float, azimuth: float = 0.0, attributes = {}) -> None:
        self.center = center.clone()
        self.radius = radius
        self.azimuth = azimuth
        super().__init__()
        self.replaceAttributesSelf(attributes)

    @property
    def points(self) -> list[GcPoint]:
        return [self.center]
    
    @property
    def children(self) -> list[GcPoint]:
        return self.points
    
    def clone(self) -> "GcCircle":
        """returns a new object that is a full copy of the current one"""
        return GcCircle(self.center, self.radius, self.azimuth, self.attributes)

    def toQgs(self) -> QgsCircle:
        return QgsCircle(self.center.toQgsPoint(), self.radius, self.azimuth)

    @staticmethod
    def fromQgs(qgs_geom: QgsCircle, attributes = {}) -> "GcCircle":
        return GcCircle(GcPoint.fromQgs(qgs_geom.center()), qgs_geom.radius(), attributes=attributes)
    
    @staticmethod
    def from3Points(pt1: GcPoint, pt2: GcPoint, pt3: GcPoint, epsilon: float = 1e-08, attributes = {}):
       return GcCircle.fromQgs(QgsCircle.from3Points(pt1.toQgsPoint(), pt2.toQgsPoint(), pt3.toQgsPoint(), epsilon), attributes)
    
    @staticmethod
    def fromPointDirectionAndRadius(point_on_arc: GcPoint, direction: GcDirection, radius: float, attributes = {}) -> "GcCircle":
        """Creates a circle from a point on the circle, the radius and a direction to the circles center"""
        return GcCircle(point_on_arc.translateXYZ(direction.normalize(),radius), radius, attributes=attributes)

    @staticmethod
    def fromPointAndCenter(point_on_arc: GcPoint, center: GcPoint, attributes = {}) -> "GcCircle":
        """Creates a circle from a point on the circle, the center Point of that circle"""
        return GcCircle(center, center.distanceXY(point_on_arc),attributes=attributes)

    def innerTangents(self, other_circle: "GcCircle") -> tuple[int, Optional[GcLine], Optional[GcLine]]:
        """Calculates the Innter tangets lines 
        (the two lines that cross each other and touch booth circles on opposide sides) 
        of this circle and the given circle

        Those tangents only exist, when the two circles don't intersect or touch

        If the tangents exist, it is ensured, that their startpoint lies on this circle and theire Endpoint lies on other_circle

        booth tangent points will have the Z value of the center point of there corresponding circles

        Returns:
        - the number of tangents (either 2 or 0)
        - the first tangent or None
        - the second tangent or None
        """
        tangent_count, l1p1, l1p2, l2p1, l2p2 = self.toQgs().innerTangents(other_circle.toQgs())
        if tangent_count < 2:
            return 0, None, None
        
        t1 = GcLine(GcPoint.fromQgsPointXY(l1p1),GcPoint.fromQgsPointXY(l1p2))
        t2 = GcLine(GcPoint.fromQgsPointXY(l2p1),GcPoint.fromQgsPointXY(l2p2))

        self._reorientCircleTangent(other_circle, t1)
        self._reorientCircleTangent(other_circle, t2)

        
        return 2, t1, t2
    
    def outerTangents(self, other_circle: "GcCircle") -> tuple[int, Optional[GcLine], Optional[GcLine]]:
        """Calculates the outer tangets lines 
        (the two lines that do not cross each other and touch booth circles on the same side) 
        of this circle and the given circle

        Those tangents only exist, when the two circles are not identical and one circle is not fully contained within the other

        If the tangents exist, it is ensured, that their startpoint lies on this circle and theire Endpoint lies on other_circle

        booth tangent points will have the Z value of the center point of there corresponding circles

        Returns:
        - the number of tangents (either 2 or 0)
        - the first tangent or None
        - the second tangent or None
        """
        tangent_count, l1p1, l1p2, l2p1, l2p2 = self.toQgs().outerTangents(other_circle.toQgs())
        if tangent_count < 2:
            return 0, None, None
        
        t1 = GcLine(GcPoint.fromQgsPointXY(l1p1),GcPoint.fromQgsPointXY(l1p2))
        t2 = GcLine(GcPoint.fromQgsPointXY(l2p1),GcPoint.fromQgsPointXY(l2p2))

        self._reorientCircleTangent(other_circle, t1)
        self._reorientCircleTangent(other_circle, t2)

        
        return 2, t1, t2

    def _reorientCircleTangent(self, target: "GcCircle", tangent: GcLine):
        """Internal use only. Reorients the given tangent to point away from self and applys the z value of self.center and target.center"""
        if abs(self.center.distanceXY(tangent.start) - self.radius) > 1e-08:
            tangent.invertSelf()

        tangent.start.z = self.center.z
        tangent.end.z = target.center.z
