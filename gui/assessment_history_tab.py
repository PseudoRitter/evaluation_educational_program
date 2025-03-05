import tkinter as tk
import numpy as np
from tkinter import ttk, scrolledtext, messagebox
import logging
from moduls.export_to_excel import ExcelExporter
from moduls.table_sort import sort_treeview_column  

def create_rating_history_tab(frame, app):
    """Создание вкладки истории оценок."""
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=True, pady=5)

    # Таблица программ и вакансий
    program_vacancy_frame = tk.LabelFrame(main_frame, text="Образовательная программа и оцениваемая вакансия")
    program_vacancy_frame.pack(fill="both", expand=True, padx=5, pady=5)

    app.program_vacancy_history_table = ttk.Treeview(
        program_vacancy_frame,
        columns=("educational_program", "vacancy", "assessment_date"),
        show="headings",
        height=6
    )
    app.program_vacancy_history_table.heading("educational_program", text="Образовательная программа", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "educational_program", False))
    app.program_vacancy_history_table.heading("vacancy", text="Вакансия", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "vacancy", False))
    app.program_vacancy_history_table.heading("assessment_date", text="Дата и время анализа", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "assessment_date", False))
    app.program_vacancy_history_table.column("educational_program", width=350)
    app.program_vacancy_history_table.column("vacancy", width=250)
    app.program_vacancy_history_table.column("assessment_date", width=150)
    app.program_vacancy_history_table.pack(fill="both", expand=True)
    app.program_vacancy_history_table.bind("<<TreeviewSelect>>", lambda event: update_competence_history_table(app))

    # Таблица компетенций
    competence_frame = tk.LabelFrame(main_frame, text="Оценка компетенций образовательной программы")
    competence_frame.pack(fill="both", expand=True, padx=5, pady=5)

    app.competence_history_table = ttk.Treeview(
        competence_frame,
        columns=("competence", "type_competence", "score"),
        show="headings",
        height=6
    )
    app.competence_history_table.heading("competence", text="Компетенция", command=lambda: sort_treeview_column(app.competence_history_table, "competence", False))
    app.competence_history_table.heading("type_competence", text="Вид компетенции", command=lambda: sort_treeview_column(app.competence_history_table, "type_competence", False))
    app.competence_history_table.heading("score", text="Оценка")
    app.competence_history_table.column("competence", width=400)
    app.competence_history_table.column("type_competence", width=300)
    app.competence_history_table.column("score", width=150)
    app.competence_history_table.pack(fill="both", expand=True)

    # Контейнер результатов
    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)
    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_history_frame = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_history_frame.pack(pady=4)

    # Кнопка экспорта
    export_frame = tk.Frame(main_frame)
    export_frame.pack(pady=4, fill="both", expand=False)
    app.export_history_button = tk.Button(export_frame, text="Экспорт в Excel", command=lambda: export_history_to_excel(app))
    app.export_history_button.pack()

    load_program_vacancy_history_table(app)

def export_history_to_excel(app):
    """Экспорт данных из таблиц истории в Excel."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите запись для экспорта!")
        return

    values = app.program_vacancy_history_table.item(selected_item[0])["values"]
    educational_program_name, vacancy_name, assessment_date = values

    try:
        results = app.logic.db.fetch_assessment_results(educational_program_name, vacancy_name, assessment_date)
        exporter = ExcelExporter(results, educational_program_name, vacancy_name)
        exporter.export_to_excel()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
        logging.error(f"Ошибка экспорта истории: {e}", exc_info=True)

def load_program_vacancy_history_table(app):
    """Загрузка данных в таблицу программ и вакансий."""
    try:
        app.program_vacancy_history_table.delete(*app.program_vacancy_history_table.get_children())
        rows = app.logic.db.fetch_program_vacancy_history()
        logging.info(f"Загружено {len(rows)} строк из таблицы assessment")
        for row in rows:
            assessment_date_str = row[2] if row[2] else "Не указана"
            app.program_vacancy_history_table.insert("", tk.END, values=(row[0], row[1], assessment_date_str))
        if app.program_vacancy_history_table.get_children():
            app.program_vacancy_history_table.selection_set(app.program_vacancy_history_table.get_children()[0])
            update_competence_history_table(app)
            update_group_scores(app)
    except Exception as e:
        app.show_error(f"Ошибка при загрузке данных: {e}")
        logging.error(f"Ошибка загрузки данных из assessment: {e}", exc_info=True)

def update_competence_history_table(app):
    """Обновление таблицы компетенций на основе выбранной записи."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        app.competence_history_table.delete(*app.competence_history_table.get_children())
        app.group_scores_history_frame.delete(1.0, tk.END)
        return

    values = app.program_vacancy_history_table.item(selected_item[0])["values"]
    educational_program_name, vacancy_name, assessment_date = values

    try:
        app.competence_history_table.delete(*app.competence_history_table.get_children())
        rows = app.logic.db.fetch_competence_history(educational_program_name, vacancy_name, assessment_date)
        for row in rows:
            app.competence_history_table.insert("", tk.END, values=(row[0], row[1], f"{row[2]:.6f}"))
        update_group_scores(app)
    except Exception as e:
        app.show_error(f"Ошибка загрузки компетенций: {e}")
        logging.error(f"Ошибка обновления таблицы компетенций: {e}", exc_info=True)

def update_group_scores(app):
    """Обновление оценок групп компетенций и общей оценки."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        app.group_scores_history_frame.delete(1.0, tk.END)
        return

    values = app.program_vacancy_history_table.item(selected_item[0])["values"]
    educational_program_name, vacancy_name, assessment_date = values

    try:
        app.group_scores_history_frame.delete(1.0, tk.END)
        assessments = app.logic.db.fetch_competence_history(educational_program_name, vacancy_name, assessment_date)

        if not assessments:
            app.group_scores_history_frame.insert(tk.END, "Нет данных об оценках.")
            return

        group_scores = {}
        for _, type_competence, score in assessments:
            group_scores.setdefault(type_competence, []).append(float(score))

        group_averages = {ctype: np.mean(scores) for ctype, scores in group_scores.items()}
        overall_score = np.mean([score for scores in group_scores.values() for score in scores])

        app.group_scores_history_frame.insert(tk.END, "Оценки групп компетенций:\n")
        for ctype, avg_score in group_averages.items():
            app.group_scores_history_frame.insert(tk.END, f"{ctype}: {avg_score:.6f}\n")
        app.group_scores_history_frame.insert(tk.END, f"\nОбщая оценка программы: {overall_score:.6f}\n")
    except Exception as e:
        app.show_error(f"Ошибка обновления оценок: {e}")
        logging.error(f"Ошибка обновления оценок групп: {e}", exc_info=True)

def refresh_history_tables(app):
    """Ручное обновление таблиц истории."""
    load_program_vacancy_history_table(app)
    selected_item = app.program_vacancy_history_table.selection()
    if selected_item:
        update_competence_history_table(app)
        update_group_scores(app)