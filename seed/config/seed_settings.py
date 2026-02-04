import os
from .seed_profiles import SeedSize, PROFILES

# # Environment awareness
# ENV = os.getenv("APP_ENV", "DEV").upper()
# IS_PRODUCTION_LIKE = ENV in ["RENDER", "STAGING", "PROD"]
#
# # Dataset selection
# SELECTED_SIZE = SeedSize(os.getenv("SEED_SIZE", "MEDIUM").lower())
#
# # Get profile or custom
# if SELECTED_SIZE == SeedSize.CUSTOM:
#     CURRENT_PROFILE = PROFILES[SeedSize.MEDIUM] # Fallback
#     # Override with env vars if custom
#     CURRENT_PROFILE.products_count = int(os.getenv("SEED_PRODUCTS", 500))
#     CURRENT_PROFILE.clients_count = int(os.getenv("SEED_CLIENTS", 100))
#     CURRENT_PROFILE.entries_count = int(os.getenv("SEED_ENTRIES", 200))
#     CURRENT_PROFILE.distributions_count = int(os.getenv("SEED_DISTRIBUTIONS", 150))
#     CURRENT_PROFILE.sales_count = int(os.getenv("SEED_SALES", 300))
# else:
#     CURRENT_PROFILE = PROFILES[SELECTED_SIZE]
#
# # Safety flags
# FORCE_SEED = os.getenv("FORCE_SEED", "false").lower() == "true"
# DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
def load_settings():
    env = os.getenv("APP_ENV", "DEV").upper()
    is_production_like = env in ["RENDER", "STAGING", "PROD"]

    selected_size = SeedSize(os.getenv("SEED_SIZE", "MEDIUM").lower())

    if selected_size == SeedSize.CUSTOM:
        profile = PROFILES[SeedSize.MEDIUM]  # fallback
        profile.products_count = int(os.getenv("SEED_PRODUCTS", 500))
        profile.clients_count = int(os.getenv("SEED_CLIENTS", 100))
        profile.entries_count = int(os.getenv("SEED_ENTRIES", 200))
        profile.distributions_count = int(os.getenv("SEED_DISTRIBUTIONS", 150))
        profile.sales_count = int(os.getenv("SEED_SALES", 300))
    else:
        profile = PROFILES[selected_size]

    force_seed = os.getenv("FORCE_SEED", "false").lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    return {
        "ENV": env,
        "IS_PRODUCTION_LIKE": is_production_like,
        "CURRENT_PROFILE": profile,
        "FORCE_SEED": force_seed,
        "DRY_RUN": dry_run,
    }