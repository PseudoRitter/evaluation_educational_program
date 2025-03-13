import tkinter.ttk as ttk

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