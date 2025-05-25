from sqlalchemy import Column, Integer, String, BigInteger
from app.models import Base

class User(Base):
    """
    Модель пользователя.

    Атрибуты:
        id (int): Уникальный ID пользователя.
        telegram_id (int): Telegram ID пользователя (используется в боте).
        username (str): Имя пользователя (опционально).
        created_at (datetime): Время создания пользователя.

    Пример использования:
        new_user = User(telegram_id=123456789, username="ivan")
        db.add(new_user)
        db.commit()
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)  # Телеграм-пользователь
