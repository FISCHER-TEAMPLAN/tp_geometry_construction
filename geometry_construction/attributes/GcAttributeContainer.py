from qgis.core import QgsFeature, QgsField, QgsFields
from typing import Optional
from qgis.PyQt.QtCore import QVariant
from typing import Union

class GcAttributeContainer():
    def __init__(self) -> None:
        self.attributes = {}

    def replaceAttributesSelf(self, target: Union["GcAttributeContainer", dict[str,object]]):
        """Deletes All Attributes of self and the copys all attributes form the Target (container or dict)"""
        self.attributes = {}
        self.overwriteAttributesSelf(target)

    def augmentAttributesSelf(self, target: Union["GcAttributeContainer", dict[str,object]]):
        """Copys all Attributes from target (container or dict), that self does not have"""
        if isinstance(target, GcAttributeContainer):
            target = target.attributes

        for key, value in target.items():
            if self.attributes.get(key, False):
                continue
            self.attributes[key] = value

    def overwriteAttributesSelf(self, target: Union["GcAttributeContainer", dict[str,object]]):
        """Copys all Attributes from target (container or dict), overwriting attributes that self has"""
        if isinstance(target, GcAttributeContainer):
            target = target.attributes

        for key, value in target.items():
            self.attributes[key] = value

    def toQgsFields(self) -> QgsFields:
        """Assumes fitting QGIS Filds for the data currently stored in the attributes"""

        fields = QgsFields()
        for key, value in self.attributes.items():
            type = QVariant.String

            if isinstance(value, QVariant):
                type = value.Type()
            
            elif isinstance(value, bool):
                type = QVariant.Bool

            elif isinstance(value, int):
                type = QVariant.Int
            
            elif isinstance(value, float):
                type = QVariant.Double     

            field = QgsField(key, type)
            fields.append(field)
        return fields

    def toQgsFeature(self, fields: Optional[QgsFields] = None) -> QgsFeature:
        """Creates an empty Qgis Feature and assigns all Matching Attributes of the given Fields to it.
        If no fields are Given, the proper fields are assumed from the attributes type"""
        feat = QgsFeature()

        if fields == None:
            fields = self.toQgsFields()

        feat.setFields(fields)

        for key, _value in feat.attributeMap().items():
            feat.setAttribute(key, self.attributes.get(key))

        return feat