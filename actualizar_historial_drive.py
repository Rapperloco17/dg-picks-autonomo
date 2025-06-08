from drive_utils import descargar_archivos_drive, subir_archivo_drive
import os

def actualizar_historial():
    print("Descargando archivos del historial desde Google Drive...")
    archivos = descargar_archivos_drive("Historial_Futbol")
    for archivo in archivos:
        print(f"Procesando {archivo}...")
        # Aquí iría la lógica de análisis o actualización de datos

    print("Actualización terminada. Subiendo archivos actualizados...")
    for archivo in archivos:
        subir_archivo_drive("Historial_Futbol", archivo)

if __name__ == "__main__":
    actualizar_historial()
