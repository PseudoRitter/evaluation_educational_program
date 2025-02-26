import tkinter as tk
from tkinter import ttk

def create_education_tab(frame, app):
    # Выпадающий список для выбора образовательной программы
    app.program_label = tk.Label(frame, text="Выберите образовательную программу:")
    app.program_label.pack()
    app.program_var = tk.StringVar()
    app.program_combobox = ttk.Combobox(frame, textvariable=app.program_var, state="readonly")
    app.program_combobox.pack()
    app.program_combobox.bind("<<ComboboxSelected>>", app.on_program_select)