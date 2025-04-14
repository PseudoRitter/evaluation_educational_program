import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os
import torch
import gc
from gui.app import App
from logic import Logic
from concurrent.futures import ThreadPoolExecutor


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
            return  

        if event.keycode == 67 and event.state & 0x0004:  
            widget.event_generate("<<Copy>>")
            logging.debug(f"Копирование выполнено в виджете {type(widget)}")
            return "break"
        elif event.keycode == 86 and event.state & 0x0004:
            widget.event_generate("<<Paste>>")
            logging.debug(f"Вставка выполнена в виджете {type(widget)}")
            return "break"
        elif event.keycode == 88 and event.state & 0x0004:
            widget.event_generate("<<Cut>>")
            logging.debug(f"Вырезание выполнено в виджете {type(widget)}")
            return "break"
        elif event.keycode == 65 and event.state & 0x0004:
            widget.event_generate("<<SelectAll>>")
            logging.debug(f"Выделение всего выполнено в виджете {type(widget)}")
            return "break"

    root.bind_all("<Control-KeyPress>", keypress)

def on_closing(root, app, logic):
    """Обработчик закрытия окна с подтверждением и полным завершением процессов."""
    if messagebox.askyesno("Подтверждение", "Уверены, что хотите закрыть программу?"):
        try:
            # Завершаем ThreadPoolExecutor в App
            if hasattr(app, 'executor'):
                app.executor.shutdown(wait=False)
                logging.info("Executor в App завершен")

            if hasattr(app, 'vac_executor'):
                app.vac_executor.shutdown(wait=False)
                logging.info("Vac_executor в App завершен")

            # Завершаем ThreadPoolExecutor в Logic
            if hasattr(logic, 'executor'):
                logic.executor.shutdown(wait=False)
                logging.info("Executor в Logic завершен")

            # Очищаем ресурсы GPU, если используются
            if hasattr(logic, 'device') and logic.device == "cuda":
                # Проверяем наличие matcher и его модели
                if hasattr(logic, 'matcher') and logic.matcher is not None and hasattr(logic.matcher, 'model') and logic.matcher.model is not None:
                    logic.matcher.model.to("cpu")  # Перемещаем модель на CPU
                    del logic.matcher.model  # Удаляем модель
                    logging.info("Модель matcher перемещена на CPU и удалена")
                # Очистка кэша GPU из run_analysis
                logging.info("Очистка кэш GPU при закрытии программы...")
                gc.collect()
                torch.cuda.empty_cache()
                logging.info("Ресурсы GPU очищены")

            # Закрываем соединение с базой данных
            if hasattr(logic.db, 'close_connection'):
                logic.db.close_connection()
                logging.info("Соединение с базой данных закрыто")

            # Уничтожаем главное окно
            root.destroy()
            logging.info("Программа закрыта пользователем")

            # Принудительное завершение процесса Python
            os._exit(0)  # Используем os._exit для немедленного завершения

        except Exception as e:
            logging.error(f"Ошибка при закрытии программы: {e}", exc_info=True)
            os._exit(1)  # Принудительное завершение с ошибкой

def main():
    """Запуск приложения."""
    configure_logging()

    BATCH_SIZE = 32

    root = tk.Tk()
    logic = Logic(batch_size=BATCH_SIZE)
    app = App(root, logic, batch_size=BATCH_SIZE)
    
    # Настройка глобальных сочетаний клавиш
    setup_global_keybindings(root)
    
    # Перехват события закрытия окна
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app, logic))
    
    try:
        root.mainloop()
    except Exception as e:
        logging.error(f"Ошибка в приложении: {e}", exc_info=True)
        on_closing(root, app, logic)

if __name__ == "__main__":
    main()