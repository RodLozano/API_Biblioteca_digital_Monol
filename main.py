import logging
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from bbdd import SessionLocal, engine
from models import DecBase
import models

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

import crud
import schemas as schemas


# Configuración de logging
logger = logging.getLogger("biblioteca_digital")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    log_format = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

    # Consola (DEBUG+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # Carpeta de logs opcional
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Archivo debug.log (DEBUG+)
    debug_file = logging.FileHandler(logs_dir / "debug.log", encoding="utf-8")
    debug_file.setLevel(logging.DEBUG)
    debug_file.setFormatter(log_format)
    logger.addHandler(debug_file)

    # Archivo warning.log (WARNING+)
    warning_file = logging.FileHandler(logs_dir / "warning.log", encoding="utf-8")
    warning_file.setLevel(logging.WARNING)
    warning_file.setFormatter(log_format)
    logger.addHandler(warning_file)


app = FastAPI(title="Biblioteca Digital API")
logger.info("FastAPI app initialized")


@app.on_event("startup")
def on_startup() -> None:
    try:
        DecBase.metadata.create_all(bind=engine)
        logger.debug("Database tables created (if not exist)")
        # Sondeo rápido de conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except SQLAlchemyError as e:
        logger.exception("Database initialization error: %s", e)
        # Nota: no hacemos raise para que Uvicorn no entre en bucle;
        # si quieres abortar el start, puedes relanzar la excepción.


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Helper de salida ----------------
def _tipo_to_dict(tr) -> dict:
    return {
        "id": tr.id,
        "nombre": tr.nombre,
        "descripcion": tr.descripcion,
    }


# ------------------------ ENDPOINTS: /tipos ------------------------

