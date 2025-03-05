import tkinter.ttk as ttk

def sort_treeview_column(treeview, col, reverse=False):
    """Сортировка столбца Treeview по возрастанию или убыванию."""
    # Получаем все строки таблицы
    data = [(treeview.set(item, col), item) for item in treeview.get_children("")]

    # Преобразуем данные для сортировки: числа как float, остальное как str
    def convert_value(val):
        val = val.strip()
        if not val:  # Пустые строки сортируются как минимальное значение
            return (0, "")
        try:
            # Если значение можно преобразовать в float, возвращаем его как число
            return (1, float(val))
        except ValueError:
            # Если не число, возвращаем как строку в нижнем регистре
            return (2, val.lower())

    # Применяем преобразование к данным
    data = [(convert_value(val), item) for val, item in data]

    # Сортируем данные
    data.sort(reverse=reverse)

    # Перемещаем строки в таблице
    for index, (_, item) in enumerate(data):
        treeview.move(item, "", index)

    # Переключаем направление сортировки при следующем клике
    treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))