import tkinter as tk
import logging
from gui import App
from logic import Logic

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()          # Вывод логов в консоль
    ]
)

if __name__ == "__main__":
    root = tk.Tk()  # Создание главного окна
    logic = Logic()  # Создание объекта логики
    app = App(root, logic)  # Передаем логику в интерфейс
    try:
        root.mainloop()  # Запуск основного цикла обработки событий
    except Exception as e:
        logging.error(f"Ошибка в main.py: {e}", exc_info=True)
        