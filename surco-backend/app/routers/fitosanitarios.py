from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/fitosanitarios", tags=["fitosanitarios"])


@router.get("", response_model=list[schemas.FitosanitarioSAGOut])
def buscar(
    q: str = Query("", description="Texto a buscar en nombre, ingrediente activo o empresa"),
    limite: int = 100,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(auth.usuario_actual),
):
    query = db.query(models.FitosanitarioSAG)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.FitosanitarioSAG.nombre_comercial.ilike(like),
                models.FitosanitarioSAG.ingrediente_activo.ilike(like),
                models.FitosanitarioSAG.empresa.ilike(like),
            )
        )
    return query.limit(limite).all()


@router.get("/detalle/{numero_registro}", response_model=schemas.FitosanitarioDetalleOut | None)
def obtener_detalle(numero_registro: str, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    return (
        db.query(models.FitosanitarioDetalle)
        .filter(models.FitosanitarioDetalle.numero_registro == numero_registro)
        .first()
    )


@router.put("/detalle", response_model=schemas.FitosanitarioDetalleOut)
def guardar_detalle(datos: schemas.FitosanitarioDetalleIn, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    """Crea o actualiza el detalle agronómico manual de un producto (cultivos,
    plagas, modo de uso, modo de acción, carencia, reingreso, banda toxicológica).
    Es información compartida entre todos los usuarios de la app: una vez que
    alguien la carga para un producto, todos se benefician de ella."""
    existente = (
        db.query(models.FitosanitarioDetalle)
        .filter(models.FitosanitarioDetalle.numero_registro == datos.numero_registro)
        .first()
    )
    if existente:
        for campo, valor in datos.model_dump().items():
            setattr(existente, campo, valor)
        db.commit()
        db.refresh(existente)
        return existente

    nuevo = models.FitosanitarioDetalle(**datos.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
