"""
Endpoint de migración "de un solo uso": agrega las columnas nuevas a la
tabla 'cultivos' que ya existe en tu Postgres, sin borrar ningún dato.
Se pega como URL en el navegador, igual que los otros atajos.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/migrar")
def migrar(db: Session = Depends(get_db)):
    sentencias = [
        "ALTER TABLE cultivos ADD COLUMN IF NOT EXISTS crop_key TEXT",
        "ALTER TABLE cultivos ADD COLUMN IF NOT EXISTS numero_plantas BIGINT DEFAULT 0",
        "ALTER TABLE cultivos ADD COLUMN IF NOT EXISTS marco_plantacion TEXT",
        "ALTER TABLE cultivos ADD COLUMN IF NOT EXISTS rendimiento_kg_m2_custom NUMERIC(6,2)",
    ]
    ejecutadas = []
    for s in sentencias:
        db.execute(text(s))
        ejecutadas.append(s)
    db.commit()
    return {"ok": True, "mensaje": "Migración aplicada.", "sentencias": ejecutadas}
