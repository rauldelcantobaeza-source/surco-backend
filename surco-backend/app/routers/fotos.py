import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/fotos", tags=["fotos"])

# Nota: este endpoint espera que el CLIENTE ya haya subido la imagen a un bucket
# (S3 / Cloudflare R2 / Supabase Storage) y solo mande la URL resultante.
# La subida real al bucket normalmente se hace con una "presigned URL" que
# el backend genera en un endpoint aparte (no incluido aquí para no atarte
# a un proveedor específico) — cualquiera de los tres tiene un ejemplo
# de 10 líneas en su documentación para esto.


@router.get("", response_model=list[schemas.FotoOut])
def listar(parcela_id: uuid.UUID | None = None, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    q = db.query(models.Foto).join(models.Parcela).filter(models.Parcela.usuario_id == usuario.id)
    if parcela_id:
        q = q.filter(models.Foto.parcela_id == parcela_id)
    return q.order_by(models.Foto.fecha.desc()).all()


@router.post("", response_model=schemas.FotoOut, status_code=201)
def crear(datos: schemas.FotoCrear, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    parcela = db.query(models.Parcela).filter(models.Parcela.id == datos.parcela_id, models.Parcela.usuario_id == usuario.id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    foto = models.Foto(**datos.model_dump())
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


@router.delete("/{foto_id}", status_code=204)
def eliminar(foto_id: uuid.UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    foto = (
        db.query(models.Foto)
        .join(models.Parcela)
        .filter(models.Foto.id == foto_id, models.Parcela.usuario_id == usuario.id)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    db.delete(foto)
    db.commit()
