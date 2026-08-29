import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/cultivos", tags=["cultivos"])


def _verificar_parcela(db: Session, usuario: models.Usuario, parcela_id: uuid.UUID):
    parcela = (
        db.query(models.Parcela)
        .filter(models.Parcela.id == parcela_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")


@router.get("", response_model=list[schemas.CultivoOut])
def listar(parcela_id: uuid.UUID | None = None, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    q = db.query(models.Cultivo).join(models.Parcela).filter(models.Parcela.usuario_id == usuario.id)
    if parcela_id:
        q = q.filter(models.Cultivo.parcela_id == parcela_id)
    return q.all()


@router.post("", response_model=schemas.CultivoOut, status_code=201)
def crear(datos: schemas.CultivoCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    _verificar_parcela(db, usuario, datos.parcela_id)
    cultivo = models.Cultivo(**datos.model_dump())
    db.add(cultivo)
    db.commit()
    db.refresh(cultivo)
    return cultivo


@router.patch("/{cultivo_id}/avanzar-etapa", response_model=schemas.CultivoOut)
def avanzar_etapa(cultivo_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    orden = ["semilla", "brote", "floracion", "cosecha"]
    cultivo = (
        db.query(models.Cultivo)
        .join(models.Parcela)
        .filter(models.Cultivo.id == cultivo_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not cultivo:
        raise HTTPException(status_code=404, detail="Cultivo no encontrado")
    idx = orden.index(cultivo.etapa.value if hasattr(cultivo.etapa, "value") else cultivo.etapa)
    cultivo.etapa = orden[min(idx + 1, len(orden) - 1)]
    db.commit()
    db.refresh(cultivo)
    return cultivo


@router.delete("/{cultivo_id}", status_code=204)
def eliminar(cultivo_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    cultivo = (
        db.query(models.Cultivo)
        .join(models.Parcela)
        .filter(models.Cultivo.id == cultivo_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not cultivo:
        raise HTTPException(status_code=404, detail="Cultivo no encontrado")
    db.delete(cultivo)
    db.commit()
