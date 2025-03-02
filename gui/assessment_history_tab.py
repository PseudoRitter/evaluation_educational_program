import tkinter as tk
import logging
from tkinter import ttk
from datetime import datetime

def create_rating_history_tab(frame, app):
    pass
    # Главный фрейм
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=False, pady=5)

    # 1. Фрейм для таблицы образовательной программы и оцениваемой вакансии
    program_vacancy_frame = tk.LabelFrame(main_frame, text="Образовательная программа и оцениваемая вакансия")
    program_vacancy_frame.pack(fill="both", expand=False, padx=5, pady=5)

    app.program_vacancy_history_table = ttk.Treeview(program_vacancy_frame, columns=("educational_program", "vacancy"), show="headings", height=6)
    app.program_vacancy_history_table.heading("educational_program", text="Образовательная программа")
    app.program_vacancy_history_table.heading("vacancy", text="Вакансия")
    app.program_vacancy_history_table.column("educational_program", width=400)
    app.program_vacancy_history_table.column("vacancy", width=300)
    app.program_vacancy_history_table.pack(fill="both", expand=False)
    app.program_vacancy_history_table.bind("<<TreeviewSelect>>", lambda event: update_history_competence_history_table(app))

    # 2. Фрейм для таблицы оценки компетенций образовательной программы
    competence_frame = tk.LabelFrame(main_frame, text="Оценка компетенций образовательной программы")
    competence_frame.pack(fill="both", expand=False, padx=2, pady=5)

    app.competence_history_table = ttk.Treeview(competence_frame, columns=("competence", "type_competence", "score"), show="headings", height=6)
    app.competence_history_table.heading("competence", text="Компетенция")
    app.competence_history_table.heading("type_competence", text="Вид компетенции")
    app.competence_history_table.heading("score", text="Оценка")
    app.competence_history_table.column("competence", width=400)
    app.competence_history_table.column("type_competence", width=300)
    app.competence_history_table.column("score", width=150)
    app.competence_history_table.pack(fill="both", expand=False)

    # Загрузка данных в таблицу программ и вакансий
    load_program_vacancy_history_table(app)

def load_program_vacancy_history_table(app):
    """Загрузка уникальных пар образовательных программ и вакансий из таблицы assessment."""
    try:
        app.program_vacancy_history_table.delete(*app.program_vacancy_history_table.get_children())
        query = """
            SELECT DISTINCT 
                ep.educational_program_name,
                v.vacancy_name
            FROM public.assessment a
            JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
            JOIN vacancy v ON a.vacancy_id = v.vacancy_id
            ORDER BY ep.educational_program_name, v.vacancy_name;
        """
        app.logic.db.cursor.execute(query)
        for row in app.logic.db.cursor.fetchall():
            app.program_vacancy_history_table.insert("", tk.END, values=row)
    except Exception as e:
        app.show_error(f"Ошибка при загрузке данных программ и вакансий: {e}")
        logging.error(f"Ошибка при загрузке данных из assessment: {e}")

def update_history_competence_history_table(app):
    """Обновление таблицы компетенций на основе выбранной программы и вакансии."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        app.competence_history_table.delete(*app.competence_history_table.get_children())
        return

    values = app.program_vacancy_history_table.item(selected_item[0])['values']
    educational_program_name, vacancy_name = values

    try:
        app.competence_history_table.delete(*app.competence_history_table.get_children())
        query = """
            SELECT 
                c.competence_name,
                tc.type_competence_full_name,
                a.value
            FROM public.assessment a
            JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
            JOIN vacancy v ON a.vacancy_id = v.vacancy_id
            JOIN competence c ON a.competence_id = c.competence_id
            JOIN type_competence tc ON a.type_competence_id = tc.type_competence_id
            WHERE ep.educational_program_name = %s AND v.vacancy_name = %s
            ORDER BY c.competence_name;
        """
        app.logic.db.cursor.execute(query, (educational_program_name, vacancy_name))
        for row in app.logic.db.cursor.fetchall():
            app.competence_history_table.insert("", tk.END, values=(row[0], row[1], f"{row[2]:.6f}"))
    except Exception as e:
        app.show_error(f"Ошибка при загрузке данных компетенций: {e}")
        logging.error(f"Ошибка при обновлении таблицы компетенций: {e}")