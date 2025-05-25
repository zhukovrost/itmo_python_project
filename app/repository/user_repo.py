from sqlalchemy.orm import Session
from app.models.user import User
from app.logger import logger

class UserRepo:
    """
    Репозиторий для работы с таблицей пользователей.

    Методы:
        get_by_id(id): Возвращает пользователя (app.models.user.User) по ID
        get_by_telegram_id(tg_id): Ищет пользователя по Telegram ID
        create(user): Создает нового пользователя

    Пример использования:
        with get_db() as db:
            repo = UserRepo(db)
            user = repo.get_by_telegram_id(123456)
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        logger.debug(f"Поиск пользователя по ID: {user_id}")
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        logger.debug(f"Поиск пользователя по Telegram ID: {telegram_id}")
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def create(self, username: str = None, email: str = None, telegram_id: int = None) -> User:
        logger.info(f"Создание пользователя: {username}")
        user = User(username=username, email=email, telegram_id=telegram_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list(self) -> list[User]:
        return self.db.query(User).all()
