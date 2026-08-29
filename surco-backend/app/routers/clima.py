import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/clima", tags=["clima"])


@router.get("/parcela/{parcela_id}", response_model=list[schemas.LecturaMeteoOut])
def lecturas_de_parcela(
    parcela_id: uuid.UUID,
    limite: int = 120,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(auth.usuario_actual),
):
    parcela = db.query(models.Parcela).filter(models.Parcela.id == parcela_id, models.Parcela.usuario_id == usuario.id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    if parcela.latitud is None or parcela.longitud is None:
        raise HTTPException(status_code=400, detail="Esta parcela no tiene latitud/longitud configurada")

    # Redondeamos a 3 decimales (~100 m) para calzar con lo que crea el job de ingesta.
    estacion = (
        db.query(models.EstacionMeteo)
        .filter(
            models.EstacionMeteo.latitud == round(float(parcela.latitud), 3),
            models.EstacionMeteo.longitud == round(float(parcela.longitud), 3),
        )
        .first()
    )
    if not estacion:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay lecturas para esta parcela. Se llenan cuando corre el job de ingesta (ver app/jobs/ingest_open_meteo.py).",
        )

    return (
        db.query(models.LecturaMeteo)
        .filter(models.LecturaMeteo.estacion_id == estacion.id)
        .order_by(models.LecturaMeteo.momento.desc())
        .limit(limite)
        .all()
    )
