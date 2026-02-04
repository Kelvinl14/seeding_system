import logging
import time
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseSeed(ABC):
    def __init__(self, conn, profile):
        self.conn = conn
        self.profile = profile
        self.name = self.__class__.__name__

    def run(self):
        start_time = time.time()
        logger.info(f"Starting {self.name}...")
        try:
            with self.conn.cursor() as cur:
                result = self.execute(cur)
                self.conn.commit()
                duration = time.time() - start_time
                logger.info(f"Finished {self.name} in {duration:.2f}s")
                return result
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error in {self.name}: {str(e)}")
            raise e

    @abstractmethod
    def execute(self, cur):
        pass
