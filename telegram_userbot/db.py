import psycopg2
from config import DB_URL

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    solicitud TEXT NOT NULL,
                    estado TEXT DEFAULT 'pendiente',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

if __name__ == "__main__":
    init_db()
