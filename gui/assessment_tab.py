import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from .assessment_history_tab import refresh_history_tables
from moduls.table_sort import sort_treeview_column, sort_competence_type_column  
import logging
from gui.graph_tab import load_graph_program_table  

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from .assessment_history_tab import refresh_history_tables
from moduls.table_sort import sort_treeview_column, sort_competence_type_column  
import logging
from gui.graph_tab import load_graph_program_table  

def create_assessment_tab(frame, app):
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=False)

    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)

    skill_results_frame = tk.LabelFrame(results_container, text="Результаты оценки компетенций:")
    skill_results_frame.pack(fill="both", expand=False)

    app.skill_results_table = ttk.Treeview(skill_results_frame, columns=("competence", "competence_type", "score"), show="headings", height=13)
    app.skill_results_table.heading("competence", text="Компетенция")
    app.skill_results_table.heading("competence_type", text="Вид компетенции", command=lambda: sort_competence_type_column(app.skill_results_table, "competence_type"))
    app.skill_results_table.heading("score", text="Оценка")
    app.skill_results_table.column("competence", width=650)
    app.skill_results_table.column("competence_type", width=120)
    app.skill_results_table.column("score", width=80)
    app.skill_results_table.pack(pady=4, fill="x")

    # Фрейм для кнопки запуска анализа
    start_analysis_frame = tk.Frame(main_frame)
    start_analysis_frame.pack(pady=4, fill="x")

    # Кнопка запуска анализа
    app.run_button = tk.Button(start_analysis_frame, text="Запустить анализ", command=app.start_analysis)
    app.run_button.pack()

    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_area = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_area.pack(pady=4)

    export_frame = tk.Frame(main_frame)
    export_frame.pack(pady=4, fill="both", expand=False)
    app.export_button = tk.Button(export_frame, text="Экспорт в Excel", command=lambda: app.logic.export_results_to_excel(app))
    app.export_button.pack()

    save_results_frame = tk.Frame(main_frame)
    save_results_frame.pack(pady=4, fill="x")
    app.save_results_button = tk.Button(save_results_frame, text="Сохранить результаты в историю", command=lambda: save_assessment_results(app))
    app.save_results_button.pack()

    threshold_frame = ttk.LabelFrame(frame, text="Настройки")
    threshold_frame.pack()

    threshold_label = ttk.Label(threshold_frame, text="Значение для графика накопления:")
    threshold_label.pack()

    app.threshold_entry = ttk.Entry(threshold_frame, width=10)
    app.threshold_entry.insert(0, "0.5")  
    app.threshold_entry.pack(padx=5)

    def validate_threshold(value):
        if value == "":
            return True
        try:
            val = float(value)
            return 0 <= val <= 1
        except ValueError:
            return False

    vcmd = (frame.register(validate_threshold), '%P')
    app.threshold_entry.configure(validate="key", validatecommand=vcmd)

def save_assessment_results(app):
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

                if not app.logic.db.ensure_competence_program_link(competence_id, type_competence_id, app.program_id):
                    logging.error(f"Не удалось создать связь для '{competence}'")
                    continue

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
    load_graph_program_table(app)