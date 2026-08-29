import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/parcelas", tags=["parcelas"])


def _obtener_o_404(db: Session, usuario: models.Usuario, parcela_id: uuid.UUID) -> models.Parcela:
    parcela = (
        db.query(models.Parcela)
        .filter(models.Parcela.id == parcela_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@router.get("", response_model=list[schemas.ParcelaOut])
def listar(db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    return db.query(models.Parcela).filter(models.Parcela.usuario_id == usuario.id).all()


@router.post("", response_model=schemas.ParcelaOut, status_code=201)
def crear(datos: schemas.ParcelaCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    parcela = models.Parcela(usuario_id=usuario.id, **datos.model_dump())
    db.add(parcela)
    db.commit()
    db.refresh(parcela)
    return parcela


@router.delete("/{parcela_id}", status_code=204)
def eliminar(parcela_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    parcela = _obtener_o_404(db, usuario, parcela_id)
    db.delete(parcela)
    db.commit()