# GET /tipos?search=
@app.get("/tipos", status_code=200, tags=["Tipos de recurso"])
def list_tipos_recurso(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    logger.debug("[api] GET /tipos")
    rows = crud.list_tipos_recurso(db)
    if search:
        s = search.lower()
        rows = [r for r in rows if s in (r.nombre or "").lower() or s in (r.descripcion or "").lower()]
    return [_tipo_to_dict(r) for r in rows]

# POST /tipos
@app.post("/tipos", status_code=201, tags=["Tipos de recurso"])
def create_tipo_recurso(body: schemas.TipoRecursoCreate, db: Session = Depends(get_db)):
    tr = crud.create_tipo_recurso(db, body)
    if tr is None:
        raise HTTPException(status_code=409, detail="El tipo de recurso ya existe")
    return {"id": tr.id, "nombre": tr.nombre, "descripcion": tr.descripcion}

# GET /tipos/{tipo_id}
@app.get("/tipos/{tipo_id}", status_code=200, tags=["Tipos de recurso"])
def get_tipo_recurso(
    tipo_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] GET /tipos/{tipo_id}")
    tr = crud.get_tipo_recurso(db, tipo_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Tipo de recurso no encontrado")
    return _tipo_to_dict(tr)

# PUT /tipos/{tipo_id}
@app.put("/tipos/{tipo_id}", status_code=200, tags=["Tipos de recurso"])
def update_tipo_recurso(
    tipo_id: int,
    body: schemas.TipoRecursoUpdate,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] PUT /tipos/{tipo_id} body={body}")
    tr = crud.update_tipo_recurso(db, tipo_id, body)
    if not tr:
        raise HTTPException(status_code=404, detail="Tipo de recurso no encontrado o no actualizado")
    return _tipo_to_dict(tr)

# ---------------- Helper de salida ----------------
def _recurso_to_dict(r: models.Recurso) -> dict:
    return {
        "id": r.id,
        "titulo": r.titulo,
        "autor": r.autor,
        "descripcion": r.descripcion,
        "isbn": r.isbn,
        "is_promoted": r.is_promoted,
        "copias_totales": r.copias_totales,
        "copias_disponibles": r.copias_disponibles,
        "tipo_id": getattr(r, "tipo_id", None),   # si usas FK
        # "tipo": getattr(r, "tipo", None),       # descomenta si tienes columna de texto
    }

# ------------------------ ENDPOINTS: /recursos ------------------------

# GET /recursos?q=&tipo_id=&solo_promocionados=
@app.get("/recursos", status_code=200, tags=["Recursos"])
def list_recursos(
    q: Optional[str] = None,
    tipo_id: Optional[int] = None,
    solo_promocionados: bool = False,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] GET /recursos q={q} tipo_id={tipo_id} promo={solo_promocionados}")
    rows = crud.list_recursos(db, q=q, tipo_id=tipo_id, solo_promocionados=solo_promocionados)
    return [_recurso_to_dict(r) for r in rows]

# POST /recursos
@app.post("/recursos", status_code=status.HTTP_201_CREATED, tags=["Recursos"])
def create_recurso(
    body: schemas.RecursoCreate,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] POST /recursos body={body}")
    rec = crud.create_recurso(db, body)
    return _recurso_to_dict(rec)

# GET /recursos/{recurso_id}
@app.get("/recursos/{recurso_id}", status_code=200, tags=["Recursos"])
def get_recurso(
    recurso_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] GET /recursos/{recurso_id}")
    rec = crud.get_recurso(db, recurso_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return _recurso_to_dict(rec)

# PUT /recursos/{recurso_id}
@app.put("/recursos/{recurso_id}", status_code=200, tags=["Recursos"])
def update_recurso(
    recurso_id: int,
    body: schemas.RecursoUpdate,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] PUT /recursos/{recurso_id} body={body}")
    rec = crud.update_recurso(db, recurso_id, body)
    if not rec:
        # Puede ser que no exista o que se haya bloqueado por reglas de negocio (copias vs préstamos)
        raise HTTPException(status_code=409, detail="No se pudo actualizar el recurso")
    return _recurso_to_dict(rec)



# ---------------- Helper de salida ----------------
def _prestamo_to_dict(p: models.Prestamo) -> dict:
    return {
        "id": p.id,
        "recurso_id": p.recurso_id,
        "usuario": p.usuario,
        "fecha_prestamo": p.fecha_prestamo,
        "fecha_vencimiento": p.fecha_vencimiento,
        "devuelto": p.devuelto,
    }

# ---------------------- ENDPOINTS: /prestamos ----------------------

# GET /prestamos?usuario=&solo_activos=
@app.get("/prestamos", status_code=200, tags=["Préstamos"])
def list_prestamos(
    usuario: Optional[str] = None,
    solo_activos: bool = False,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] GET /prestamos usuario={usuario} solo_activos={solo_activos}")
    rows = crud.list_prestamos(db, usuario=usuario, solo_activos=solo_activos)
    return [_prestamo_to_dict(p) for p in rows]

# POST /prestamos
@app.post("/prestamos", status_code=status.HTTP_201_CREATED, tags=["Préstamos"])
def create_prestamo(
    body: schemas.PrestamoCreate,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] POST /prestamos body={body}")
    p = crud.create_prestamo(db, body)
    if not p:
        # razones típicas: recurso inexistente o sin copias
        raise HTTPException(status_code=409, detail="No se pudo crear el préstamo (recurso inexistente o sin copias)")
    return _prestamo_to_dict(p)

# GET /prestamos/{prestamo_id}
@app.get("/prestamos/{prestamo_id}", status_code=200, tags=["Préstamos"])
def get_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] GET /prestamos/{prestamo_id}")
    p = crud.get_prestamo(db, prestamo_id)
    if not p:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return _prestamo_to_dict(p)

# PUT /prestamos/{prestamo_id}/devolucion
@app.put("/prestamos/{prestamo_id}/devolucion", status_code=200, tags=["Préstamos"])
def devolver_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] PUT /prestamos/{prestamo_id}/devolucion")
    p = crud.devolver_prestamo(db, prestamo_id)
    if not p:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return _prestamo_to_dict(p)

# PUT /prestamos/{prestamo_id}   (actualización parcial: fecha_vencimiento / devuelto)
@app.put("/prestamos/{prestamo_id}", status_code=200, tags=["Préstamos"])
def update_prestamo(
    prestamo_id: int,
    body: schemas.PrestamoUpdate,
    db: Session = Depends(get_db),
):
    logger.debug(f"[api] PUT /prestamos/{prestamo_id} body={body}")
    p = crud.update_prestamo(db, prestamo_id, body)
    if not p:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado o no actualizado")
    return _prestamo_to_dict(p)