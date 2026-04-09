import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Db:
    def __init__(self):
        load_dotenv()
        self.engine: Engine = create_engine(
            os.getenv("DATABASE_URL"),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=False  # Set to True for SQL logging during debug
        )

    def _get_connection(self):
        return self.engine.connect()

