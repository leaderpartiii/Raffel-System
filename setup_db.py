import logging
from database.models import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """
    Инициализирует базу данных и создает все таблицы
    """
    try:
        logger.info("Initializing database...")
        db_manager.create_all_tables()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


if __name__ == "__main__":
    setup_database()
