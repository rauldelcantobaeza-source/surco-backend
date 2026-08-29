"""
Job de ingesta de agrometeorología (Open-Meteo).

Se ejecuta periódicamente (sugerido: cada 1 hora vía cron) y hace lo siguiente
por cada parcela que tenga latitud/longitud configurada:
  1. Busca o crea su 'estacion_meteo' correspondiente.
  2. Llama a Open-Meteo pidiendo temperatura, humedad, viento, precipitación,
     radiación solar, temperatura de suelo y ETo (evapotranspiración).
  3. Guarda las lecturas horarias nuevas en 'lecturas_meteo'.

Nota sobre agrometeorologia.cl (INIA): su robots.txt bloquea el acceso
automatizado y no ofrecen API pública, así que este job usa Open-Meteo como
fuente (gratuita, con CORS/],acceso abierto, y con las mismas variables).
Si en algún momento consiguen un acuerdo formal de datos con INIA, ese
acceso se agrega aquí como una segunda fuente ('fuente_datos = "inia"'),
sin tocar el resto del sistema.

Uso manual:
    python -m app.jobs.ingest_open_meteo

Uso en cron (cada hora, en punto):
    0 * * * *  cd /ruta/al/backend && /ruta/al/venv/bin/python -m app.jobs.ingest_open_meteo
"""

from datetime import datetime, timezone

import requests

from app.database import SessionLocal
from app import models

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def obtener_o_crear_estacion(db, lat: float, lon: float, nombre: str) -> models.EstacionMeteo:
    lat_r, lon_r = round(lat, 3), round(lon, 3)
    estacion = (
        db.query(models.EstacionMeteo)
        .filter(models.EstacionMeteo.latitud == lat_r, models.EstacionMeteo.longitud == lon_r)
        .first()
    )
    if estacion:
        return estacion
    estacion = models.EstacionMeteo(nombre=nombre, fuente="open-meteo", latitud=lat_r, longitud=lon_r)
    db.add(estacion)
    db.commit()
    db.refresh(estacion)
    return estacion


def traer_datos(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
            "soil_temperature_0cm",
            "shortwave_radiation",
        ]),
        "daily": "et0_fao_evapotranspiration",
        "timezone": "auto",
        "forecast_days": 1,
        "past_days": 1,
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def guardar_lecturas(db, estacion: models.EstacionMeteo, datos: dict):
    hourly = datos.get("hourly", {})
    tiempos = hourly.get("time", [])
    eto_diaria = datos.get("daily", {}).get("et0_fao_evapotranspiration", [None])
    eto_hoy = eto_diaria[-1] if eto_diaria else None

    nuevas = 0
    for i, momento_str in enumerate(tiempos):
        momento = datetime.fromisoformat(momento_str).replace(tzinfo=timezone.utc)
        existe = (
            db.query(models.LecturaMeteo)
            .filter(models.LecturaMeteo.estacion_id == estacion.id, models.LecturaMeteo.momento == momento)
            .first()
        )
        if existe:
            continue
        lectura = models.LecturaMeteo(
            estacion_id=estacion.id,
            momento=momento,
            temperatura_c=hourly.get("temperature_2m", [None] * len(tiempos))[i],
            humedad_relativa_pct=hourly.get("relative_humidity_2m", [None] * len(tiempos))[i],
            viento_kmh=hourly.get("wind_speed_10m", [None] * len(tiempos))[i],
            precipitacion_mm=hourly.get("precipitation", [None] * len(tiempos))[i],
            radiacion_wm2=hourly.get("shortwave_radiation", [None] * len(tiempos))[i],
            temperatura_suelo_c=hourly.get("soil_temperature_0cm", [None] * len(tiempos))[i],
            eto_mm=eto_hoy,
        )
        db.add(lectura)
        nuevas += 1
    db.commit()
    return nuevas


def correr():
    db = SessionLocal()
    try:
        parcelas = (
            db.query(models.Parcela)
            .filter(models.Parcela.latitud.isnot(None), models.Parcela.longitud.isnot(None))
            .all()
        )
        print(f"Parcelas con coordenadas: {len(parcelas)}")
        for parcela in parcelas:
            lat, lon = float(parcela.latitud), float(parcela.longitud)
            estacion = obtener_o_crear_estacion(db, lat, lon, parcela.nombre)
            datos = traer_datos(lat, lon)
            nuevas = guardar_lecturas(db, estacion, datos)
            print(f"  {parcela.nombre}: {nuevas} lecturas nuevas")
    finally:
        db.close()


if __name__ == "__main__":
    correr()
