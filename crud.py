from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.exc import IntegrityError

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
import models   
import schemas  

logger = logging.getLogger("biblioteca_digital")


# =====================================
# ============ TIPO RECURSO ===========
# =====================================

def create_tipo_recurso(db: Session, data: schemas.TipoRecursoCreate) -> models.TipoRecurso | None:
    tr = models.TipoRecurso(**data.model_dump())
    db.add(tr)
    try:
        db.commit()
        db.refresh(tr)
        return tr
    except IntegrityError:
        db.rollback()
        # ya existe -> None para que el endpoint responda 409
        return None


def list_tipos_recurso(db: Session) -> list[models.TipoRecurso]:
    logger.debug("[crud] Listando tipos de recurso")
    rows = db.execute(
        select(models.TipoRecurso).order_by(models.TipoRecurso.id.desc())
    ).scalars().all()
    logger.info(f"[crud] Se encontraron {len(rows)} tipos de recurso")
    return rows


def get_tipo_recurso(db: Session, tipo_id: int) -> Optional[models.TipoRecurso]:
    logger.debug(f"[crud] Buscando tipo recurso id={tipo_id}")
    tr = db.get(models.TipoRecurso, tipo_id)
    if tr:
        logger.info(f"[crud] Tipo recurso encontrado: {tr.id} - {tr.nombre}")
    else:
        logger.warning(f"[crud] Tipo recurso no encontrado: {tipo_id}")
    return tr


def update_tipo_recurso(db: Session, tipo_id: int, patch: schemas.TipoRecursoUpdate) -> Optional[models.TipoRecurso]:
    logger.debug(f"[crud] Actualizando tipo recurso id={tipo_id} con {patch}")
    tr = db.get(models.TipoRecurso, tipo_id)
    if not tr:
        logger.warning(f"[crud] Tipo recurso a actualizar no encontrado: {tipo_id}")
        return None
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(tr, field, value)
    db.commit()
    db.refresh(tr)
    logger.info(f"[crud] Tipo recurso actualizado: {tr.id} - {tr.nombre}")
    return tr


def delete_tipo_recurso(db: Session, tipo_id: int) -> bool:
    logger.debug(f"[crud] Eliminando tipo recurso id={tipo_id}")
    tr = db.get(models.TipoRecurso, tipo_id)
    if not tr:
        logger.warning(f"[crud] Tipo recurso a eliminar no encontrado: {tipo_id}")
        return False
    # Regla: no eliminar si hay recursos asociados
    vinculados = db.execute(
        select(func.count()).select_from(models.Recurso).where(models.Recurso.tipo_id == tipo_id)
    ).scalar_one()
    if vinculados > 0:
        logger.warning(f"[crud] No se puede eliminar tipo recurso {tipo_id}: {vinculados} recursos asociados")
        return False
    db.delete(tr)
    db.commit()
    logger.info(f"[crud] Tipo recurso eliminado: {tipo_id}")
    return True


# =====================================
# =============== RECURSO =============
# =====================================

def create_recurso(db: Session, data: schemas.RecursoCreate) -> models.Recurso:
    logger.debug(f"[crud] Creando recurso: {data}")

    # Si no llega copias_disponibles, iguala a copias_totales (tu schema ya lo permite)
    payload = data.model_dump()
    if payload.get("copias_disponibles") is None:
        payload["copias_disponibles"] = payload["copias_totales"]

    allowed = {
        "titulo", "autor", "descripcion", "isbn", "is_promoted",
        "copias_totales", "copias_disponibles",
        # incluye solo si EXISTE en tu modelo:
        "tipo_id",       # quítalo si tu tabla no tiene esta FK
        # "tipo",        # descomenta si tu tabla tiene columna 'tipo' texto
    }
    data_for_model = {k: v for k, v in payload.items() if k in allowed}

    rec = models.Recurso(**data_for_model)

    db.add(rec)
    db.commit()
    db.refresh(rec)
    logger.info(f"[crud] Recurso creado: {rec.id} - {rec.titulo}")
    return rec


def list_recursos(
    db: Session,
    q: Optional[str] = None,
    tipo_id: Optional[int] = None,
    solo_promocionados: bool = False
) -> list[models.Recurso]:
    logger.debug("[crud] Listando recursos")
    stmt = select(models.Recurso)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(models.Recurso.titulo).like(like) |
            func.lower(models.Recurso.autor).like(like)
        )
    if tipo_id is not None:
        stmt = stmt.where(models.Recurso.tipo_id == tipo_id)
    if solo_promocionados:
        stmt = stmt.where(models.Recurso.is_promoted.is_(True))

    rows = db.execute(stmt.order_by(models.Recurso.id.desc())).scalars().all()
    logger.info(f"[crud] Se encontraron {len(rows)} recursos")
    return rows


def get_recurso(db: Session, recurso_id: int) -> Optional[models.Recurso]:
    logger.debug(f"[crud] Buscando recurso id={recurso_id}")
    rec = db.get(models.Recurso, recurso_id)
    if rec:
        logger.info(f"[crud] Recurso encontrado: {rec.id} - {rec.titulo}")
    else:
        logger.warning(f"[crud] Recurso no encontrado: {recurso_id}")
    return rec


