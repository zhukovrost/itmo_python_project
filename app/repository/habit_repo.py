from sqlalchemy.orm import Session
from datetime import date
from app.models.habit import Habit, HabitMark
from app.logger import logger

class HabitRepo:
    """
    Репозиторий для работы с привычками.

    Методы:
        list_by_user(user_id): Возвращает все привычки пользователя
        get_by_id(habit_id): Возвращает привычку по её ID
        create(habit): Создает новую привычку
        mark_done(habit_id): Отметить привычку выполненной
        get_marks(habit_id): Получить отметки для привычки

    Пример использования:
        with get_db() as db:
            repo = HabitRepo(db)
            habits = repo.get_all_by_user(user_id=1)
    """
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, name: str) -> Habit:
        logger.debug(f"Создание привычки: {name} для пользователя {user_id}")
        habit = Habit(user_id=user_id, name=name)
        self.db.add(habit)
        self.db.commit()
        self.db.refresh(habit)
        return habit

    def get_by_id(self, habit_id: int) -> Habit | None:
        logger.debug(f"Получение привычки с ID: {habit_id}")
        return self.db.query(Habit).filter(Habit.id == habit_id).first()

    def list_by_user(self, user_id: int) -> list[Habit]:
        logger.debug(f"Получение всех привычек пользователя с ID: {user_id}")
        return self.db.query(Habit).filter(Habit.user_id == user_id).all()

    def mark_done(self, habit_id: int, mark_date: date) -> HabitMark:
        logger.debug(f"Отметка привычки: {habit_id}")
        mark = HabitMark(habit_id=habit_id, date=mark_date)
        self.db.add(mark)
        self.db.commit()
        self.db.refresh(mark)
        return mark

    def get_marks(self, habit_id: int) -> list[HabitMark]:
        logger.debug(f"Получение отметок для привычки с ID {habit_id}")
        return self.db.query(HabitMark).filter(HabitMark.habit_id == habit_id).all()
