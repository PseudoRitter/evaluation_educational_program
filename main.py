import tkinter as tk
import logging
from gui.app import App
from logic import Logic

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

if __name__ == "__main__":
    root = tk.Tk()  # Создание главного окна
    logic = Logic()  # Создание объекта логики
    app = App(root, logic)  # Передаем логику в интерфейс и инициализируем приложение
    
    try:
        root.mainloop()  # Запуск основного цикла обработки событий
    except Exception as e:
        logging.error(f"Ошибка в main.py: {e}", exc_info=True)