import tkinter as tk
import re
from tkinter import ttk, scrolledtext

def create_debug_tab(frame, app):
    app.classification_table_label = tk.Label(frame, text="Результаты классификации:")
    app.classification_table_label.pack()

    app.classification_table = ttk.Treeview(frame, columns=("sentence", "category"), show="headings")
    app.classification_table.heading("sentence", text="Предложение")
    app.classification_table.heading("category", text="Категория")
    app.classification_table.column("sentence", width=600)
    app.classification_table.column("category", width=150)
    app.classification_table.pack(fill="x", pady=5)

    scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=app.classification_table.xview)
    app.classification_table.configure(xscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    app.result_text_label = tk.Label(frame, text="Результаты анализа:")
    app.result_text_label.pack()
    app.result_text_area = scrolledtext.ScrolledText(frame, width=120, height=5)
    app.result_text_area.pack()

@staticmethod
def validate(possible_new_value):
    return bool(re.match(r'^[0-9a-fA-F]*$', possible_new_value))