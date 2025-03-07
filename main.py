import tkinter as tk
import logging
from gui.app import App
from logic import Logic

def configure_logging():
    """Настройка логирования для приложения."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def main():
    """Запуск приложения для оценки соответствия образовательных программ."""
    configure_logging()
    
    root = tk.Tk()
    logic = Logic()
    app = App(root, logic)
    
    try:
        root.mainloop()
    except Exception as e:
        logging.error(f"Ошибка в приложении: {e}", exc_info=True)

if __name__ == "__main__":
    main()