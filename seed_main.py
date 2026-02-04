import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# ===============================
# Garantir path correto no .exe
# ===============================
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.append(str(BASE_DIR))

# ===============================
# Carregar .env
# ===============================
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

from seed.core.seed_runner import SeedRunner
from seed.config.seed_settings import load_settings
from seed.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("seed.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

def main():
    settings = load_settings()

    logging.info(f"Environment: {settings['ENV']}")
    logging.info(f"Profile: {settings['CURRENT_PROFILE']}")

    # ===============================
    # Blindagem PROD
    # ===============================
    if settings["IS_PRODUCTION_LIKE"] and not settings["FORCE_SEED"]:
        logging.error(
            "Execução de seed bloqueada em ambiente production-like. "
            "Use FORCE_SEED=true para confirmar."
        )
        sys.exit(1)

    conn = get_connection()

    runner = SeedRunner(
        conn=conn,
        settings=settings
    )

    runner.run()

    logging.info("Seed executado com sucesso!")

if __name__ == "__main__":
    main()
