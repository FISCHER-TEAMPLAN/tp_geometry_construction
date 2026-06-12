from .abstract.GcBase import GcBase
from .GcCompoundCurve import GcCompoundCurve
from .GcPoint import GcPoint
from qgis.core import QgsAbstractGeometry, QgsCurve, QgsCurvePolygon, QgsPolygon

class GcPolygon(GcBase):
    """A (Curved) Poligon consinsting of an Exterior ring and a list of interior rings, that represent a cutout"""

    qgs_layer_signature = "CurvePolygonZ"
    exterior_ring: GcCompoundCurve
    interior_rings: list[GcCompoundCurve]

    def __init__(self, exterior_ring: GcCompoundCurve, interior_rings: list[GcCompoundCurve] = [], attributes = {}):
        super().__init__()
        self.exterior_ring = exterior_ring.clone()
        self.interior_rings = [x.clone() for x in interior_rings]
        self.replaceAttributesSelf(attributes)
        

    @property
    def points(self) -> list[GcPoint]:
        point_list = self.exterior_ring.points
        for i_ring in self.interior_rings:
            point_list.extend(i_ring.points)
        return point_list

    def clone(self: "GcPolygon") -> "GcPolygon":
        """returns a new object that is a full copy of the current one"""

        return GcPolygon(self.exterior_ring, self.interior_rings, self.attributes)

    @staticmethod
    def fromQgs(qgs_geom: QgsAbstractGeometry, attributes = {}) -> "GcPolygon":
        """Creates an instance from any valid QgsAbstractGeometry. 
        If no valid Geometry is given, ValueError is raised"""

        if isinstance(qgs_geom, QgsCurvePolygon):
            ext_ring = GcCompoundCurve.fromQgs(qgs_geom.exteriorRing())
            ring_nums = qgs_geom.numInteriorRings()
            rings = []
            for i in range(ring_nums):
                rings.append(GcCompoundCurve.fromQgs(qgs_geom.interiorRing(i)))

            return GcPolygon(ext_ring, rings, attributes)
        
        if isinstance(qgs_geom, QgsCurve):
            return GcPolygon(GcCompoundCurve.fromQgs(qgs_geom.exteriorRing()), [], attributes)
            

    def toQgs(self) -> QgsCurvePolygon:
        """Returns a curved Polygon from this object. Even when no curves are present.
        Use toQgsPolygon to explicitly create a segmentized version"""

        return self.toQgsCurvePolygon()
    
    def toQgsCurvePolygon(self):
        """Returns a Curved Polygon based on this objects Geometry"""

        qpoly = QgsCurvePolygon()
        qpoly.setExteriorRing(self.exterior_ring.toQgsCompoundCurve())
        for ring in self.interior_rings:
            qpoly.addInteriorRing(GcCompoundCurve(ring))
        
        return qpoly
    
    def toQgsPolygon(self) -> QgsPolygon:
        """returns a segmentized version of this geometry as a qgis Polygon"""

        qpoly = self.toQgs()
        return qpoly.segmentize()