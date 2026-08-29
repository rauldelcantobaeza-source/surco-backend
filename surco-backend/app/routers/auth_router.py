from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=schemas.Token)
def registro(datos: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")

    usuario = models.Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=auth.hash_password(datos.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"access_token": auth.crear_token(str(usuario.id))}


@router.post("/login", response_model=schemas.Token)
def login(datos: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario or not auth.verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")
    return {"access_token": auth.crear_token(str(usuario.id))}


@router.get("/yo", response_model=schemas.UsuarioOut)
def yo(usuario: models.Usuario = Depends(auth.usuario_actual)):
    return usuario
