import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import logging


def create_assessment_tab(frame, app):
    # Главный фрейм
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=False)

    # Контейнер для таблиц результатов и общей информации
    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)

    # Фрейм для результатов анализа
    skill_results_frame = tk.LabelFrame(results_container, text="Результаты оценки компетенций:")
    skill_results_frame.pack(fill="both", expand=False)
    
    # Таблица для фрейма 
    app.skill_results_table = ttk.Treeview(skill_results_frame, columns=("competence", "type_competence", "score"), show="headings", height=13)
    app.skill_results_table.heading("competence", text="Компетенция")
    app.skill_results_table.heading("type_competence", text="Тип компетенции")
    app.skill_results_table.heading("score", text="Оценка")
    app.skill_results_table.column("competence", width=400)
    app.skill_results_table.column("type_competence", width=300)
    app.skill_results_table.column("score", width=150)
    app.skill_results_table.pack(pady=4, fill="x")  # Уменьшен pady для минимального расстояния
    app.skill_results_table = app.skill_results_table  # Сохраняем как атрибут

    start_analysis_frame = tk.Frame(main_frame)
    start_analysis_frame.pack(pady=4, fill="x")
    app.run_button = tk.Button(start_analysis_frame, text="Запустить анализ", command=app.start_analysis)
    app.run_button.pack()

    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп компетенций и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_area = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_area.pack(pady=4)
    app.group_scores_area = app.group_scores_area  # Сохраняем как атрибут

    # Фрейм для сохранения строк
    export_frame = tk.Frame(main_frame)
    export_frame.pack(pady=4, fill="both", expand=False) 
    app.export_button = tk.Button(export_frame, text="Экспорт в Excel", command=app.logic.export_results_to_excel)
    app.export_button.pack()

    # Фрейм для кнопки сохранения результатов
    save_results_frame = tk.Frame(main_frame)
    save_results_frame.pack(pady=4, fill="x")
    app.save_results_button = tk.Button(save_results_frame, text="Сохранить результаты оценивания", command=lambda: save_assessment_results(app))
    app.save_results_button.pack()

# Добавляем новую функцию для сохранения результатов
def save_assessment_results(app):
    """Сохранение результатов оценки в таблицу assessment."""
    if not app.program_id or not app.selected_vacancy_id or not app.logic.results:
        app.show_error("Сначала выполните анализ!")
        return

    try:
        # Получаем данные из результатов анализа
        results = app.logic.results["similarity_results"]
        assessment_date = datetime.now().strftime("%Y-%m-%d")

        for competence, (score, type_competence) in results.items():
            # Предполагаем, что competence и type_competence нужно сопоставить с ID из БД
            # Это упрощённая логика, предполагает наличие competence_id и type_competence_id
            competence_data = app.logic.db.fetch_competence_by_name(competence)
            if not competence_data:
                app.show_error(f"Компетенция '{competence}' не найдена в БД!")
                continue
            competence_id, _, type_competence_id = competence_data

            # Сохранение в таблицу assessment
            query = """
                INSERT INTO public.assessment (
                    competence_id, type_competence_id, educational_program_id, vacancy_id, 
                    assessment_date, value
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING assessment_id;
            """
            app.logic.db.cursor.execute(query, (
                competence_id, type_competence_id, app.program_id, app.selected_vacancy_id,
                assessment_date, float(score)
            ))
            assessment_id = app.logic.db.cursor.fetchone()[0]
            app.logic.db.connection.commit()
            logging.info(f"Сохранена оценка (ID: {assessment_id}) для компетенции '{competence}'")

        app.show_info("Результаты успешно сохранены в таблице assessment!")
    except Exception as e:
        app.show_error(f"Ошибка при сохранении результатов: {e}")
        logging.error(f"Ошибка при сохранении в assessment: {e}")
        app.logic.db.connection.rollback()