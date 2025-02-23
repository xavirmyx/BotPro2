from telethon import TelegramClient, events
import asyncio
import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from db import get_db_connection

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener variables de entorno
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, CHAT_ID, BOT_TOKEN]):
    raise ValueError("Faltan variables de entorno necesarias (API_ID, API_HASH, CHAT_ID, BOT_TOKEN)")

# Inicializar el cliente de Telegram
client = TelegramClient('userbot', API_ID, API_HASH)

# Manejador para solicitudes '#Solicito'
@client.on(events.NewMessage(pattern=r'#Solicito (.+)', chats=CHAT_ID))
async def handle_solicito(event):
    try:
        user_id = event.sender_id
        solicitud = event.pattern_match.group(1)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM solicitudes WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '1 day'", (user_id,))
                count = cur.fetchone()[0]
                if count >= 3:
                    await event.reply("❌ Has alcanzado el límite de 3 solicitudes diarias.")
                    return
                cur.execute("INSERT INTO solicitudes (user_id, solicitud, estado) VALUES (%s, %s, %s)", (user_id, solicitud, 'pendiente'))
                conn.commit()
                await event.reply(f"✅ Solicitud recibida: '{solicitud}'. ¡Gracias!")
    except Exception as e:
        await event.reply(f"Error al procesar la solicitud: {str(e)}")
        logger.error(f"Error en handle_solicito: {str(e)}")

# Manejador para eliminar solicitudes '#Eliminar'
@client.on(events.NewMessage(pattern=r'#Eliminar (.+)', chats=CHAT_ID))
async def handle_eliminar(event):
    try:
        user_id = event.sender_id
        solicitud = event.pattern_match.group(1)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM solicitudes WHERE user_id = %s AND solicitud = %s", (user_id, solicitud))
                conn.commit()
                await event.reply(f"✅ Solicitud '{solicitud}' eliminada correctamente.")
    except Exception as e:
        await event.reply(f"Error al eliminar la solicitud: {str(e)}")
        logger.error(f"Error en handle_eliminar: {str(e)}")

# Configurar FastAPI para manejar webhooks y health checks
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # Configurar el webhook de Telegram
    await client.start()
    webhook_url = f"https://botpro2.onrender.com/webhook"
    await client.set_webhook(webhook_url, secret="mytoken")
    logger.info("Bot iniciado y webhook configurado")

@app.on_event("shutdown")
async def on_shutdown():
    await client.stop()
    logger.info("Bot detenido")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "message" in data:
        update = await client.parse_update(data)
        await client.dispatch_event(update)
    return PlainTextResponse(content="OK", status_code=200)

@app.get("/healthcheck")
async def healthcheck():
    return PlainTextResponse(content="Bot is running fine", status_code=200)

async def run_bot():
    logger.info("Iniciando bot en segundo plano...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import uvicorn
    # Iniciar el servidor FastAPI y el bot en paralelo
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))