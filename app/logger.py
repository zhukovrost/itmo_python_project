import logging

# Создание логгера
logger = logging.getLogger("habit_tracker")
logger.setLevel(logging.DEBUG)  # Можно заменить на INFO в проде

# Создание обработчика для консоли
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Формат логов
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Добавление обработчика, если еще не добавлен
if not logger.hasHandlers():
    logger.addHandler(console_handler)
