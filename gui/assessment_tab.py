import tkinter as tk
from tkinter import ttk, scrolledtext

def create_assessment_tab(frame, app):
    # Кнопка для запуска анализа
    app.run_button = tk.Button(frame, text="Запустить анализ", command=app.start_analysis)
    app.run_button.pack()

    # Кнопка для экспорта результатов в Excel
    app.export_button = tk.Button(frame, text="Экспорт в Excel", command=app.logic.export_results_to_excel)
    app.export_button.pack()

    # Таблица для вывода результатов оценки компетенций
    app.skill_results_label = tk.Label(frame, text="Результаты оценки компетенций:")
    app.skill_results_label.pack(pady=5)

    app.skill_results_table = ttk.Treeview(frame, columns=("competence", "type_competence", "score"), show="headings")
    app.skill_results_table.heading("competence", text="Компетенция")
    app.skill_results_table.heading("type_competence", text="Тип компетенции")
    app.skill_results_table.heading("score", text="Оценка")
    app.skill_results_table.column("competence", width=400)
    app.skill_results_table.column("type_competence", width=300)
    app.skill_results_table.column("score", width=150)
    app.skill_results_table.pack(pady=5)
    app.skill_results_table = app.skill_results_table  # Сохраняем как атрибут

    # Поле для вывода оценок групп компетенций и общей оценки
    app.group_scores_label = tk.Label(frame, text="Оценки групп компетенций и программы:")
    app.group_scores_label.pack(pady=5)
    app.group_scores_area = scrolledtext.ScrolledText(frame, width=120, height=5)
    app.group_scores_area.pack()
    app.group_scores_area = app.group_scores_area  # Сохраняем как атрибут