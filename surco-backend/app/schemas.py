import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Usuarios / Auth ----------
class UsuarioCrear(BaseModel):
    nombre: str
    email: EmailStr
    password: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Parcelas ----------
class ParcelaCrear(BaseModel):
    nombre: str
    area_ha: Optional[float] = None
    ubicacion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class ParcelaOut(ParcelaCrear):
    model_config
