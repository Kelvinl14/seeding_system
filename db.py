import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from psycopg2.extras import RealDictCursor

# Caminho absoluto para a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega explicitamente o .env
load_dotenv(BASE_DIR / ".env")

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432),
        cursor_factory=RealDictCursor,
        sslmode="require"
    )
