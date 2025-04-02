import tkinter as tk
import tkinter.ttk as ttk

# Класс для всплывающей подсказки с задержкой
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.after_id = None  # Для хранения идентификатора отложенного вызова

    def show_tip(self, text):
        """Показать всплывающую подсказку с текстом."""
        if self.tip_window or not text:
            return
        x, y = self.widget.winfo_pointerxy()  # Получаем координаты курсора
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Убираем рамку окна
        tw.wm_geometry(f"+{x + 10}+{y + 10}")  # Позиционируем рядом с курсором
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self):
        """Скрыть всплывающую подсказку."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)  # Отменяем отложенный вызов
            self.after_id = None
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def schedule_tip(self, text):
        """Запланировать показ подсказки с задержкой."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)  # Отменяем предыдущий вызов
        self.after_id = self.widget.after(800, lambda: self.show_tip(text))  # Задержка 0.8 секунды

def sort_treeview_column(treeview, col, reverse=False):
    """Сортировка столбца таблицы по возрастанию или убыванию."""
    data = [(treeview.set(item, col), item) for item in treeview.get_children("")]

    def convert_value(val):
        val = val.strip()
        if not val:  
            return (0, "")
        try:
            return (1, float(val))
        except ValueError:
            return (2, val.lower())

    data = [(convert_value(val), item) for val, item in data]
    data.sort(reverse=reverse)

    for index, (_, item) in enumerate(data):
        treeview.move(item, "", index)

    treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))

def sort_competence_type_column(treeview, col):
    """Сортировка столбца по типу компетенции."""
    if col not in treeview["columns"]:
        return

    competence_order = {
        "Универсальная компетенция": 0,
        "Общепрофессиональная компетенция": 1,
        "Профессиональная компетенция": 2
    }

    data = [(treeview.set(item, col), item) for item in treeview.get_children("")]

    def get_sort_key(value):
        val = value.strip()
        return competence_order.get(val, 3)

    data.sort(key=lambda x: get_sort_key(x[0]))

    for index, (_, item) in enumerate(data):
        treeview.move(item, "", index)

    treeview.heading(col, command=lambda: sort_competence_type_column(treeview, col))

def add_tooltip_to_treeview(treeview):
    """Добавляет всплывающую подсказку к таблице Treeview для конкретной ячейки."""
    tooltip = ToolTip(treeview)

    def on_motion(event):
        """Обработчик события движения курсора над таблицей."""
        item = treeview.identify_row(event.y)  # Определяем строку
        column = treeview.identify_column(event.x)  # Определяем столбец
        if item and column:
            # Получаем индекс столбца (column возвращает строку вида "#0", "#1" и т.д.)
            col_index = int(column[1:]) - 1  # Преобразуем в индекс (нумерация начинается с #0, но нам нужен 0-based index)
            if col_index >= 0:  # Проверяем, что это не столбец заголовка дерева (#0)
                values = treeview.item(item, 'values')
                if values and len(values) > col_index:
                    full_text = values[col_index]  # Текст из конкретной ячейки
                    tooltip.schedule_tip(full_text)  # Запускаем отложенный показ
        else:
            tooltip.hide_tip()  # Скрываем, если курсор не над ячейкой

    # Привязываем события к таблице
    treeview.bind('<Motion>', on_motion)
    treeview.bind('<Leave>', lambda e: tooltip.hide_tip())