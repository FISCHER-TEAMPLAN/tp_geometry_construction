from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, Optional, Type, Union
from qgis.core import *
from ...attributes.GcAttributeTree import GcAttributeTree
from ...GcConfig import gc_config


T = TypeVar('T', bound='GcBase')

if TYPE_CHECKING:
    from ..GcPoint import GcPoint
    from ..GcDirection import GcDirection
    from ..GcCollection import GcCollection

class GcBase(GcAttributeTree):
    """Abstract class representing a common interface for all geometry like objects"""
    def __init__(self) -> None:
        super().__init__()

    qgs_layer_signature = ""

    @property
    @abstractmethod
    def points(self) -> list["GcPoint"]:
        pass

    @abstractmethod
    def clone(self: T) -> T:
        """returns a new object that is a full copy of the current one"""
        pass

    def translateSelfXYZ(self, direction: "GcDirection", distance: float):
        """Translates itself about the given direction and distance. M dimension stays unmodifyed"""
        for p in self.points:
            p.translateSelfXYZ(direction, distance)
    

    def rotateSelfXY(self, origin: "GcPoint", angle: float):
        """Rotates itself around the center by the angle in radiants"""
        for p in self.points:
            p.rotateSelfXY(origin, angle)

    def translateXYZ(self: T, direction: "GcDirection", distance: float) -> T:
        """retuns a moved copy of the geometry about the given direction and distance. M dimension stays unmodifyed"""
        n = self.clone()
        n.translateSelfXYZ(direction, distance)
        return n
    
    def rotateXY(self: T, origin: "GcPoint", angle: float) -> T:
        """returns a new object rotated around the center by the angle in radiants"""
        n = self.clone()
        n.rotateXY(origin, angle)
        return n
    
    def forEachPoint(self: T, point_function) -> T:
        """returns a copy of this Geometry with the given function applied to all points"""
        geom = self.clone()
        for new_p in geom.points, self.points:
            new_p.replaceWith(point_function(new_p))
        return geom
    
    @classmethod
    def fromQgsFeature(cls: Type[T], feature: QgsFeature) -> Optional[T]:
        """If the given QGIS Feature has a compatible geometry type a new Instance is returned. If not, None is retuned"""

        if not cls.QgsFeatureValidForConstruction(feature):
            return None
        
        geom = feature.geometry()
        abs_geom = geom.get()
        if not abs_geom:
            return None

        try:
            return cls.fromQgs(abs_geom, feature.attributeMap())
        except:
            return None
        
    @classmethod
    def collectionFromQgsFeature(cls: Type[T], feature: QgsFeature) -> "GcCollection[T]":
        from ..GcCollection import GcCollection

        col = GcCollection[T]([],feature.attributeMap())
        geom = feature.geometry()
        abs_geom = geom.get()

        if not abs_geom or not isinstance(abs_geom, QgsGeometryCollection):
            return col

        num = abs_geom.numGeometries()

        for i in range(0,num):
            try:
                res =  cls.fromQgs(abs_geom.geometryN(i), feature.attributeMap())
                if res:
                    col.parts.append(res)
            except:
               continue

        return col


    @staticmethod
    def QgsFeatureValidForConstruction(feature: QgsFeature) -> bool:
        if not feature.hasGeometry():
            return False
        
        geom = feature.geometry()

        if geom.isEmpty():
            return False
        
        return True

    def toQgsFeature(self, fields: Optional[QgsFields] = None) -> QgsFeature:
        """Creates a QGIS Feature from the current Object"""
        feat = super().toQgsFeature(fields)
        feat.setGeometry(self.toQgsGeometry())
        return feat

    @abstractmethod
    def toQgs(self) -> QgsAbstractGeometry:
        """Returns the QgsAbstract Geoemetry, that Represents this Object.
        Not every object might have a corresponding abstract geometry."""
        pass

    def toQgsGeometry(self) -> QgsGeometry:
        """Returns a new Qgis Geometry representing the current Object"""
        return QgsGeometry(self.toQgs())

    @staticmethod
    @abstractmethod
    def fromQgs(qgs_geom: QgsAbstractGeometry, attributes = {}) -> T:
        """Creates an instance from any valid QgsAbstractGeometry. 
        If no valid Geometry is given, ValueError is raised"""
        pass

    def sampleZ(self: T, dem_layer: Union[QgsRasterLayer,QgsMeshLayer], band_index = 1, default_value: float = gc_config.default_z_value) -> T:
        """Returs a Copy of this Opject with the Z values set according to the Given DEM. Nodata values will be set to the Default nodata value.
        This function supports Raster and Mesh layers as Elevation input"""
        p = self.clone()
        p.sampleZSelf(dem_layer, band_index, default_value)
        return p
    
    def sampleZSelf(self,dem_layer: Union[QgsRasterLayer,QgsMeshLayer], band_index = 1, default_value: float = gc_config.default_z_value) -> list[bool]:
        """Reads the given DEM at every Point and sets the Z value accordingly. Nodata values will be set to the Default nodata value.
        Returns an array of Bool, where each value corresponts to the Point at that Index.
        if it is True, the DEM value was used at that Point. If it is False, Nodata value was used instead.
        This function supports Raster and Mesh layers as Elevation input"""

        #can be called if input data is invalid, to set z of all points to the default value
        def allInvalid():
            report = []

            for p in self.points:
                report.append(False)
                p.z = default_value
                return report

        
        #Get Elevation from Raster, if the Given Layer is a Raster Layer
        if dem_layer.type() == QgsMapLayer.RasterLayer:
            dp = dem_layer.dataProvider()

            if not dp:
                return allInvalid()
            
            count = dp.bandCount()
            if count < band_index:
                return allInvalid()
            
            report = []
            for p in self.points:
                z = dp.identify(p.toQgsPointXY(), QgsRaster.IdentifyFormatValue).results()[band_index]
                if z is None or z is NULL:
                    p.z = default_value
                    report.append(False)
                    continue
                
                p.z = z
                report.append(True)
            
            return report
        
        #Get Elevation from Mesh, if the Given layer is a Mesh Layer
        elif dem_layer.type() == QgsMapLayer.MeshLayer:
            dem_layer.createMapRenderer(QgsRenderContext())
            active_dataset_group = dem_layer.rendererSettings().activeScalarDatasetGroup()

            dataset_index = dem_layer.staticScalarDatasetIndex().dataset()
            if dataset_index < 0:
                dataset_index=0

            mesh_dataset = QgsMeshDatasetIndex(active_dataset_group, dataset_index)

            report = []
            for p in self.points:
                try:
                    p.z = dem_layer.datasetValue(mesh_dataset, p.toQgsPointXY()).scalar()
                    report.append(True)
                except:
                    p.z = default_value
                    report.append(False)
            
            return report
    
    def augmentPointAttributesWithSelf(self):
        """Copys the Attributes from self to every Point, if the Point does not already have an Attribute with the same name"""
        for p in self.points:
            p.augmentAttributesSelf(self)

    def replacePointAttributesWithSelf(self):
        """Removes all Attributes from Every point - then Copys the Attributes from self to every Point"""
        for p in self.points:
            p.replaceAttributesSelf(self)

    def overwritePointAttributesWithSelf(self):
        """Copys all Attributes form self to every Point, Overwriting Attributes of the point with the same name"""
        for p in self.points:
            p.overwriteAttributesSelf(self)
    
    def emptyQgsLayerLikeSelf(self, name: str) -> QgsVectorLayer:
        """Creates an empty QGIS layer with the given name based on this Objects Geometry and Attributes"""
        layer = QgsVectorLayer(self.qgs_layer_signature + "?crs=" + QgsProject.instance().crs().toWkt(),
                            name, "memory")
        
        layer.dataProvider().addAttributes(self.toQgsFields())
        layer.updateFields()
        return layer

    def toQgsLayer(self, name) -> QgsVectorLayer:
        """Creates a QGIS layer with this Object as QgsFeature added to it"""
        layer = self.emptyQgsLayerLikeSelf(name)
        layer.startEditing()
        layer.addFeatures([self.toQgsFeature(layer.fields())])
        layer.commitChanges()
        layer.updateExtents()
        return layer
    
    def _filterdGeometryOperation(self, target: QgsGeometry, expected_type: Type[T], function_name: str) -> Optional[T]:
        """Performs the given Geometry Operation on self an target and casting the result to the given Gc Geometry type.
         if unsucessfull, nothiong is returned"""
        
        try:
            a = self.toQgsGeometry()
            geom = getattr(a, function_name)(target)
            return expected_type.fromQgs(geom.get())
        except ValueError:
            return
    
    def filterdIntersection(self, target: QgsGeometry, expetcs: Type[T]) -> Optional[T]:
        """Performes an Itersection between self an the target geometry. Casts the result as a geometry of the given type and returns the result.
        if the intersection result is not of the given type, none is returned."""

        return self._filterdGeometryOperation(target, expetcs, "intersection")

