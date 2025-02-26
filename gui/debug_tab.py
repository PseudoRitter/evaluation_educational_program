import tkinter as tk
from tkinter import ttk, scrolledtext

def create_debug_tab(frame, app):
    # Результаты классификации и таблица
    app.classification_table_label = tk.Label(frame, text="Результаты классификации:")
    app.classification_table_label.pack()

    app.classification_table = ttk.Treeview(frame, columns=("sentence", "category", "score"), show="headings")
    app.classification_table.heading("sentence", text="Предложение")
    app.classification_table.heading("category", text="Категория")
    app.classification_table.heading("score", text="Оценка")
    app.classification_table.column("sentence", width=800)
    app.classification_table.column("category", width=150)
    app.classification_table.column("score", width=100)
    app.classification_table.pack()

    # Поле для вывода результатов анализа
    app.result_text_label = tk.Label(frame, text="Результаты анализа:")
    app.result_text_label.pack()
    app.result_text_area = scrolledtext.ScrolledText(frame, width=120, height=5)
    app.result_text_area.pack()
    app.result_text_area = app.result_text_area  # Сохраняем как атрибут

    # Кнопка для экспорта результатов в TXT
    app.export_txt_button = tk.Button(frame, text="Экспорт в TXT", command=app.export_to_txt)
    app.export_txt_button.pack(pady=10)