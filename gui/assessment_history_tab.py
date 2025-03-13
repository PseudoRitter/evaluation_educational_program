import tkinter as tk
import numpy as np
from tkinter import ttk, scrolledtext, messagebox
import logging
from moduls.export_to_excel import ExcelExporter
from moduls.table_sort import sort_treeview_column, sort_competence_type_column  
from gui.graph_tab import load_graph_program_table  


def create_rating_history_tab(frame, app):
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=True, pady=5)

    program_vacancy_frame = tk.LabelFrame(main_frame, text="Образовательная программа и оцениваемая вакансия")
    program_vacancy_frame.pack(fill="both", expand=True, padx=5, pady=5)

    app.program_vacancy_history_table = ttk.Treeview(program_vacancy_frame, columns=("educational_program", "university", "year", "vacancy", "assessment_date"), show="headings",height=6)
    app.program_vacancy_history_table.heading("educational_program", text="Образовательная программа", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "educational_program", False))
    app.program_vacancy_history_table.heading("university", text="ВУЗ", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "university", False))
    app.program_vacancy_history_table.heading("year", text="Год", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "year", False))
    app.program_vacancy_history_table.heading("vacancy", text="Вакансия", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "vacancy", False))
    app.program_vacancy_history_table.heading("assessment_date", text="Дата и время анализа", command=lambda: sort_treeview_column(app.program_vacancy_history_table, "assessment_date", False))
    app.program_vacancy_history_table.column("educational_program", width=300)
    app.program_vacancy_history_table.column("university", width=80)
    app.program_vacancy_history_table.column("year", width=80)
    app.program_vacancy_history_table.column("vacancy", width=250)
    app.program_vacancy_history_table.column("assessment_date", width=150)
    app.program_vacancy_history_table.pack(fill="both", expand=True)
    app.program_vacancy_history_table.bind("<<TreeviewSelect>>", lambda event: update_competence_history_table(app))

    competence_frame = tk.LabelFrame(main_frame, text="Оценка компетенций образовательной программы")
    competence_frame.pack(fill="both", expand=True, padx=5, pady=5)

    app.competence_history_table = ttk.Treeview(competence_frame, columns=("competence", "competence_type", "score"), show="headings", height=6)
    app.competence_history_table.heading("competence", text="Компетенция")
    app.competence_history_table.heading("competence_type", text="Вид компетенции", command=lambda: sort_competence_type_column(app.competence_history_table, "competence_type"))
    app.competence_history_table.heading("score", text="Оценка")
    app.competence_history_table.column("competence", width=650)
    app.competence_history_table.column("competence_type", width=160)
    app.competence_history_table.column("score", width=50)
    app.competence_history_table.pack(fill="both", expand=True)

    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)
    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_history_frame = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_history_frame.pack(pady=4)

    export_frame = tk.Frame(main_frame)
    export_frame.pack(pady=4, fill="both", expand=False)
    app.export_history_button = tk.Button(export_frame, text="Экспорт в Excel", command=lambda: export_history_to_excel(app))
    app.export_history_button.pack(side=tk.LEFT, padx=5)
    app.delete_history_button = tk.Button(export_frame, text="Удалить", command=lambda: delete_assessment_table(app))
    app.delete_history_button.pack(side=tk.LEFT, padx=5)

    load_program_vacancy_history_table(app)

def export_history_to_excel(app):
    """Экспорт данных из таблиц истории в Excel."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        logging.error("Ошибка: Выберите запись для экспорта!")
        return

    values = app.program_vacancy_history_table.item(selected_item[0])["values"]
    educational_program_name, university_short, year, vacancy_name, assessment_date = values

    try:
        results = app.logic.db.fetch_assessment_results(educational_program_name, vacancy_name, assessment_date)
        exporter = ExcelExporter(
            results,
            program_name=educational_program_name,
            vacancy_name=vacancy_name,
            university=university_short,
            year=year
        )
        message = exporter.export_history_to_excel()  
        if "успешно экспортированы" in message:
            logging.info(message)
        else:
            logging.error(message)
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}", exc_info=True)

def load_program_vacancy_history_table(app):
    try:
        app.program_vacancy_history_table.delete(*app.program_vacancy_history_table.get_children())
        rows = app.logic.db.fetch_program_vacancy_history()
        logging.info(f"Загружено {len(rows)} строк из таблицы assessment")
        for row in rows:
            program_name, university_short, year, vacancy_name, assessment_date = row
            year = year if year else "" 
            assessment_date_str = assessment_date if assessment_date else "Не указана"
            app.program_vacancy_history_table.insert("", tk.END, values=(program_name, university_short, year, vacancy_name, assessment_date_str))
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
    educational_program_name, _, _, vacancy_name, assessment_date = values

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
    educational_program_name, _, _, vacancy_name, assessment_date = values

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

def delete_assessment_table(app):
    """Удаление выбранной записи из таблицы assessment."""
    selected_item = app.program_vacancy_history_table.selection()
    if not selected_item:
        logging.error("Ошибка: Выберите запись для удаления!")
        return

    values = app.program_vacancy_history_table.item(selected_item[0])["values"]
    if len(values) != 5:
        logging.error(f"Ошибка: Неверное количество значений в строке: ожидалось 5, получено {len(values)}: {values}")
        return

    # Извлекаем только нужные поля для удаления из базы данных
    educational_program_name = values[0]  # educational_program
    vacancy_name = values[3]            # vacancy
    assessment_date = values[4]         # assessment_date

    try:
        logging.info(f"Попытка удалить запись: {educational_program_name}, {vacancy_name}, {assessment_date}")
        if app.logic.db.delete_assessment(educational_program_name, vacancy_name, assessment_date):
            # Удаляем строку из таблицы интерфейса (все столбцы, включая university и year)
            app.program_vacancy_history_table.delete(selected_item[0])
            app.group_scores_history_frame.delete(1.0, tk.END)
            app.refresh_graph_table()  # Обновляем таблицу на вкладке "Графики"
            logging.info(f"Запись '{educational_program_name} - {vacancy_name} - {assessment_date}' удалена из assessment")
            logging.info("Успех: Запись успешно удалена!")
        else:
            logging.error("Ошибка: Не удалось удалить запись! Проверьте логи для подробностей.")
    except Exception as e:
        logging.error(f"Ошибка удаления: {e}")

    load_graph_program_table(app)