import tkinter as tk
import logging
from gui.app import App
from logic import Logic

def configure_logging():
    """Настройка логирования."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

def setup_global_keybindings(root):
    """Настройка глобальных сочетаний клавиш с использованием кодов клавиш."""
    def keypress(event):
        widget = root.focus_get()
        if not isinstance(widget, (tk.Entry, tk.Text, tk.scrolledtext.ScrolledText)):
            return  # Действия применяются только к текстовым виджетам

        # Ctrl+C (копирование)
        if event.keycode == 67 and event.state & 0x0004:  # 0x0004 — флаг Control
            widget.event_generate("<<Copy>>")
            logging.debug(f"Копирование выполнено в виджете {type(widget)}")
            return "break"

        # Ctrl+V (вставка)
        elif event.keycode == 86 and event.state & 0x0004:
            widget.event_generate("<<Paste>>")
            logging.debug(f"Вставка выполнена в виджете {type(widget)}")
            return "break"

        # Ctrl+X (вырезание)
        elif event.keycode == 88 and event.state & 0x0004:
            widget.event_generate("<<Cut>>")
            logging.debug(f"Вырезание выполнено в виджете {type(widget)}")
            return "break"

        # Ctrl+A (выделение всего)
        elif event.keycode == 65 and event.state & 0x0004:
            widget.event_generate("<<SelectAll>>")
            logging.debug(f"Выделение всего выполнено в виджете {type(widget)}")
            return "break"

    # Привязка события <Control-KeyPress> ко всем виджетам
    root.bind_all("<Control-KeyPress>", keypress)

def main():
    """Запуск приложения."""
    configure_logging()

    BATCH_SIZE = 32

    root = tk.Tk()
    logic = Logic(batch_size=BATCH_SIZE)
    app = App(root, logic, batch_size=BATCH_SIZE)
    
    # Настройка глобальных сочетаний клавиш
    setup_global_keybindings(root)
    
    try:
        root.mainloop()
    except Exception as e:
        logging.error(f"Ошибка в приложении: {e}", exc_info=True)

if __name__ == "__main__":
    main()