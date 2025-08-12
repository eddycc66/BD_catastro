from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsVectorDataProvider
)
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from qgis._3d import QgsVectorLayer3DRenderer, QgsPolygon3DSymbol, Qgs3DMapCanvas
from qgis.gui import QgsGui
import random

# --- 1. Ruta y nombre de la capa ---
ruta_gpkg = "D:/proyecto_catastral/base_catastro.gpkg"  # <-- Cambia por tu ruta
nombre_capa = "lotes_limpios"

# --- 2. Cargar capa ---
layer_path = f"{ruta_gpkg}|layername={nombre_capa}"
layer = QgsVectorLayer(layer_path, nombre_capa, "ogr")
if not layer.isValid():
    raise Exception("No se pudo cargar la capa. Verifica la ruta y el nombre.")
QgsProject.instance().addMapLayer(layer)

# --- 3. Crear campo 'altura' si no existe ---
layer.startEditing()
if 'altura' not in [f.name() for f in layer.fields()]:
    campo_altura = QgsField('altura', QVariant.Double)
    layer.dataProvider().addAttributes([campo_altura])
    layer.updateFields()

# --- 4. Asignar alturas aleatorias ---
idx_altura = layer.fields().indexFromName('altura')
for feature in layer.getFeatures():
    altura_random = round(random.uniform(5, 30), 2)
    layer.changeAttributeValue(feature.id(), idx_altura, altura_random)
layer.commitChanges()

# --- 5. Configurar símbolo 3D ---
symbol3d = QgsPolygon3DSymbol()
symbol3d.setHeight(0)  # Base
symbol3d.setExtrusionHeight(15)  # Fijo para QGIS 3.4

# Cambiar color
material = symbol3d.material()
material.setDiffuse(QColor(200, 100, 50))
symbol3d.setMaterial(material)

# Asignar renderizador
renderer3d = QgsVectorLayer3DRenderer(symbol3d)
layer.setRenderer3D(renderer3d)

# --- 6. Abrir Vista 3D centrada ---
canvas3d = Qgs3DMapCanvas(None)
canvas3d.setWindowTitle("Vista 3D - Catastro")
canvas3d.setLayers([layer])
canvas3d.setViewFromLayerExtent(layer)  # Centrar en la capa
canvas3d.show()

print("✅ Vista 3D abierta y centrada en la capa.")
