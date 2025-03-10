import tkinter.ttk as ttk

def sort_treeview_column(treeview, col, reverse=False):
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