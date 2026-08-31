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
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Cultivos ----------
class CultivoCrear(BaseModel):
    parcela_id: uuid.UUID
    nombre: str
    etapa: Optional[str] = "semilla"
    fecha_siembra: Optional[date] = None
    fecha_cosecha_est: Optional[date] = None
    crop_key: Optional[str] = None
    numero_plantas: Optional[int] = 0
    marco_plantacion: Optional[str] = None
    rendimiento_kg_m2_custom: Optional[float] = None


class CultivoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    parcela_id: uuid.UUID
    nombre: str
    etapa: str
    fecha_siembra: Optional[date]
    fecha_cosecha_est: Optional[date]
    crop_key: Optional[str] = None
    numero_plantas: Optional[int] = 0
    marco_plantacion: Optional[str] = None
    rendimiento_kg_m2_custom: Optional[float] = None


# ---------- Manejos ----------
class ManejoCrear(BaseModel):
    cultivo_id: uuid.UUID
    fecha: date
    tipo: Optional[str] = "otro"
    producto: Optional[str] = None
    dosis: Optional[str] = None
    cantidad: Optional[str] = None
    valor: Optional[float] = None
    notas: Optional[str] = None


class ManejoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cultivo_id: uuid.UUID
    fecha: date
    tipo: str
    producto: Optional[str]
    dosis: Optional[str]
    cantidad: Optional[str]
    valor: Optional[float]
    notas: Optional[str]


# ---------- Tareas ----------
class TareaCrear(BaseModel):
    parcela_id: uuid.UUID
    titulo: str
    tipo: Optional[str] = "otro"
    fecha: date
    hecha: Optional[bool] = False


class TareaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    parcela_id: uuid.UUID
    titulo: str
    tipo: str
    fecha: date
    hecha: bool


# ---------- Gastos ----------
class GastoCrear(BaseModel):
    parcela_id: uuid.UUID
    categoria: Optional[str] = "otro"
    monto_clp: float
    fecha: date
    descripcion: Optional[str] = None


class GastoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    parcela_id: uuid.UUID
    categoria: str
    monto_clp: float
    fecha: date
    descripcion: Optional[str]


# ---------- Fotos ----------
class FotoCrear(BaseModel):
    parcela_id: uuid.UUID
    url_imagen: str
    caption: Optional[str] = None
    fecha: date


class FotoOut(FotoCrear):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Clima ----------
class LecturaMeteoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    momento: datetime
    temperatura_c: Optional[float]
    humedad_relativa_pct: Optional[float]
    viento_kmh: Optional[float]
    precipitacion_mm: Optional[float]
    radiacion_wm2: Optional[float]
    temperatura_suelo_c: Optional[float]
    eto_mm: Optional[float]


# ---------- Fitosanitarios ----------
class FitosanitarioSAGOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_comercial: Optional[str]
    ingrediente_activo: Optional[str]
    empresa: Optional[str]
    categoria: Optional[str]
    numero_registro: Optional[str]
    vigencia: Optional[str]


class FitosanitarioDetalleIn(BaseModel):
    numero_registro: str
    cultivos: Optional[str] = None
    plagas: Optional[str] = None
    modo_uso: Optional[str] = None
    modo_accion: Optional[str] = None
    carencia_dias: Optional[int] = None
    reingreso_horas: Optional[int] = None
    banda_toxicologica: Optional[str] = None


class FitosanitarioDetalleOut(FitosanitarioDetalleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
