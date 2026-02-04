import sys
import os
from pathlib import Path

# Adicionar o diretório atual ao sys.path para permitir importações relativas
sys.path.append(str(Path(__file__).resolve().parent))

from db import get_connection
from seed.core.seed_runner import SeedRunner

def main():
    print("--- Professional Data Seeding System ---")
    try:
        conn = get_connection()
        runner = SeedRunner(conn)
        runner.run_all()
        conn.close()
        print("--- Seeding Process Finished ---")
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
