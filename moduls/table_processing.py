import tkinter as tk
import tkinter.ttk as ttk

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.after_id = None  

    def wrap_text(self, text, max_width=80):
        """Разбивает текст на строки, каждая из которых не превышает max_width символов."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if sum(len(w) for w in current_line) + len(word) + len(current_line) <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def show_tip(self, text):
        """Показать всплывающую подсказку с текстом."""
        if self.tip_window or not text:
            return

        wrapped_text = self.wrap_text(text, max_width=100)

        x, y = self.widget.winfo_pointerxy()  
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  
        tw.wm_geometry(f"+{x + 10}+{y + 10}")  
        label = tk.Label(
            tw,
            text=wrapped_text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
            anchor="w"
        )
        label.pack(ipadx=5, ipady=5)

    def hide_tip(self):
        """Скрыть всплывающую подсказку."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)  
            self.after_id = None
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def schedule_tip(self, text):
        """Запланировать показ подсказки с задержкой."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)  
        self.after_id = self.widget.after(800, lambda: self.show_tip(text)) 


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
        item = treeview.identify_row(event.y)  
        column = treeview.identify_column(event.x)  
        if item and column:
            col_index = int(column[1:]) - 1 
            if col_index >= 0:  
                values = treeview.item(item, 'values')
                if values and len(values) > col_index:
                    full_text = values[col_index]  
                    tooltip.schedule_tip(full_text)  
        else:
            tooltip.hide_tip()  

    treeview.bind('<Motion>', on_motion)
    treeview.bind('<Leave>', lambda e: tooltip.hide_tip())