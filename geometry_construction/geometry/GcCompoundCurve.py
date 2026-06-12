from .GcPoint import GcPoint
from .abstract.GcCurve import GcCurve
from .GcArc import GcArc
from .GcLine import GcLine
from typing import Optional
from qgis.core import QgsCompoundCurve, QgsCircularString, QgsLineString, QgsFeature, QgsVectorLayer, QgsAbstractGeometry, QgsGeometry
from typing import TypeVar, Generic, Union
import math

T = TypeVar('T', bound=GcCurve)

class GcCompoundCurve(Generic[T], GcCurve):

    qgs_layer_signature = "CompoundCurveZ"

    def __init__(self, parts: list[T] = [], attributes = {}) -> None:
        super().__init__()

        self.parts: list[T] = list[T]()

        for p in parts:
            self.append(p)

        self.replaceAttributesSelf(attributes)

    @property
    def children(self) -> list[T]:
        return self.parts

    @property
    def start(self) -> Optional[GcPoint]: 
        if len(self.parts) > 0:
            return self.parts[0].start
        return None

    @property
    def end(self) -> Optional[GcPoint]:
        if len(self.parts) > 0:
            return self.parts[len(self.parts) - 1].end
        return None

    @property
    def lengthXY(self) -> float:
        """The 2D Length of this curve in XY direction"""
        acc_len = 0.0
        for g in self.parts:
            acc_len += g.lengthXY
        return acc_len
    
    @property
    def lengthXYZ(self) -> float:
        """The 3D Length of this curve in XYZ direction"""
        acc_len = 0.0
        for g in self.parts:
            acc_len += g.lengthXYZ
        return acc_len

    def invertSelf(self):
        """Inverts the current line direction in place"""
        self.parts.reverse()
        for g in self.parts:
            g.invertSelf()

    def interpolatePointFractionXY(self, fraction: float) -> Optional[GcPoint]:
        """Interpolates a point on this Curve with a given fraction in 2D between 0 and 1. Values outside this bound will be clamped"""
        fraction = max(0, min(fraction, 1))
        target = self.lengthXY * fraction
        current = 0.0
        for p in self.parts:
            pl = p.lengthXY
            if current + pl >= target:
                return p.interpolatePointDistanceXY(target - current)
            
            current = current + pl

    def interpolatePointFractionXYZ(self, fraction: float) -> Optional[GcPoint]:
        """Interpolates a point on this Curve with a given fraction in 3D between 0 and 1. Values outside this bound will be clamped"""
        fraction = max(0, min(fraction, 1))
        target = self.lengthXYZ * fraction
        current = 0.0
        for p in self.parts:
            pl = p.lengthXYZ
            if current + pl >= target:
                return p.interpolatePointDistanceXY(target - current)
            
            current = current + pl

    def invert(self) -> "GcCompoundCurve":
        """Returns a Copy of curve, Pointing in the Opposite Direction"""
        cp = self.clone()
        cp.invertSelf()
        return cp

    @property
    def points(self) -> list[GcPoint]:
        points = []
        if len(self.parts) > 0:
            for p in self.parts:
                points.extend(p.points[0:-1])

            points.append(self.parts[len(self.parts) - 1].end)

        return points

    def clone(self) -> "GcCompoundCurve":
        """returns a new object that is a full copy of the current one"""
        nc = GcCompoundCurve()
        nc.append(self)
        return nc
    
    def _appendSingle(self, sc: GcCurve):
        sc.clone()

        if self.end: 
            self.end.augmentAttributesSelf(sc.start)
            sc.start = self.end

        self.parts.append(sc)

    def append(self, curve: Union[T , list[T]]):   
        """Appends the given GcCurve to this GcCompoundCurve.
        The startpoint of the given GcCurve will be deleted and replaced with the endpoint of self.
        The Attributes of the deleted starpoint will Augment the Attributes of the endpoint of self.
        Dublicate Attributes will be Ignored
        The endpoint of curve will be the new enpoint of self.

        if a list of GcCurves is given, they will be appended in order
        
        It is Allowed to Append a single Compound Curve or an array including Compound Curves.
        This does not Cause nesting. 
        Instead, the parts of the given Compound Curve are appended and the 
        Attributes of self are Augmented with the Attributes of the given Curve(s).
        """
        if isinstance(curve, GcCurve):
            curve = [curve]

        for ci in curve:
            if isinstance(ci, GcCompoundCurve):
                self.augmentAttributesSelf(ci)
                for c in ci.parts:
                    self._appendSingle(c)
            else:
                self._appendSingle(ci)

    @property
    def xy(self) -> "GcCompoundCurve":
        """A Cloned geometry with Z and M dropped"""
        return self.forEachPoint(lambda p: p.xy)
    
    @property
    def xyz(self) -> "GcCompoundCurve":
        """A Cloned geometry with M dropped"""
        return self.forEachPoint(lambda p: p.xyz)
    
    @property
    def mz(self) -> "GcCompoundCurve[GcLine]":
        """Cloned compound curve with MZ as XY"""
        return GcCompoundCurve._pointManipulationAndLinestringConversion(self, lambda p: p.mz)
    
    def toMZXY(self) -> "GcCompoundCurve[GcLine]":
        """Cloned compound curve with MZ as XY and XY as ZM"""
        return GcCompoundCurve._pointManipulationAndLinestringConversion(self,  lambda p: p.toMZXY())


    def toQgs(self) -> QgsCompoundCurve:
        return self.toQgsCompoundCurve()

    def toQgsCompoundCurve(self) -> QgsCompoundCurve:
        cc = QgsCompoundCurve()
        for p in self.parts:
            cc.addCurve(p.toQgs())
        return cc

    def toQgsLineString(self) -> QgsLineString:
        cc = QgsLineString()
        pts = self.points
        for i in range(1, len(pts)):
            cc.append(GcLine(pts[i-1], pts[i]).toQgs())
        return cc

    def toQgsCircularString(self) -> QgsCircularString:
        """Creates a Circular string from this geometry. 
        If the Compound Curve only consists of Arcs, the full geometry is converted.
        if not, the first curve an all curves that imediately follow it are converted"""
        cc = QgsCircularString()
        curve_found = False
        for p in self.parts:
            if isinstance(p, GcArc):
                cc.append(p.toQgs())
                curve_found = True
                continue
            if curve_found:
                break

        return cc


    @staticmethod
    def fromQgs(curve: Union[QgsCompoundCurve, QgsLineString, QgsCircularString], attributes = {}) -> "GcCompoundCurve[GcCurve]":
        if isinstance(curve, QgsCompoundCurve):
            return GcCompoundCurve.fromQgsCompoundCurve(curve, attributes)
        if isinstance(curve, QgsLineString):
            return GcCompoundCurve.fromQgsLineString(curve, attributes)
        if isinstance(curve, QgsCircularString):
            return GcCompoundCurve.fromQgsCircularString(curve, attributes)
    
    
    @staticmethod
    def fromQgsCompoundCurve(curve: QgsCompoundCurve, attributes = {}) -> "GcCompoundCurve[GcCurve]":
        cc = GcCompoundCurve(attributes=attributes)

        for i in range(0,curve.nCurves()):
            current = curve.curveAt(i)
            if isinstance(current,QgsLineString):
                cc.append(GcLine.listFromQgsLineString(current))

            if isinstance(current,QgsCircularString):
                cc.append(GcArc.listFromQgsCircularString(current))
            
        return cc
    
    @staticmethod
    def fromQgsLineString(line_string: QgsLineString, attributes = {}) -> "GcCompoundCurve[GcLine]":
        cc = GcCompoundCurve[GcLine](attributes=attributes)
        cc.append(GcLine.listFromQgsLineString(line_string))
        return cc
    
    @staticmethod
    def fromQgsCircularString(line_string: QgsCircularString, attributes = {}) -> "GcCompoundCurve[GcArc]":
        cc = GcCompoundCurve[GcArc](attributes=attributes)
        cc.append(GcArc.listFromQgsCircularString(line_string))
        return cc
    
    @staticmethod
    def _pointManipulationAndLinestringConversion(curve: "GcCompoundCurve", point_function) -> "GcCompoundCurve[GcLine]":
        """Generalized function to excecute the given function on the points fromt the given compound curve 
        and create a new compound curve consisting of lines connecting the points returned by that function"""
        
        lines: list[GcLine] = []
        last_point: GcPoint = None
        for p in curve.points:
            p = point_function(p)
            if not last_point:
                last_point = p
                continue

            lines.append(GcLine(last_point, p))
            last_point = p

        return GcCompoundCurve(lines, curve.attributes)

    @staticmethod
    def fromMZXY(curve: "GcCompoundCurve") -> "GcCompoundCurve[GcLine]":
        """Transforms a compound curve form the MZXY representation to the regular XYZM represenation. The resulting curve only includes lines - cuves will be converted to lines"""
        
        return GcCompoundCurve._pointManipulationAndLinestringConversion(curve, lambda p: GcPoint.fromMZXY(p, p.attributes))

    @staticmethod
    def mergeTouchingQgsFeauresXY(features: list[QgsFeature]) -> tuple[list["GcCompoundCurve"], list[QgsFeature]]:
        """
        extracts the lines from the given features and builds GcCompoundCurves from them. 
        All touching features that form a continuus line will be merged together in one compound curve.
        Two features are considerd touching, when the endpoint of feature 1 is the startpoint of feature 2

        The Geometry of the Features must be Convertable to GcCompoundCurve

        Returns a Tuple with an array Contianing the CompoundCurves created from the merged Features,
        as well as a list of all features that had faulty geometry or whos geometry id not convertable to GcCompoundCurve.
        Features in the error list are not included in the result list
        """
        
        unorderd_curves = list[GcCompoundCurve]()
        errors = list[QgsFeature]()

        for f in features:
            cc = GcCompoundCurve.fromQgsFeature(f)
            if not cc:
                errors.append(f)
                continue
            cc.overwriteChildAttributesWithSelf()
            unorderd_curves.append(cc)

        curves = GcCompoundCurve.mergeTouchingCurvesXY(unorderd_curves)
        
        return (curves,errors)
    
    @staticmethod
    def mergeTouchingCurvesXY(unorderd_geometry: list[GcCurve]) -> list["GcCompoundCurve"]:
        """Merges all touching curves in the given unorderd list of Curves into a single compoundcurve. Returns all resulting compound curves"""
        class LinkedList():
            next: Optional['LinkedList'] = None
            previuos: Optional['LinkedList'] = None

            def __init__(self, curve: GcCurve) -> None:
                self.curve = curve


        endpoint_dict = dict[str, LinkedList]()

        for curve in unorderd_geometry:
            endpoint_dict[curve.end.spacialIdXY()] = LinkedList(curve)
        
        start = list[LinkedList]()
        for v in endpoint_dict.values():
            v.previuos = endpoint_dict.get(v.curve.start.spacialIdXY())
            if not v.previuos:
                start.append(v)
            else:
                v.previuos.next = v

        compound_curves = []
        for c_line in start:
            pointer = c_line
            ccurve = GcCompoundCurve()
            compound_curves.append(ccurve)
            ccurve.append(c_line.curve)
            while pointer.next:
                pointer = pointer.next
                ccurve.append(pointer.curve)

        return compound_curves


    
    def recalculateMXYZSelf(self, start = 0.0):
        if len(self.parts) == 0:
            return
        
        for c in self.parts:
            c.recalculateMXYZSelf(start)
            start = c.end.m

    def recalculateMXYSelf(self, start = 0.0):
        if len(self.parts) == 0:
            return
        
        for c in self.parts:
            c.recalculateMXYSelf(start)
            start = c.end.m
    
    def sliceFractionXY(self, start: float, end: float) -> "GcCompoundCurve":
        length = self.lengthXY
        return self.sliceDistanceXY(length*start, length*end)
    
    def _sliceDistance(self, start: float, end: float, length_property: str, slice_function: str) -> "GcCompoundCurve":
        """Slice distance prototype function, combining all similar operations from xy and xyz special case reducing code dublication"""

        ref_curve = self
        length = self[length_property]

        if start >= end:
            ref_curve = self.invert()
            tmp = start
            start = end
            end = tmp

        end = max(0, min(length, end))
        start = max(0, min(length, start))

        if start == end:
            return GcCompoundCurve([], self.attributes)

        curves: list[GcCurve] = []

        current = 0.0
        for p in ref_curve.parts:
            pl = p[length_property]
            current = current + pl

            if current <= start:
                continue

            curves.append(p[slice_function](start - current + pl, end - current + pl))

            if current >= end:
                break
        return GcCompoundCurve(curves, self.attributes)
        

    def sliceDistanceXY(self, start: float, end: float) -> "GcCompoundCurve":
        return self._sliceDistance(start, end, "lengthXY", "sliceDistanceXY")

    def sliceFractionXYZ(self, start: float, end: float) -> T:
        length = self.lengthXYZ
        return self.sliceDistanceXYZ(length*start, length*end)

    def sliceDistanceXYZ(self, start: float, end: float) -> T:
        return self._sliceDistance(start, end, "lengthXYZ", "sliceDistanceXYZ")
    
    def _resampleCurve(self, max_distance: float, distance_property: str, slice_function: str) -> "GcCompoundCurve":
        result: list[GcCurve] = []
        
        for p in self.parts:
            p_dist = getattr(p,distance_property)
            segment_num = math.ceil(p_dist / max_distance)

            delta = p_dist / segment_num
            for i in range(0, segment_num):
                result.append(getattr(p,slice_function)(delta * i, delta * (i + 1)))
        
        return GcCompoundCurve(result, self.attributes)
            

    def resampleCurveXY(self, distance: float) -> "GcCompoundCurve":
        """Returns a copy of this curve that haves a point at least on every "distance" Meters. 
        Will not delete points, that are already there. distance is calculated in XY space"""

        return self._resampleCurve(distance, "lengthXY", "sliceDistanceXY")

    def resampleCurveXYZ(self, distance: float) -> "GcCompoundCurve":
        """Returns a copy of this curve that haves a least on every "distance" Meters. 
        Will not delete points, that are already there. distance is calculated in XYZ space"""

        return self._resampleCurve(distance, "lengthXYZ", "sliceDistanceXYZ")
    
    def curveToLine(self, tolerance: float, tolerance_type: QgsAbstractGeometry.SegmentationToleranceType) -> "GcCompoundCurve[GcLine]":
        """Returns a version of this geometry without Curves. All Curves will be aproximated by line goeometry"""

        return GcCompoundCurve.fromQgsLineString(self.toQgs().curveToLine(tolerance, tolerance_type), self.attributes)
    
    def debugString(self) -> str:
        debung_string = f"Parts: {len(self.parts)}\n Points: {len(self.points)}\n\n"
        for i,p in enumerate(self.parts):
            debung_string += str(i) + ": " + type(p).__name__ + " - " + p.debugString() + "\n"
        return debung_string
    
    
    def combineXYwithMZ(self, mz_geom: "GcCompoundCurve", tolerance: float, tolerance_type: QgsAbstractGeometry.SegmentationToleranceType, merge_dist: float = 0.02) -> "GcCompoundCurve":
        """
        This function is currently broken for geometrys with curves, so all curves will be segmentized - this will change in the future

        Returns a copy of this CompoundCurve combined with the Height information from the MZ variant. 
        Will create additional Points along the curve if needed to represent height information"""

        height_reference = mz_geom.curveToLine(tolerance, tolerance_type)

        new_segments: list[GcCurve] = []
        #function currently broken for curves, so geometry is converted to linestring
        clone = self.curveToLine(tolerance, tolerance_type)#self.clone()
        
        for p in clone.points:
            p.z = math.nan
        
        parts: list[GcCurve] = clone.parts
        height_points = height_reference.points
        height_points.sort(key=lambda x: x.x)

        #add additional points for height reference
        i = 0
        for part in parts:
            last_seg = part.start.m

            #skip all points before the start of the geometry
            while i < len(height_points) and (height_points[i].x <= part.start.m or abs(height_points[i].x-part.start.m) <= merge_dist):
                i += 1

            #loop through all points within this segment
            while i < len(height_points) and height_points[i].x < (part.end.m - merge_dist):
                new_segments.append(part.sliceDistanceXY(last_seg, height_points[i].x))
                last_seg = height_points[i].x
                i+=1

            new_segments.append(part.sliceDistanceXY(last_seg, part.end.m))

        new_curve = GcCompoundCurve(new_segments,self.attributes)

        #extract height for every point
        curve_points = new_curve.points
        curve_points.sort(key=lambda x: x.m)

        i = 0
        for cp in curve_points:
            if cp.m >= height_points[len(height_points) - 1].x:
                cp.z = height_points[len(height_points) - 1].y
                continue

            if cp.m <= height_points[0].x:
                cp.z = height_points[0].y
                continue

            #fast forward to next relevant point
            #checing for array bounds not required, due to 
            #cp.m >= height_points[len(height_points) - 1].x conditon
            while cp.m > height_points[i].x:
                i+=1
            
            #linear interpolation to recive height form reference
            p1 = height_points[i - 1]
            p2 = height_points[i]
            diff = p2.y - p1.y
            dist = p2.x - p1.x
            incline = diff / dist

            cp.z = p1.y + (incline * (cp.m - p1.x))

        return new_curve
        
      