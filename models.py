from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, String, Text, Column, ForeignKey, Boolean, DateTime
from datetime import datetime, timezone


class DecBase(DeclarativeBase):
    pass

class TipoRecurso(DecBase):
    __tablename__ = "tipos_recurso"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, default="")

    # Relación uno-a-muchos con Recurso
    recursos = relationship("Recurso", back_populates="tipo_recurso")

class Recurso(DecBase):
    __tablename__ = "recursos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    autor = Column(String(100), nullable=True)
    descripcion = Column(Text, default="")
    isbn = Column(String(20), nullable=True)
    copias_totales = Column(Integer, default=1)
    copias_disponibles = Column(Integer, default=1)
    is_promoted = Column(Boolean, default=False) # revisar si quiero tenerlo, puede ser interesante para tarea asincrona

    # Relación con TipoRecurso
    tipo_id = Column(Integer, ForeignKey("tipos_recurso.id"), nullable=True)
    tipo_recurso = relationship("TipoRecurso", back_populates="recursos")

    # Relación con Préstamos
    prestamos = relationship("Prestamo", back_populates="recurso")

class Prestamo(DecBase):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(120), nullable=False)
    fecha_prestamo = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    devuelto = Column(Boolean, default=False)

    # Clave foránea a recurso
    recurso_id = Column(Integer, ForeignKey("recursos.id"), nullable=False)
    recurso = relationship("Recurso", back_populates="prestamos")

    