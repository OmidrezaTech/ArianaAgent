import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from src.api.main import init_db_and_seed
from src.core.logging import logger



async def main():
    logger.info("setting_up_database_and_seeds")
    await init_db_and_seed()
    logger.info("database_setup_completed_successfully")


if __name__ == "__main__":
    asyncio.run(main())
