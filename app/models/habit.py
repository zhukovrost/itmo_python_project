from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.models import Base

class Habit(Base):
    """
    Модель привычки пользователя.

    Атрибуты:
        id (int): Уникальный ID привычки.
        user_id (int): ID пользователя (внешний ключ).
        name (str): Название привычки.
        description (str): Описание привычки.
        created_at (datetime): Дата создания.

    Пример использования:
        habit = Habit(user_id=1, name="Чтение", description="Читать 30 минут в день")
        db.add(habit)
        db.commit()
    """
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)

    user = relationship("User", backref="habits")


class HabitMark(Base):
    """
    Модель отметки привычки пользователя.

    Атрибуты:
        id (int): Уникальный ID привычки.
        habit_id (int): ID привычки, которую мы отмечаем (внешний ключ).
        date (datetime): Дата отметки.

    Пример использования:
        mark = HabitMark(habit_id=1, date=date.today())
        db.add(mark)
        db.commit()
    """
    __tablename__ = "habit_marks"

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"))
    date = Column(Date, nullable=False)

    habit = relationship("Habit", backref="marks")
