import logging
# from ..config.seed_settings import CURRENT_PROFILE, ENV, IS_PRODUCTION_LIKE, FORCE_SEED
from ..config.seed_settings import load_settings
from ..seeds.seed_products import SeedProducts
from ..seeds.seed_clients import SeedClients
from ..seeds.seed_entries import SeedEntries, SeedEntriesAPI
from ..seeds.seed_distributions import SeedDistributions, SeedDistributionsAPI
from ..seeds.seed_sales import SeedSales, SeedSalesAPI

logger = logging.getLogger(__name__)

class SeedRunner:
    def __init__(self, conn, settings=None):
        self.conn = conn
        self.settings = settings
        self.profile = load_settings()["CURRENT_PROFILE"]
        self.force = settings["FORCE_SEED"] if settings else False

        self.stages = {
            "products": SeedProducts,
            "clients": SeedClients,
            "entries": SeedEntriesAPI,
            "distributions": SeedDistributionsAPI,
            "sales": SeedSalesAPI,
        }

    def run(self, only: list[str] | None = None):
        logger.info(f"Starting seed runner in environment: {load_settings()['ENV']}")
        logger.info(f"Profile: {self.profile}")

        if load_settings()["IS_PRODUCTION_LIKE"] and not load_settings()["FORCE_SEED"]:
            logger.warning("Targeting a production-like environment without FORCE_SEED=true. Aborting.")
            return

        stages_to_run = (
            self.stages
            if not only
            else {k: v for k, v in self.stages.items() if k in only}
        )

        # for name, stage in stages_to_run.items():
        #     logging.info(f"Executando seed: {name}")
        #     stage()

        for stage_name in stages_to_run:
            stage_class = self.stages.get(stage_name)
            if stage_class:
                stage = stage_class(self.conn, self.profile)
                stage.run()
            else:
                logger.warning(f"Unknown seed stage: {stage_name}")

    def run_all(self):
        logger.info(f"Starting seed runner in environment: {load_settings()['ENV']}")
        logger.info(f"Profile: {self.profile}")

        if load_settings()["IS_PRODUCTION_LIKE"] and not load_settings()["FORCE_SEED"]:
            logger.warning("Targeting a production-like environment without FORCE_SEED=true. Aborting.")
            return

        # Ordem de execução respeitando integridade referencial
        stages = [
            SeedProducts,
            SeedClients,
            SeedEntries,
            SeedDistributions,
            SeedSales
        ]

        for stage_class in stages:
            stage = stage_class(self.conn, self.profile)
            stage.run()

        logger.info("All seed stages completed successfully.")

    def run_selected(self, stages):
        logger.info(f"Starting selected seed stages in environment: {load_settings()['ENV']}")
        logger.info(f"Profile: {self.profile}")

        if load_settings()["IS_PRODUCTION_LIKE"] and not load_settings()["FORCE_SEED"]:
            logger.warning("Targeting a production-like environment without FORCE_SEED=true. Aborting.")
            return

        stage_map = {
            "products": SeedProducts,
            "clients": SeedClients,
            "entries": SeedEntries,
            "distributions": SeedDistributions,
            "sales": SeedSales
        }

        for stage_name in stages:
            stage_class = stage_map.get(stage_name)
            if stage_class:
                stage = stage_class(self.conn, self.profile)
                stage.run()
            else:
                logger.warning(f"Unknown seed stage: {stage_name}")

        logger.info("Selected seed stages completed successfully.")
