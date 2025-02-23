from telethon import TelegramClient, events, Button
import asyncio
import os
from db import get_db_connection
from config import API_ID, API_HASH, CHAT_ID

# Obtener variables de entorno para API_ID, API_HASH y CHAT_ID
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHAT_ID = os.getenv("CHAT_ID")

if not all([API_ID, API_HASH, CHAT_ID]):
    raise ValueError("Faltan variables de entorno necesarias (API_ID, API_HASH, CHAT_ID)")

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
        print(f"Error en handle_solicito: {str(e)}")

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
        print(f"Error en handle_eliminar: {str(e)}")

async def main():
    print("Userbot en ejecución...")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())