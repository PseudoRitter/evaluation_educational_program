import tkinter as tk
import logging
from gui.app import App
from logic import Logic

def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def main():
    configure_logging()

    BATCH_SIZE = 16  # Пользователь может изменить это значение здесь

    root = tk.Tk()
    logic = Logic(batch_size=BATCH_SIZE)  
    app = App(root, logic, batch_size=BATCH_SIZE) 
    
    try:
        root.mainloop()
    except Exception as e:
        logging.error(f"Ошибка в приложении: {e}", exc_info=True)

if __name__ == "__main__":
    main()