def update_recurso(db: Session, recurso_id: int, patch: schemas.RecursoUpdate) -> Optional[models.Recurso]:
    logger.debug(f"[crud] Actualizando recurso id={recurso_id} con {patch}")
    rec = db.get(models.Recurso, recurso_id)
    if not rec:
        logger.warning(f"[crud] Recurso a actualizar no encontrado: {recurso_id}")
        return None

    data = patch.model_dump(exclude_unset=True)

    # Regla de negocio: no permitir copias_totales por debajo de préstamos activos
    if "copias_totales" in data:
        activos = rec.copias_totales - rec.copias_disponibles
        if data["copias_totales"] < activos:
            logger.warning(
                f"[crud] Denegado: copias_totales {data['copias_totales']} < préstamos activos {activos}"
            )
            return None
        # Si no envían copias_disponibles, ajusta automáticamente
        if "copias_disponibles" not in data:
            data["copias_disponibles"] = data["copias_totales"] - activos

    # Regla: si envían copias_disponibles explícitas, que no superen las totales (si se conocen)
    if "copias_disponibles" in data:
        tot = data.get("copias_totales", rec.copias_totales)
        if data["copias_disponibles"] > tot:
            logger.warning(
                f"[crud] Denegado: copias_disponibles {data['copias_disponibles']} > copias_totales {tot}"
            )
            return None

    for field, value in data.items():
        setattr(rec, field, value)

    db.commit()
    db.refresh(rec)
    logger.info(f"[crud] Recurso actualizado: {rec.id} - {rec.titulo}")
    return rec


def delete_recurso(db: Session, recurso_id: int) -> bool:
    logger.debug(f"[crud] Eliminando recurso id={recurso_id}")
    rec = db.get(models.Recurso, recurso_id)
    if not rec:
        logger.warning(f"[crud] Recurso a eliminar no encontrado: {recurso_id}")
        return False

    # Bloquea el borrado si hay préstamos activos
    activos = db.execute(
        select(func.count()).select_from(models.Prestamo)
        .where(models.Prestamo.recurso_id == recurso_id)
    ).scalar_one()

    if activos > 0:
        logger.warning(f"[crud] No se puede borrar recurso {recurso_id}: {activos} préstamos activos")
        return False

    db.delete(rec)
    db.commit()
    logger.info(f"[crud] Recurso eliminado: {recurso_id}")
    return True


# =====================================
# ============== PRÉSTAMO =============
# =====================================

def create_prestamo(db: Session, data: schemas.PrestamoCreate) -> Optional[models.Prestamo]:
    logger.debug(f"[crud] Creando préstamo: {data}")
    rec = db.get(models.Recurso, data.recurso_id)
    if not rec:
        logger.warning(f"[crud] Recurso para préstamo no encontrado: {data.recurso_id}")
        return None
    if rec.copias_disponibles <= 0:
        logger.warning("[crud] No hay copias disponibles")
        return None

    # fecha_prestamo por defecto ahora (UTC) si no viene del cliente
    fp = data.fecha_prestamo or datetime.now(timezone.utc)

    p = models.Prestamo(
        recurso_id=data.recurso_id,
        usuario=data.usuario,  # EmailStr ya validado en schema
        fecha_prestamo=fp,
        fecha_vencimiento=data.fecha_vencimiento,
        devuelto=data.devuelto,
    )

    # Actualiza disponibilidad
    rec.copias_disponibles -= 1
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info(f"[crud] Préstamo creado: {p.id} (recurso {p.recurso_id})")
    return p


def list_prestamos(
    db: Session,
    usuario: Optional[str] = None,
    solo_activos: bool = False
) -> list[models.Prestamo]:
    logger.debug("[crud] Listando préstamos")
    stmt = select(models.Prestamo)
    if usuario:
        stmt = stmt.where(models.Prestamo.usuario == usuario)
    if solo_activos:
        stmt = stmt.where(models.Prestamo.devuelto.is_(False))
    rows = db.execute(stmt.order_by(models.Prestamo.id.desc())).scalars().all()
    logger.info(f"[crud] Se encontraron {len(rows)} préstamos")
    return rows


def get_prestamo(db: Session, prestamo_id: int) -> Optional[models.Prestamo]:
    logger.debug(f"[crud] Buscando préstamo id={prestamo_id}")
    p = db.get(models.Prestamo, prestamo_id)
    if p:
        logger.info(f"[crud] Préstamo encontrado: {p.id}")
    else:
        logger.warning(f"[crud] Préstamo no encontrado: {prestamo_id}")
    return p


def devolver_prestamo(db: Session, prestamo_id: int) -> Optional[models.Prestamo]:
    logger.debug(f"[crud] Devolviendo préstamo id={prestamo_id}")
    p = db.get(models.Prestamo, prestamo_id)
    if not p:
        logger.warning(f"[crud] Préstamo a devolver no encontrado: {prestamo_id}")
        return None
    if not p.devuelto:
        p.devuelto = True
        rec = db.get(models.Recurso, p.recurso_id)
        if rec:
            rec.copias_disponibles += 1
        db.commit()
        db.refresh(p)
        logger.info(f"[crud] Préstamo devuelto: {p.id}")
    else:
        logger.info(f"[crud] Préstamo ya estaba devuelto: {p.id}")
    return p


def update_prestamo(db: Session, prestamo_id: int, patch: schemas.PrestamoUpdate) -> Optional[models.Prestamo]:
    logger.debug(f"[crud] Actualizando préstamo id={prestamo_id} con {patch}")
    p = db.get(models.Prestamo, prestamo_id)
    if not p:
        logger.warning(f"[crud] Préstamo a actualizar no encontrado: {prestamo_id}")
        return None

    data = patch.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(p, field, value)

    db.commit()
    db.refresh(p)
    logger.info(f"[crud] Préstamo actualizado: {p.id}")
    return p
