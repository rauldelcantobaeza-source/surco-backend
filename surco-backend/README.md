# Surco — Backend

API real para la app Surco: parcelas, cultivos, tareas, gastos, fotos,
agrometeorología (Open-Meteo) y fitosanitarios (planilla oficial del SAG +
tu propio detalle agronómico).

## 1. Levantar la base de datos

```bash
docker compose up -d
```

Esto levanta Postgres en `localhost:5432` con usuario/clave `surco`/`surco`.

## 2. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y ajusta JWT_SECRET al menos
```

## 3. Levantar la API

```bash
uvicorn app.main:app --reload
```

Documentación interactiva automática en `http://localhost:8000/docs`.

Al arrancar por primera vez, la API crea todas las tablas del esquema
automáticamente (`Base.metadata.create_all`). Para un proyecto que ya está
en producción, conviene migrar a **Alembic** para tener migraciones
versionadas en vez de esto.

## 4. Probar rápido

```bash
# Crear usuario
curl -X POST localhost:8000/auth/registro -H "Content-Type: application/json" \
  -d '{"nombre":"Test","email":"test@test.com","password":"12345678"}'

# Guarda el access_token que te devuelve, y úsalo así:
curl localhost:8000/parcelas -H "Authorization: Bearer TU_TOKEN"
```

## 5. Jobs de ingesta automatizados

Estos dos scripts alimentan la app con datos externos. Se corren con cron
(o cualquier programador de tareas del hosting que uses — Railway y Render
tienen "cron jobs" nativos).

```bash
# Agrometeorología (Open-Meteo) — sugerido cada 1 hora
python -m app.jobs.ingest_open_meteo

# Planilla de fitosanitarios del SAG — sugerido 1 vez por semana
python -m app.jobs.ingest_sag
```

Ejemplo de crontab:

```cron
0 * * * *  cd /ruta/al/backend && venv/bin/python -m app.jobs.ingest_open_meteo >> logs/clima.log 2>&1
0 6 * * 1  cd /ruta/al/backend && venv/bin/python -m app.jobs.ingest_sag >> logs/sag.log 2>&1
```

**Importante sobre `ingest_sag.py`**: la primera vez que lo corras, revisa el
mensaje de columnas faltantes que imprime — el SAG puede nombrar los
encabezados de la planilla distinto a lo que se supuso en `MAPEO_COLUMNAS`.
Ajusta ese diccionario una vez y no lo vuelves a tocar.

## 6. Conectar el frontend

Reemplaza las llamadas a `window.storage` de la app (surco-app.jsx) por
llamadas `fetch` a esta API, por ejemplo:

```js
const res = await fetch(`${API_URL}/parcelas`, {
  headers: { Authorization: `Bearer ${token}` },
});
const parcelas = await res.json();
```

## 7. Sobre lo que NO está en este backend todavía

- **Subida real de fotos a un bucket** (S3/R2/Supabase Storage): el endpoint
  `/fotos` ya está listo para recibir la URL final, pero la subida del
  archivo en sí depende del proveedor que elijas — todos tienen un ejemplo
  de "presigned URL" de ~10 líneas en su documentación.
- **Acceso a agrometeorologia.cl (INIA)**: no tienen API pública y su
  `robots.txt` bloquea el acceso automatizado. El job usa Open-Meteo como
  fuente equivalente mientras tanto. Si consiguen un acuerdo formal de datos
  con INIA, se agrega como una segunda fuente en `estaciones_meteo.fuente`.
