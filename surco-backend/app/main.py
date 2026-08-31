from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth_router, parcelas, cultivos, tareas, gastos, fotos, clima, fitosanitarios, telegram, admin, manejos

# Para un proyecto en marcha usa Alembic (migraciones versionadas) en vez de
# create_all. Se deja así para que puedas arrancar de inmediato.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Surco API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(parcelas.router)
app.include_router(cultivos.router)
app.include_router(tareas.router)
app.include_router(gastos.router)
app.include_router(fotos.router)
app.include_router(clima.router)
app.include_router(fitosanitarios.router)
app.include_router(telegram.router)
app.include_router(admin.router)
app.include_router(manejos.router)


@app.get("/salud")
def salud():
    return {"ok": True}
