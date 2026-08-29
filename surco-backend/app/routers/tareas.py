import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/tareas", tags=["tareas"])


@router.get("", response_model=list[schemas.TareaOut])
def listar(parcela_id: uuid.UUID | None = None, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    q = db.query(models.Tarea).join(models.Parcela).filter(models.Parcela.usuario_id == usuario.id)
    if parcela_id:
        q = q.filter(models.Tarea.parcela_id == parcela_id)
    return q.order_by(models.Tarea.fecha).all()


@router.post("", response_model=schemas.TareaOut, status_code=201)
def crear(datos: schemas.TareaCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    parcela = db.query(models.Parcela).filter(models.Parcela.id == datos.parcela_id, models.Parcela.usuario_id == usuario.id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    tarea = models.Tarea(**datos.model_dump())
    db.add(tarea)
    db.commit()
    db.refresh(tarea)
    return tarea


@router.patch("/{tarea_id}/toggle", response_model=schemas.TareaOut)
def toggle(tarea_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    tarea = (
        db.query(models.Tarea)
        .join(models.Parcela)
        .filter(models.Tarea.id == tarea_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    tarea.hecha = not tarea.hecha
    db.commit()
    db.refresh(tarea)
    return tarea


@router.delete("/{tarea_id}", status_code=204)
def eliminar(tarea_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    tarea = (
        db.query(models.Tarea)
        .join(models.Parcela)
        .filter(models.Tarea.id == tarea_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(tarea)
    db.commit()
