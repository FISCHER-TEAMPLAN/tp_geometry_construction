from qgis.core import QgsAbstractGeometry, QgsGeometryCollection, QgsMessageLog, QgsFeature, QgsGeometry, QgsSpatialIndex
from .abstract.GcBase import GcBase
from .GcPoint import GcPoint
from typing import TypeVar, Union, Type, Generic


T = TypeVar('T', bound=GcBase)
class GcCollection(Generic[T], GcBase):
    
    def __init__(self, geometries: list[T] = [], attributes = {}) -> None:
        super().__init__()
        self.replaceAttributesSelf(attributes)
        self.parts: list[T] = []
        for g in geometries:
            self.parts.append(g)

        self.spacial_index = None
    
    def updateSpacialIndex(self):
        self.spacial_index = QgsSpatialIndex(QgsSpatialIndex.FlagStoreFeatureGeometries)
        for i, p in enumerate(self.parts):
            f = p.toQgsFeature()
            f.setId(i)
            self.spacial_index.addFeature(f)

    @property
    def points(self) -> list["GcPoint"]:
        point_list = []
        for e in self.parts:
            for p in e.points:
                point_list.append(p)
        return point_list
    
    @property
    def children(self) -> list[T]:
        return self.parts
    
    def toQgs(self) -> QgsAbstractGeometry:
        """Not Implemented"""
        return super().toQgs()
    
    @staticmethod
    def fromQgsFeature(feature: QgsFeature) -> "GcCollection[T]":
        """Returns a collcetion with the geometries of the Qgis Feature - if they are compatible"""
        col = GcCollection[T]([],feature.attributeMap())
        return col


    @staticmethod
    def fromQgs(qgs_geom: QgsAbstractGeometry, attributes = {})  -> "GcCollection[T]":
        col = GcCollection[T](attributes=attributes)
        return col

    def clone(self) -> "GcCollection[T]":
        cl = GcCollection()
        for g in self.parts:
            cl.parts.append(g.clone())
        return cl
    
    def connectionPoints(self, precision = 3) -> list[list[tuple[GcPoint,T]]]:
        """ For every point, where 2 or more Geometries of this collection touch, a list is returned. 
        This list contains a tuple of the touching point and the geometry the point belongs to

        This function is not recursive - consider the folowing example:
         - collection a
         - collection b
         
        *GcCollection([a,b]).connectionPoints()* -> Returns all points that are shared between a and b, 
            does not return points that are shared within geometries of a or geometries of b
        
        
        *c = GcCollection(a.copy())*

        *c.extend(b)*

        *c.connectionPoints()* -> Returns all points that are shared within any geometries within a and b.
        """
        p_dict = {}

        for g in self.parts:
            for p in g.points:
                id = p.spacialIdXY(precision)
                if not p_dict.get(id,False):
                    p_dict[id] = []
                p_dict[id].append((p,g))
        
        ret = []

        for v in p_dict.values():
            if len(v) > 1:
                ret.append(v)

        return ret