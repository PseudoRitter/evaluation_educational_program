import tkinter as tk
import logging
import numpy as np
from tkinter import ttk, scrolledtext
from datetime import datetime

def create_rating_history_tab(frame, app):
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=True, pady=5)

    program_vacancy_frame = tk.LabelFrame(main_frame, text="Образовательная программа и оцениваемая вакансия")
    program_vacancy_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Добавляем новый столбец "assessment_date"
    app.program_vacancy_history_table = ttk.Treeview(program_vacancy_frame, columns=("educational_program", "vacancy", "assessment_date"), show="headings", height=6)
    app.program_vacancy_history_table.heading("educational_program", text="Образовательная программа")
    app.program_vacancy_history_table.heading("vacancy", text="Вакансия")
    app.program_vacancy_history_table.heading("assessment_date", text="Дата и время анализа")
    app.program_vacancy_history_table.column("educational_program", width=350)
    app.program_vacancy_history_table.column("vacancy", width=250)
    app.program_vacancy_history_table.column("assessment_date", width=150)
    app.program_vacancy_history_table.pack(fill="both", expand=True)
    app.program_vacancy_history_table.bind("<<TreeviewSelect>>", lambda event: update_competence_history_table(app))

    competence_frame = tk.LabelFrame(main_frame, text="Оценка компетенций образовательной программы")
    competence_frame.pack(fill="both", expand=True, padx=5, pady=5)

    app.competence_history_table = ttk.Treeview(competence_frame, columns=("competence", "type_competence", "score"), show="headings", height=6)
    app.competence_history_table.heading("competence", text="Компетенция")
    app.competence_history_table.heading("type_competence", text="Вид компетенции")
    app.competence_history_table.heading("score", text="Оценка")
    app.competence_history_table.column("competence", width=400)
    app.competence_history_table.column("type_competence", width=300)
    app.competence_history_table.column("score", width=150)
    app.competence_history_table.pack(fill="both", expand=True)

    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)
    group_scores_history_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_history_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_history_frame = scrolledtext.ScrolledText(group_scores_history_frame, width=120, height=8)
    app.group_scores_history_frame.pack(pady=4)

    export_history_frame = tk.Frame(main_frame)
    export_history_frame.pack(pady=4, fill="both", expand=False)
    app.export_history_button = tk.Button(export_history_frame, text="Экспорт в Excel", command=app.logic.export_results_to_excel)
    app.export_history_button.pack()

    load_program_vacancy_history_table(app)

def load_program_vacancy_history_table(app):
    """Загрузка уникальных пар программ, вакансий и даты анализа из таблицы assessment."""
    try:
        app.program_vacancy_history_table.delete(*app.program_vacancy_history_table.get_children())
        query = """
            SELECT DISTINCT 
                ep.educational_program_name,
                v.vacancy_name,
                a.assessment_date
            FROM public.assessment a
            JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
            JOIN vacancy v ON a.vacancy_id = v.vacancy_id
            ORDER BY ep.educational_program_name, v.vacancy_name, a.assessment_date;
        """
        conn = app.logic.db.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            logging.info(f"Загружено {len(rows)} строк из таблицы assessment")
            for row in rows:
                # Поскольку assessment_date - TEXT, используем его как есть
                assessment_date_str = row[2] if row[2] else "Не указана"
                app.program_vacancy_history_table.insert("", tk.END, values=(row[0], row[1], assessment_date_str))
            # Обновляем оценки для первой строки, если она есть
            if app.program_vacancy_history_table.get_children():
                app.program_vacancy_history_table.selection_set(app.program_vacancy_history_table.get_children()[0])
                update_competence_history_table(app)
                update_group_scores(app)
        app.logic.db.release_connection(conn)
    except Exception as e:
        app.show_error(f"Ошибка при загрузке данных программ и вакансий: {e}")
        logging.error(f"Ошибка при загрузке данных из assessment: {e}", exc_info=True)

def update_competence_history_table(app):
    """Обновление таблицы компетенций на основе выбранной программы и вакансии."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        app.competence_history_table.delete(*app.competence_history_table.get_children())
        app.group_scores_history_frame.delete(1.0, tk.END)
        return

    values = app.program_vacancy_history_table.item(selected_item[0])['values']
    educational_program_name, vacancy_name, assessment_date = values

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
            WHERE ep.educational_program_name = %s AND v.vacancy_name = %s AND a.assessment_date = %s
            ORDER BY c.competence_name;
        """
        conn = app.logic.db.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, (educational_program_name, vacancy_name, assessment_date))
            for row in cursor.fetchall():
                app.competence_history_table.insert("", tk.END, values=(row[0], row[1], f"{row[2]:.6f}"))
            update_group_scores(app)
        app.logic.db.release_connection(conn)
    except Exception as e:
        app.show_error(f"Ошибка при загрузке данных компетенций: {e}")
        logging.error(f"Ошибка при обновлении таблицы компетенций: {e}")

def update_group_scores(app):
    """Обновление оценок групп компетенций и общей оценки в group_scores_history_frame."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        app.group_scores_history_frame.delete(1.0, tk.END)
        return

    values = app.program_vacancy_history_table.item(selected_item[0])['values']
    educational_program_name, vacancy_name, assessment_date = values

    try:
        app.group_scores_history_frame.delete(1.0, tk.END)
        query = """
            SELECT c.competence_name, tc.type_competence_full_name, a.value
            FROM public.assessment a
            JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
            JOIN vacancy v ON a.vacancy_id = v.vacancy_id
            JOIN competence c ON a.competence_id = c.competence_id
            JOIN type_competence tc ON a.type_competence_id = tc.type_competence_id
            WHERE ep.educational_program_name = %s AND v.vacancy_name = %s AND a.assessment_date = %s
        """
        conn = app.logic.db.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, (educational_program_name, vacancy_name, assessment_date))
            assessments = cursor.fetchall()

            if not assessments:
                app.group_scores_history_frame.insert(tk.END, "Нет данных об оценках.")
                return

            group_scores = {}
            for competence_name, type_competence, score in assessments:
                if type_competence not in group_scores:
                    group_scores[type_competence] = []
                group_scores[type_competence].append(float(score))

            group_averages = {ctype: np.mean(scores) for ctype, scores in group_scores.items()}
            overall_score = np.mean([score for _, scores in group_scores.items() for score in scores])

            app.group_scores_history_frame.insert(tk.END, "Оценки групп компетенций:\n")
            for ctype, avg_score in group_averages.items():
                app.group_scores_history_frame.insert(tk.END, f"{ctype}: {avg_score:.6f}\n")
            app.group_scores_history_frame.insert(tk.END, f"\nОбщая оценка программы: {overall_score:.6f}\n")
        app.logic.db.release_connection(conn)
    except Exception as e:
        app.show_error(f"Ошибка при обновлении оценок групп: {e}")
        logging.error(f"Ошибка при обновлении group_scores_history_frame: {e}")

def refresh_history_tables(app):
    """Ручное обновление обеих таблиц на вкладке истории."""
    load_program_vacancy_history_table(app)
    selected_item = app.program_vacancy_history_table.selection()
    if selected_item:
        update_competence_history_table(app)
        update_group_scores(app)