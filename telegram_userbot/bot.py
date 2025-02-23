from telethon import TelegramClient, events, Button
import asyncio
from db import get_db_connection
from config import API_ID, API_HASH, CHAT_ID

client = TelegramClient('userbot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'#Solicito (.+)', chats=CHAT_ID))
async def handle_solicito(event):
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

@client.on(events.NewMessage(pattern=r'#Eliminar (.+)', chats=CHAT_ID))
async def handle_eliminar(event):
    user_id = event.sender_id
    solicitud = event.pattern_match.group(1)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM solicitudes WHERE user_id = %s AND solicitud = %s", (user_id, solicitud))
            conn.commit()
            await event.reply(f"✅ Solicitud '{solicitud}' eliminada correctamente.")

client.start()
print("Userbot en ejecución...")
client.run_until_disconnected()
