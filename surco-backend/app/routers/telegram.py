"""
Integración con Telegram.

Flujo:
1. Creas tu bot con @BotFather en Telegram (te da un TELEGRAM_BOT_TOKEN).
2. Lo pones en tu .env.
3. Le hablas a tu bot: escribe /start y te responde con tu chat_id.
4. Desde la app (ya logueado) llamas POST /telegram/vincular con ese chat_id.
5. Desde ahí, cualquier mensaje que le mandes a tu bot ("Regué el lote norte")
   se guarda como tarea en tu cuenta.

Para conectar Telegram con este servidor hace falta que el backend esté
publicado en una URL https (Telegram no manda mensajes a localhost). Con
Railway/Render basta correr, al desplegar:

  curl "https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=https://TU-DOMINIO/telegram/webhook"
"""

import requests
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app import models, auth

router = APIRouter(prefix="/telegram", tags=["telegram"])

PALABRAS_TIPO = {
    "riego": ["regué", "regue", "riego"],
    "fertilizacion": ["fertilic", "abon"],
    "fitosanitario": ["fumig", "fitosanitario", "plaguicida"],
}


def enviar_mensaje(chat_id: str, texto: str):
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": texto}, timeout=10)


def detectar_tipo(texto: str) -> str:
    texto = texto.lower()
    for tipo, palabras in PALABRAS_TIPO.items():
        if any(p in texto for p in palabras):
            return tipo
    return "otro"


@router.post("/vincular")
def vincular(chat_id: str, db: Session = Depends(get_db), usuario: models.Usuario = Depends(auth.usuario_actual)):
    usuario.telegram_chat_id = str(chat_id)
    db.commit()
    return {"ok": True, "mensaje": "Cuenta de Telegram vinculada"}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Telegram llama a esta URL cada vez que alguien le escribe al bot."""
    update = await request.json()
    mensaje = update.get("message")
    if not mensaje:
        return {"ok": True}

    chat_id = str(mensaje["chat"]["id"])
    texto = mensaje.get("text", "").strip()

    if texto == "/start":
        enviar_mensaje(chat_id, f"Hola 👋 Tu chat_id es: {chat_id}\nPégalo en Surco (Ajustes → Vincular Telegram) para conectar tu cuenta.")
        return {"ok": True}

    usuario = db.query(models.Usuario).filter(models.Usuario.telegram_chat_id == chat_id).first()
    if not usuario:
        enviar_mensaje(chat_id, "Todavía no vinculas tu cuenta. Escribe /start y sigue las instrucciones.")
        return {"ok": True}

    parcelas = db.query(models.Parcela).filter(models.Parcela.usuario_id == usuario.id).all()
    parcela_encontrada = next((p for p in parcelas if p.nombre.lower() in texto.lower()), None)
    if not parcela_encontrada:
        nombres = ", ".join(p.nombre for p in parcelas) or "no tienes parcelas creadas"
        enviar_mensaje(chat_id, f"No reconocí la parcela en tu mensaje. Menciónala por su nombre exacto ({nombres}).")
        return {"ok": True}

    tipo = detectar_tipo(texto)
    from datetime import date
    tarea = models.Tarea(parcela_id=parcela_encontrada.id, titulo=texto, tipo=tipo, fecha=date.today(), hecha=True)
    db.add(tarea)
    db.commit()

    enviar_mensaje(chat_id, f"✅ Registrado en {parcela_encontrada.nombre} como '{tipo}': {texto}")
    return {"ok": True}


@router.get("/configurar-rapido")
def configurar_rapido(nombre: str, email: str, password: str, chat_id: str, db: Session = Depends(get_db)):
    """Atajo pensado para pegar como URL en el navegador (sin Swagger ni curl):
    crea la cuenta si no existe, o solo actualiza el chat_id si el email ya
    estaba registrado, y deja todo vinculado con Telegram en un solo paso."""
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario:
        usuario.telegram_chat_id = str(chat_id)
        db.commit()
        return {"ok": True, "mensaje": f"Cuenta existente '{email}' vinculada a Telegram."}

    usuario = models.Usuario(
        nombre=nombre,
        email=email,
        password_hash=auth.hash_password(password),
        telegram_chat_id=str(chat_id),
    )
    db.add(usuario)
    db.commit()
    return {"ok": True, "mensaje": f"Cuenta '{email}' creada y vinculada a Telegram."}


@router.get("/crear-parcela-rapida")
def crear_parcela_rapida(chat_id: str, nombre: str, area_ha: float = 0, ubicacion: str = "", db: Session = Depends(get_db)):
    """Otro atajo para pegar como URL: crea una parcela usando tu chat_id de
    Telegram para identificar tu cuenta (no hace falta login ni Swagger)."""
    usuario = db.query(models.Usuario).filter(models.Usuario.telegram_chat_id == chat_id).first()
    if not usuario:
        return {"ok": False, "mensaje": "No hay ninguna cuenta vinculada a ese chat_id todavía."}

    parcela = models.Parcela(usuario_id=usuario.id, nombre=nombre, area_ha=area_ha or None, ubicacion=ubicacion or None)
    db.add(parcela)
    db.commit()
    return {"ok": True, "mensaje": f"Parcela '{nombre}' creada para {usuario.email}."}
