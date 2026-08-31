import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/manejos", tags=["manejos"])


def _cultivo_del_usuario(db: Session, usuario: models.Usuario, cultivo_id: uuid.UUID) -> models.Cultivo:
    cultivo = (
        db.query(models.Cultivo)
        .join(models.Parcela)
        .filter(models.Cultivo.id == cultivo_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not cultivo:
        raise HTTPException(status_code=404, detail="Cultivo no encontrado")
    return cultivo


@router.get("", response_model=list[schemas.ManejoOut])
def listar(cultivo_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    _cultivo_del_usuario(db, usuario, cultivo_id)
    return db.query(models.Manejo).filter(models.Manejo.cultivo_id == cultivo_id).order_by(models.Manejo.fecha.desc()).all()


@router.post("", response_model=schemas.ManejoOut, status_code=201)
def crear(datos: schemas.ManejoCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    cultivo = _cultivo_del_usuario(db, usuario, datos.cultivo_id)
    manejo = models.Manejo(**datos.model_dump())
    db.add(manejo)

    # Si tiene valor, se registra automáticamente como gasto de la parcela.
    if datos.valor and datos.valor > 0:
        categoria = "fertilizantes" if datos.tipo == "fertilizante" else "fitosanitarios" if datos.tipo == "fitosanitario" else "otro"
        gasto = models.Gasto(
            parcela_id=cultivo.parcela_id,
            categoria=categoria,
            monto_clp=datos.valor,
            fecha=datos.fecha,
            descripcion=f"{datos.producto or 'Manejo'}{f' ({datos.cantidad})' if datos.cantidad else ''} — {cultivo.nombre}",
        )
        db.add(gasto)

    db.commit()
    db.refresh(manejo)
    return manejo


@router.delete("/{manejo_id}", status_code=204)
def eliminar(manejo_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    manejo = (
        db.query(models.Manejo)
