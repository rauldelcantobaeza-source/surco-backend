import uuid
import enum

from sqlalchemy import (
    Column, String, Numeric, Date, Boolean, DateTime, ForeignKey,
    Enum, Text, BigInteger, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def uuid_pk():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Usuario(Base):
    __tablename__ = "usuarios"
    id = uuid_pk()
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    telegram_chat_id = Column(String, unique=True, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    parcelas = relationship("Parcela", back_populates="usuario", cascade="all, delete-orphan")


class Parcela(Base):
    __tablename__ = "parcelas"
    id = uuid_pk()
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    area_ha = Column(Numeric(10, 2))
    ubicacion = Column(String)
    latitud = Column(Numeric(9, 6))
    longitud = Column(Numeric(9, 6))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="parcelas")
    cultivos = relationship("Cultivo", back_populates="parcela", cascade="all, delete-orphan")
    tareas = relationship("Tarea", back_populates="parcela", cascade="all, delete-orphan")
    gastos = relationship("Gasto", back_populates="parcela", cascade="all, delete-orphan")
    fotos = relationship("Foto", back_populates="parcela", cascade="all, delete-orphan")


class EtapaCultivo(str, enum.Enum):
    semilla = "semilla"
    brote = "brote"
    floracion = "floracion"
    cosecha = "cosecha"


class Cultivo(Base):
    __tablename__ = "cultivos"
    id = uuid_pk()
    parcela_id = Column(UUID(as_uuid=True), ForeignKey("parcelas.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    etapa = Column(Enum(EtapaCultivo, name="etapa_cultivo"), nullable=False, default=EtapaCultivo.semilla)
    fecha_siembra = Column(Date)
    fecha_cosecha_est = Column(Date)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    parcela = relationship("Parcela", back_populates="cultivos")


class TipoTarea(str, enum.Enum):
    riego = "riego"
    siembra = "siembra"
    fertilizacion = "fertilizacion"
    cosecha = "cosecha"
    otro = "otro"


class Tarea(Base):
    __tablename__ = "tareas"
    id = uuid_pk()
    parcela_id = Column(UUID(as_uuid=True), ForeignKey("parcelas.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String, nullable=False)
    tipo = Column(Enum(TipoTarea, name="tipo_tarea"), nullable=False, default=TipoTarea.otro)
    fecha = Column(Date, nullable=False)
    hecha = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    parcela = relationship("Parcela", back_populates="tareas")


class CategoriaGasto(str, enum.Enum):
    semillas = "semillas"
    fertilizantes = "fertilizantes"
    fitosanitarios = "fitosanitarios"
    mano_obra = "mano_obra"
    maquinaria = "maquinaria"
    otro = "otro"


class Gasto(Base):
    __tablename__ = "gastos"
    id = uuid_pk()
    parcela_id = Column(UUID(as_uuid=True), ForeignKey("parcelas.id", ondelete="CASCADE"), nullable=False)
    categoria = Column(Enum(CategoriaGasto, name="categoria_gasto"), nullable=False, default=CategoriaGasto.otro)
    monto_clp = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    parcela = relationship("Parcela", back_populates="gastos")


class Foto(Base):
    __tablename__ = "fotos"
    id = uuid_pk()
    parcela_id = Column(UUID(as_uuid=True), ForeignKey("parcelas.id", ondelete="CASCADE"), nullable=False)
    url_imagen = Column(Text, nullable=False)
    caption = Column(Text)
    fecha = Column(Date, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    parcela = relationship("Parcela", back_populates="fotos")


class EstacionMeteo(Base):
    __tablename__ = "estaciones_meteo"
    id = uuid_pk()
    nombre = Column(String, nullable=False)
    fuente = Column(String, nullable=False)  # 'open-meteo' | 'inia'
    latitud = Column(Numeric(9, 6), nullable=False)
    longitud = Column(Numeric(9, 6), nullable=False)


class LecturaMeteo(Base):
    __tablename__ = "lecturas_meteo"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    estacion_id = Column(UUID(as_uuid=True), ForeignKey("estaciones_meteo.id", ondelete="CASCADE"), nullable=False)
    momento = Column(DateTime(timezone=True), nullable=False)
    temperatura_c = Column(Numeric(5, 2))
    humedad_relativa_pct = Column(Numeric(5, 2))
    viento_kmh = Column(Numeric(6, 2))
    precipitacion_mm = Column(Numeric(6, 2))
    radiacion_wm2 = Column(Numeric(7, 2))
    temperatura_suelo_c = Column(Numeric(5, 2))
    eto_mm = Column(Numeric(6, 3))


class FitosanitarioSAG(Base):
    __tablename__ = "fitosanitarios_sag"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre_comercial = Column(Text)
    ingrediente_activo = Column(Text)
    empresa = Column(Text)
    categoria = Column(Text)
    numero_registro = Column(Text)
    vigencia = Column(Text)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now())


class FitosanitarioDetalle(Base):
    """Enriquecimiento agronómico que el propio usuario carga a mano
    (cultivos, plagas, modo de uso, modo de acción, carencia, reingreso,
    banda toxicológica) — no viene en ningún archivo público del SAG."""
    __tablename__ = "fitosanitarios_detalle"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    numero_registro = Column(Text, nullable=False, unique=True)
    cultivos = Column(Text)
    plagas = Column(Text)
    modo_uso = Column(String)         # foliar | riego | ambos | semilla
    modo_accion = Column(Text)
    carencia_dias = Column(Numeric(4, 0))
    reingreso_horas = Column(Numeric(5, 0))
    banda_toxicologica = Column(String)  # rojo | naranja | amarillo | azul
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
