"""
Job de ingesta de la planilla oficial de plaguicidas autorizados del SAG.

Descarga el .xlsx público del SAG *del lado del servidor* (aquí no hay
restricción de CORS, a diferencia de hacerlo desde el navegador) y reemplaza
el contenido de la tabla 'fitosanitarios_sag'. Pensado para correr una vez
por semana, ya que el SAG actualiza esta planilla ocasionalmente, no a diario.

IMPORTANTE: hay que revisar el nombre de las columnas la primera vez que se
corre — el SAG cambia el nombre exacto del archivo (incluye la fecha) y
puede variar ligeramente el nombre de las columnas entre versiones. Ajusta
el diccionario MAPEO_COLUMNAS de acuerdo a lo que traiga tu descarga.

Uso manual:
    python -m app.jobs.ingest_sag

Uso en cron (todos los lunes a las 6am):
    0 6 * * 1  cd /ruta/al/backend && /ruta/al/venv/bin/python -m app.jobs.ingest_sag
"""

import io

import requests
import openpyxl

from app.database import SessionLocal
from app.config import settings
from app import models

# Ajusta estas claves según los encabezados reales de la planilla descargada.
# La izquierda es el nombre de columna esperado en el .xlsx; la derecha, el
# campo de nuestra tabla. Si el SAG cambia encabezados, solo se edita aquí.
MAPEO_COLUMNAS = {
    "Nombre Comercial": "nombre_comercial",
    "Ingrediente Activo": "ingrediente_activo",
    "Titular": "empresa",
    "Categoria": "categoria",
    "N° Registro": "numero_registro",
    "Vigencia": "vigencia",
}


def descargar_planilla() -> openpyxl.workbook.Workbook:
    resp = requests.get(settings.sag_xlsx_url, timeout=30)
    resp.raise_for_status()
    return openpyxl.load_workbook(io.BytesIO(resp.content), data_only=True)


def correr():
    wb = descargar_planilla()
    hoja = wb.worksheets[0]

    filas = list(hoja.iter_rows(values_only=True))
    encabezados = [str(c).strip() if c else "" for c in filas[0]]
    indices = {col: encabezados.index(col) for col in MAPEO_COLUMNAS if col in encabezados}

    faltantes = set(MAPEO_COLUMNAS) - set(indices)
    if faltantes:
        print(f"Aviso: no se encontraron estas columnas en la planilla: {faltantes}")
        print(f"Encabezados reales encontrados: {encabezados}")

    db = SessionLocal()
    try:
        db.query(models.FitosanitarioSAG).delete()
        insertados = 0
        for fila in filas[1:]:
            if not any(fila):
                continue
            registro = {
                campo: (fila[indices[col]] if col in indices else None)
                for col, campo in MAPEO_COLUMNAS.items()
            }
            db.add(models.FitosanitarioSAG(**registro))
            insertados += 1
        db.commit()
        print(f"Listo: {insertados} productos cargados desde la planilla del SAG.")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
