import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from .assessment_history_tab import refresh_history_tables
from moduls.table_sort import sort_treeview_column  

import logging

def create_assessment_tab(frame, app):
    """Создание вкладки для отображения результатов анализа компетенций."""
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=False)

    # Контейнер результатов
    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)

    # Таблица результатов компетенций
    skill_results_frame = tk.LabelFrame(results_container, text="Результаты оценки компетенций:")
    skill_results_frame.pack(fill="both", expand=False)

    app.skill_results_table = ttk.Treeview(
        skill_results_frame,
        columns=("competence", "type_competence", "score"),
        show="headings",
        height=13
    )
    app.skill_results_table.heading("competence", text="Компетенция",command=lambda: sort_treeview_column(app.skill_results_table, "competence", False))
    app.skill_results_table.heading("type_competence", text="Тип компетенции", command=lambda: sort_treeview_column(app.skill_results_table, "type_competence", False))
    app.skill_results_table.heading("score", text="Оценка")
    app.skill_results_table.column("competence", width=400)
    app.skill_results_table.column("type_competence", width=300)
    app.skill_results_table.column("score", width=150)
    app.skill_results_table.pack(pady=4, fill="x")

    # Кнопка запуска анализа
    start_analysis_frame = tk.Frame(main_frame)
    start_analysis_frame.pack(pady=4, fill="x")
    app.run_button = tk.Button(start_analysis_frame, text="Запустить анализ", command=app.start_analysis)
    app.run_button.pack()

    # Оценки групп и программы
    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_area = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_area.pack(pady=4)

    # Кнопка экспорта
    export_frame = tk.Frame(main_frame)
    export_frame.pack(pady=4, fill="both", expand=False)
    app.export_button = tk.Button(export_frame, text="Экспорт в Excel", command=lambda: app.logic.export_results_to_excel(app))
    app.export_button.pack()

    # Кнопка сохранения результатов
    save_results_frame = tk.Frame(main_frame)
    save_results_frame.pack(pady=4, fill="x")
    app.save_results_button = tk.Button(save_results_frame, text="Сохранить результаты в историю", command=lambda: save_assessment_results(app))
    app.save_results_button.pack()

def save_assessment_results(app):
    """Сохранение результатов анализа в таблицу assessment."""
    if not hasattr(app.logic, "results") or not app.logic.results:
        app.show_error("Сначала выполните анализ!")
        return

    results = app.logic.results.get("similarity_results", {})
    if not results:
        app.show_error("Нет данных для сохранения!")
        return

    try:
        assessment_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = app.logic.db.get_connection()
        with conn.cursor() as cursor:
            for competence, (score, type_competence) in results.items():
                competence_data = app.logic.db.fetch_competence_by_name(competence)
                if not competence_data:
                    logging.error(f"Компетенция '{competence}' не найдена!")
                    continue
                competence_id, _, type_competence_id = competence_data

                cursor.execute("""
                    INSERT INTO public.assessment (
                        competence_id, type_competence_id, educational_program_id, vacancy_id,
                        assessment_date, value
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING assessment_id;
                """, (competence_id, type_competence_id, app.program_id, app.selected_vacancy_id, assessment_date, float(score)))
                assessment_id = cursor.fetchone()[0]
                logging.info(f"Сохранена оценка ID: {assessment_id} для '{competence}'")
            conn.commit()
        app.show_info("Результаты сохранены в таблице assessment!")
    except Exception as e:
        app.show_error(f"Ошибка сохранения: {e}")
        logging.error(f"Ошибка сохранения результатов: {e}", exc_info=True)
        if "conn" in locals():
            conn.rollback()
    finally:
        if "conn" in locals():
            app.logic.db.release_connection(conn)

    refresh_history_tables(app)