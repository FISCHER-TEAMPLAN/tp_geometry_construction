# Teamplan Geometry Construction

Qgis Plugin das als Bilbiothek für plugins dient, welche geometrieconstruction durchführen

# Warum Gibt es dieses Projekt

Geometrieverarbeitung ist ein Komplexes Problem was durch die QGIS Python API (Garbage collection -> C++) Deutlich verkompliziert wird.
Die Geometrie verwaltung in QGIS (und Geos) ist außerdem Primär auf 2D Top-Down betrachtung und Render Performance ausgelegt. Bei Vielen funktionen muss man erst in die Dokumentation schauen, um zu sehen, ob sie mit 2D oder 3D Daten Arbeiten und ob sie inplace sind, oder ob sie ein Kopie anlegen - und welche der Zwei QGIS Point Klassen sie jetzt nochmal brauchte

Teamplan Geometry Construction Addressiert diese Probleme über die Folgenden Paradigmen

# Design Richtlinien
 - Jede Geometrie ist ein Object und Erbt von GcBase
 - Es gibt nur einen Punkt - und der hat immer 4 Dimensionen: XYZM
 - Alle Funktionen geben in ihrem Namen an, auf welchen der Dimensionen sie Arbeiten (z.b. translateXYZ)
 - Alle funktionen ohne "Self" im Namen Erzeugen recursiv eine Vollständinge Kopie des Objects
    - langsamer, reduziert Fehleranfälligkeit aber massiv
 - Alle Datentypen und Funktionen sind Klar Dokumentiert
 - Es wird eine Weniger Performante, aber einfacher zu verarbeitende Datenstruktur verwendet, welche ausschlißlich in python verwaltet wird
    - Alle Objecte verfügen über converter von und zu ihrem QGIS Äquivalent
    - Vermeidet Crashes durch von pythons GC deallocierten speicher, der in Qgis aber noch verwendet wird
 - jedes Object verfügt über Attribute und behällt diese, auch wenn es Teil eines anderen Objectes wird
    - ein punkt mit dem Attribut "namen" behält diesen, auch wenn es Teil einer linie wird
    - diese Linie wiederum behällt ebenfalls all ihre attribute, auch wenn sie Teil einer Collection wird
    - gc stellt Funktionen zum einfachen übertragen von attributen auf kind elemmente und umgekehrt bereit

# Nutzung aus einem plugin

in der ```__init__.py``` des plugins als oberste Zeilen (for jedem anderen Import) folgendes einfügen:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../tp_geometry_construction')))
```

Danch kann die Biliothek in jedem python file des Plugins verwendet werden:
```python
from geometry_construction.geometry.GcLine import GcLine
```

Damit die IDE Typehinting und Autovervollständigung unterstützt, muss Teamplan Geometry Construction noch als Extra pfad eingefügt werden.
Dies unterscheidet sich von IDE zu IDE. Für Visual Studio Code muss die datei ```.vscode/settings.json``` angelegt/bearbeitet werden und es müssen die folgenden Zeilen Ergänzt werden:
```
    "python.analysis.extraPaths": ["../tp_geometry_construction"],
    "python.autoComplete.extraPaths": ["../tp_geometry_construction"]
```
wenn keine anderen Einstellungen gesetzt sind, sieht die Datei am ende so aus:

```json
{
    "python.analysis.extraPaths": ["../tp_geometry_construction"],
    "python.autoComplete.extraPaths": ["../tp_geometry_construction"]
}
```