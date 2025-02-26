import tkinter as tk
from tkinter import ttk

def create_vacancies_tab(frame, app):
    # Выпадающий список для выбора вакансии
    app.vacancy_label = tk.Label(frame, text="Выберите вакансию:")
    app.vacancy_label.pack()
    app.vacancy_var = tk.StringVar()
    app.vacancy_combobox = ttk.Combobox(frame, textvariable=app.vacancy_var, state="readonly")
    app.vacancy_combobox.pack()
    app.vacancy_combobox.bind("<<ComboboxSelected>>", app.on_vacancy_select)