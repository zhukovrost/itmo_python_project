from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.models import Base, user, habit
from app.logger import logger
import os


# SQLite БД в папке `data/`
DATABASE_URL = "sqlite:///./data/habits.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Только для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Инициализация базы данных и создание всех таблиц.

    Создаёт папку 'data' при необходимости, если её нет,
    и создает таблицы, описанные в моделях.

    Использование:
        init_db()
    """
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    logger.info("База данных и таблицы успешно инициализированы")


@contextmanager
def get_db():
    """
    Контекстный менеджер для получения сессии базы данных.

    Использование:
        with get_db() as db:
            # Работа с сессией db
            user = db.query(User).first()

    При выходе из контекста сессия автоматически закрывается.
    """
    logger.debug("Создание новой сессии БД")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Сессия БД закрыта")
