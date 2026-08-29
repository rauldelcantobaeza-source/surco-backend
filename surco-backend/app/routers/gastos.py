import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/gastos", tags=["gastos"])


@router.get("", response_model=list[schemas.GastoOut])
def listar(parcela_id: uuid.UUID | None = None, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    q = db.query(models.Gasto).join(models.Parcela).filter(models.Parcela.usuario_id == usuario.id)
    if parcela_id:
        q = q.filter(models.Gasto.parcela_id == parcela_id)
    return q.order_by(models.Gasto.fecha.desc()).all()


@router.post("", response_model=schemas.GastoOut, status_code=201)
def crear(datos: schemas.GastoCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    parcela = db.query(models.Parcela).filter(models.Parcela.id == datos.parcela_id, models.Parcela.usuario_id == usuario.id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    gasto = models.Gasto(**datos.model_dump())
    db.add(gasto)
    db.commit()
    db.refresh(gasto)
    return gasto


@router.delete("/{gasto_id}", status_code=204)
def eliminar(gasto_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    gasto = (
        db.query(models.Gasto)
        .join(models.Parcela)
        .filter(models.Gasto.id == gasto_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(gasto)
    db.commit()
