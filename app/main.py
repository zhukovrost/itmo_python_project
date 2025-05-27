from app.database import init_db, get_db
from app.repository.user_repo import UserRepo


def main():
    """
    Точка входа. Создает базу данных и таблицы.

    Пример использования:
        python -m app.main
    """
    init_db()   # ОБЯЗАТЕЛЬНО ДОЛЖНО БЫТЬ В САМОМ НАЧАЛЕ
    # Далее пример использования работы с бд
    with get_db() as db:
        users = UserRepo(db)
        users.get_by_id(1)

if __name__ == "__main__":
    main()
