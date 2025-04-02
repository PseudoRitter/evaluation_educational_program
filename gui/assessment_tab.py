import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from .assessment_history_tab import refresh_history_tables
from moduls.table_processing import sort_treeview_column, sort_competence_type_column, add_tooltip_to_treeview
import logging
from gui.graph_tab import load_graph_program_table  

def create_assessment_tab(frame, app):
    main_frame = tk.Frame(frame)
    main_frame.pack(fill="both", expand=False)

    run_frame = tk.Frame(main_frame)
    run_frame.pack(pady=4, fill="x")
    
    app.run_button = tk.Button(run_frame, text="Запустить анализ", command=app.start_analysis)
    app.run_button.pack(side="left", padx=5)

    app.save_results_button = tk.Button(run_frame, text="Сохранить результаты в историю", command=lambda: save_assessment_results(app))
    app.save_results_button.pack(side=tk.LEFT, padx=5)

    control_frame = tk.Frame(main_frame)
    control_frame.pack(pady=4, fill="x")

    threshold_frame = ttk.LabelFrame(control_frame, text="Настройки")
    threshold_frame.pack(side="left", padx=5, pady=5)

    threshold_label = ttk.Label(threshold_frame, text="Значение для графика накопления:")
    threshold_label.pack(side="left", padx=5)

    app.threshold_entry = ttk.Entry(threshold_frame, width=10)
    app.threshold_entry.insert(0, "0.5")
    app.threshold_entry.pack(side="left", padx=5)

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

    weights_frame = ttk.LabelFrame(control_frame, text="Веса компетенций")
    weights_frame.pack(side="left", padx=5, pady=5)

    app.use_weights_var = tk.BooleanVar(value=False)
    use_weights_check = ttk.Checkbutton(weights_frame, text="Использовать веса", variable=app.use_weights_var, command=lambda: update_weights(app))
    use_weights_check.pack(side="left", padx=5)

    uni_label = ttk.Label(weights_frame, text="Универсальные:")
    uni_label.pack(side="left", padx=5)
    app.uni_weight_entry = ttk.Entry(weights_frame, width=5)
    app.uni_weight_entry.insert(0, "0.2")
    app.uni_weight_entry.pack(side="left", padx=5)

    gen_label = ttk.Label(weights_frame, text="Общепроф.:")
    gen_label.pack(side="left", padx=5)
    app.gen_weight_entry = ttk.Entry(weights_frame, width=5)
    app.gen_weight_entry.insert(0, "0.4")
    app.gen_weight_entry.pack(side="left", padx=5)

    prof_label = ttk.Label(weights_frame, text="Проф.:")
    prof_label.pack(side="left", padx=5)
    app.prof_weight_entry = ttk.Entry(weights_frame, width=5)
    app.prof_weight_entry.insert(0, "0.4")
    app.prof_weight_entry.pack(side="left", padx=5)

    def validate_weight(value):
        if value == "":
            return True
        try:
            val = float(value)
            return 0 <= val <= 1
        except ValueError:
            return False

    wcmd = (frame.register(validate_weight), '%P')
    app.uni_weight_entry.configure(validate="key", validatecommand=wcmd)
    app.gen_weight_entry.configure(validate="key", validatecommand=wcmd)
    app.prof_weight_entry.configure(validate="key", validatecommand=wcmd)

    app.uni_weight_entry.bind("<FocusOut>", lambda event: update_weights(app))
    app.gen_weight_entry.bind("<FocusOut>", lambda event: update_weights(app))
    app.prof_weight_entry.bind("<FocusOut>", lambda event: update_weights(app))

    results_container = tk.Frame(main_frame)
    results_container.pack(pady=4, fill="both", expand=False)

    skill_results_frame = tk.LabelFrame(results_container, text="Результаты оценки компетенций:")
    skill_results_frame.pack(fill="both", expand=False)

    app.skill_results_table = ttk.Treeview(skill_results_frame, columns=("competence", "competence_type", "score"), show="headings", height=17)
    app.skill_results_table.heading("competence", text="Компетенция")
    app.skill_results_table.heading("competence_type", text="Вид компетенции", command=lambda: sort_competence_type_column(app.skill_results_table, "competence_type"))
    app.skill_results_table.heading("score", text="Оценка")
    app.skill_results_table.column("competence", width=650)
    app.skill_results_table.column("competence_type", width=120)
    app.skill_results_table.column("score", width=80)
    app.skill_results_table.pack(pady=4, fill="x")

    add_tooltip_to_treeview(app.skill_results_table)

    app.export_button = tk.Button(run_frame, text="Экспорт в Excel", command=lambda: app.logic.export_results_to_excel(app))
    app.export_button.pack(side=tk.LEFT, padx=5)

    group_scores_frame = tk.LabelFrame(results_container, text="Оценки групп и программы:")
    group_scores_frame.pack(pady=4, fill="both", expand=False)
    app.group_scores_area = scrolledtext.ScrolledText(group_scores_frame, width=120, height=8)
    app.group_scores_area.pack(pady=4)

def update_weights(app):
    """Пересчет групповых и общей оценки с учетом весов."""
    if not hasattr(app.logic, "results") or not app.logic.results:
        app.show_error("Сначала выполните анализ!")
        return

    results = app.logic.results
    use_weights = app.use_weights_var.get()
    weights = None
    if use_weights:
        try:
            weights = {
                "Универсальная компетенция": float(app.uni_weight_entry.get() or "0.2"),
                "Общепрофессиональная компетенция": float(app.gen_weight_entry.get() or "0.4"),
                "Профессиональная компетенция": float(app.prof_weight_entry.get() or "0.4")
            }
            total_weight = sum(weights.values())
            if not abs(total_weight - 1.0) < 1e-6:
                app.show_error(f"Сумма весов должна равняться 1, текущая сумма: {total_weight:.2f}")
                return
            for key, val in weights.items():
                if not (0 <= val <= 1):
                    app.show_error(f"Вес для {key} должен быть от 0 до 1!")
                    return
        except ValueError:
            app.show_error("Введите корректные числовые значения для весов (от 0 до 1)!")
            return

    overall_score, weighted_group_scores = app.logic.calculate_overall_score(results["group_scores"], use_weights, weights)

    app.group_scores_area.delete(1.0, tk.END)
    app.group_scores_area.insert(tk.END, "Оценки групп компетенций:\n")
    for ctype, score in (weighted_group_scores if use_weights else results["group_scores"]).items():
        app.group_scores_area.insert(tk.END, f"{ctype}: {score:.6f}\n")
    app.group_scores_area.insert(tk.END, f"\nОбщая оценка программы: {overall_score:.6f}\n")

def save_assessment_results(app):
    """Сохранение результатов анализа в базу данных."""
    if not hasattr(app.logic, "results") or not app.logic.results:
        app.show_error("Сначала выполните анализ!")
        return

    results = app.logic.results.get("similarity_results", {})
    if not results:
        app.show_error("Нет данных для сохранения!")
        return

    success = app.logic.db.save_assessment_results(app.program_id, app.selected_vacancy_id, results)
    if success:
        app.show_info("Результаты сохранены в таблице assessment в невзвешенном формате!")
        refresh_history_tables(app)
        load_graph_program_table(app)
    else:
        app.show_error("Ошибка при сохранении результатов в базу данных!")