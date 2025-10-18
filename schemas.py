from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, constr, conint, field_validator, model_validator



class TipoRecursoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=1000)

class TipoRecursoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=1000)


class RecursoCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    autor: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=1000)
    # NOTA: tipo es str (no enum) para que NO aparezca como enum en Swagger
    tipo: Optional[str] = Field(None, min_length=1, max_length=50)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    copias_totales: int = Field(..., ge=1, le=999)
    copias_disponibles: Optional[int] = Field(None, ge=0, le=999)
    is_promoted: bool = False
    tipo_id: Optional[int] = None  # si usas también la FK numérica

    @field_validator("tipo")
    @classmethod
    def validar_tipo_existente(cls, v: str):
        # Validación dinámica contra la BD (sin enum en Swagger)
        from bbdd import SessionLocal
        from models import TipoRecurso
        with SessionLocal() as db:
            if not db.query(TipoRecurso).filter_by(nombre=v).first():
                raise ValueError(f"Tipo de recurso '{v}' no existe")
        return v
    
    @field_validator("copias_disponibles")
    @classmethod
    def validar_disponibles_vs_totales(cls, v: Optional[int], info):
        # Si no envían 'copias_disponibles', se deja como None
        # y lo puedes setear en el endpoint = copias_totales.
        if v is None:
            return v
        # Accedemos a otros campos con info.data
        totales = info.data.get("copias_totales")
        if totales is not None and v > totales:
            raise ValueError("copias_disponibles no puede exceder copias_totales")
        return v

class RecursoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    autor: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=1000)
    tipo: Optional[str] = Field(None, min_length=1, max_length=50)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    copias_totales: Optional[int] = Field(None, ge=1, le=999)
    copias_disponibles: Optional[int] = Field(None, ge=0, le=999)
    is_promoted: Optional[bool] = None
    tipo_id: Optional[int] = None

    @field_validator("tipo")
    @classmethod
    def validar_tipo_existente_update(cls, v: Optional[str]):
        if v is None:
            return v
        from bbdd import SessionLocal
        from models import TipoRecurso
        with SessionLocal() as db:
            if not db.query(TipoRecurso).filter_by(nombre=v).first():
                raise ValueError(f"Tipo de recurso '{v}' no existe")
        return v

    

class PrestamoCreate(BaseModel):
    recurso_id: int = Field(..., ge=1)
    usuario: EmailStr
    fecha_prestamo: Optional[datetime] = None
    fecha_vencimiento: datetime
    devuelto: bool = False

    # Validación simple: vencimiento después de préstamo (si no llega, se setea en endpoint)
    @field_validator("fecha_vencimiento")
    @classmethod
    def validar_fechas(cls, fv: datetime, info):
        fp = info.data.get("fecha_prestamo")
        if fp is not None and fv <= fp:
            raise ValueError("fecha_vencimiento debe ser posterior a fecha_prestamo")
        return fv


class PrestamoUpdate(BaseModel):
    fecha_vencimiento: Optional[datetime] = None
    devuelto: Optional[bool] = None
