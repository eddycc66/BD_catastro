from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext,
    QgsRelation,
    QgsField
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
import os

gpkg_path = r"D:/proyecto_catastral/base_catastro.gpkg"

# Crear carpeta si no existe
os.makedirs(os.path.dirname(gpkg_path), exist_ok=True)

# Eliminar si existe
if os.path.exists(gpkg_path):
    os.remove(gpkg_path)

transform_context = QgsProject.instance().transformContext()

def export_first_layer(layer, gpkg_path, layer_name):
    """Crea el GPKG con la primera capa"""
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    options.fileEncoding = "UTF-8"
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
    result, error = QgsVectorFileWriter.writeAsVectorFormatV2(
        layer, gpkg_path, transform_context, options
    )
    print(f"Primera capa '{layer_name}':", "✅" if result == QgsVectorFileWriter.NoError else f"❌ {error}")

def export_additional_layer(layer, gpkg_path, layer_name):
    """Añade más capas al GPKG ya creado"""
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    options.fileEncoding = "UTF-8"
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    result, error = QgsVectorFileWriter.writeAsVectorFormatV2(
        layer, gpkg_path, transform_context, options
    )
    print(f"Capa '{layer_name}':", "✅" if result == QgsVectorFileWriter.NoError else f"❌ {error}")

# 1️⃣ Obtener capas abiertas por nombre exacto
lotes = QgsProject.instance().mapLayersByName("lotes_limpios")[0]
vias = QgsProject.instance().mapLayersByName("vias")[0]
datos_csv = QgsProject.instance().mapLayersByName("datos_distrito_limpio")[0]

# 2️⃣ Crear copia en memoria de datos_distrito_limpio con id_predio
if "id_predio" not in [f.name() for f in datos_csv.fields()]:
    prov = datos_csv.dataProvider()
    prov.addAttributes([QgsField("id_predio", QVariant.String)])
    datos_csv.updateFields()
    
    # Buscar campo 'codigo' y copiarlo a 'id_predio'
    if "codigo" in [f.name() for f in datos_csv.fields()]:
        idx_codigo = datos_csv.fields().indexOf("codigo")
        idx_idpredio = datos_csv.fields().indexOf("id_predio")
        
        from qgis.core import edit
        with edit(datos_csv):
            for feat in datos_csv.getFeatures():
                feat[idx_idpredio] = str(feat[idx_codigo])
                datos_csv.updateFeature(feat)
        print("🆕 Campo 'id_predio' creado y llenado desde 'codigo'.")
    else:
        print("⚠ No se encontró el campo 'codigo', no se pudo llenar 'id_predio'.")

# 3️⃣ Exportar capas
export_first_layer(lotes, gpkg_path, "lotes_limpios")
export_additional_layer(datos_csv, gpkg_path, "datos_distrito_limpio")
export_additional_layer(vias, gpkg_path, "vias")

print(f"🎯 GeoPackage creado en: {gpkg_path}")

# 4️⃣ Cargar capas desde el GPKG
def load_gpkg_layer(gpkg_path, layer_name):
    uri = f"{gpkg_path}|layername={layer_name}"
    layer = QgsVectorLayer(uri, f"{layer_name} (gpkg)", "ogr")
    QgsProject.instance().addMapLayer(layer)
    return layer

lotes_gpkg = load_gpkg_layer(gpkg_path, "lotes_limpios")
datos_gpkg = load_gpkg_layer(gpkg_path, "datos_distrito_limpio")
vias_gpkg = load_gpkg_layer(gpkg_path, "vias")

# 5️⃣ Crear relación
if "id_predio" in [f.name() for f in lotes_gpkg.fields()] and \
   "id_predio" in [f.name() for f in datos_gpkg.fields()]:
    
    relation = QgsRelation()
    relation.setId("relacion_predio")
    relation.setName("Relación Lotes - Datos Distrito")
    relation.setReferencingLayer(datos_gpkg.id())  # Hija
    relation.setReferencedLayer(lotes_gpkg.id())   # Madre
    relation.addFieldPair("id_predio", "id_predio")
    
    if relation.isValid():
        QgsProject.instance().relationManager().addRelation(relation)
        print("🔗 Relación creada correctamente.")
        
        # Abrir panel de relaciones (corregido)
        from qgis.PyQt.QtWidgets import QAction
        for action in iface.mainWindow().findChildren(QAction):
            if "Relaciones" in action.text():
                action.trigger()
                break
    else:
        print("❌ Relación inválida.")
else:
    print("❌ 'id_predio' no existe en ambas capas.")
