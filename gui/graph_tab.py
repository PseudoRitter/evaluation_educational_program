import tkinter as tk
import tkinter.ttk as ttk
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from moduls.table_sort import sort_treeview_column

def create_graph_tab(graph_frame, app):
    """Создание вкладки 'Графики' с двумя подвкладками."""
    notebook = ttk.Notebook(graph_frame)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Сравнение ОП и Вакансий")
    create_comparison_op_vacancies_tab(tab1, app)

    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Сравнение Вакансий и ОП")
    create_comparison_vacancies_op_tab(tab2, app)

def create_comparison_op_vacancies_tab(frame, app):
    """Создание содержимого вкладки 'Сравнение ОП и Вакансий'."""
    program_frame = ttk.LabelFrame(frame, text="Выберите ОП для графиков")
    program_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    columns = ("program_name", "program_code", "university", "year")
    app.graph_program_table = ttk.Treeview(program_frame, columns=columns, show="headings", height=5)
    app.graph_program_table.pack(fill="both", expand=True, padx=5, pady=5)
    
    app.graph_program_table.heading("program_name", text="Название ОП", command=lambda: sort_treeview_column(app.graph_program_table, "program_name"))
    app.graph_program_table.heading("program_code", text="Код", command=lambda: sort_treeview_column(app.graph_program_table, "program_code"))
    app.graph_program_table.heading("university", text="ВУЗ", command=lambda: sort_treeview_column(app.graph_program_table, "university"))
    app.graph_program_table.heading("year", text="Год", command=lambda: sort_treeview_column(app.graph_program_table, "year"))
    
    app.graph_program_table.column("program_name", width=300)
    app.graph_program_table.column("program_code", width=100)
    app.graph_program_table.column("university", width=150)
    app.graph_program_table.column("year", width=50)
    
    app.graph_program_table.bind("<<TreeviewSelect>>", lambda event: on_program_select(app))
    
    app.vacancy_frame = ttk.LabelFrame(frame, text="Выберите вакансии")
    app.vacancy_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    vacancy_columns = ("vacancy_name", "assessment_date")
    app.vacancy_table = ttk.Treeview(app.vacancy_frame, columns=vacancy_columns, show="headings", selectmode="extended", height=5)
    app.vacancy_table.pack(fill="both", expand=True, padx=5, pady=5)
    
    app.vacancy_table.heading("vacancy_name", text="Название вакансии", command=lambda: sort_treeview_column(app.vacancy_table, "vacancy_name"))
    app.vacancy_table.heading("assessment_date", text="Дата оценки", command=lambda: sort_treeview_column(app.vacancy_table, "assessment_date"))
    
    app.vacancy_table.column("vacancy_name", width=300)
    app.vacancy_table.column("assessment_date", width=200)
    
    app.graph_button = ttk.Button(frame, text="Отобразить график", command=lambda: display_graph_op_vacancies(app))
    app.graph_button.pack(pady=5)
    
    app.graph_canvas_frame = ttk.Frame(frame)
    app.graph_canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    load_graph_program_table(app)

def load_graph_program_table(app):
    """Загрузка списка ОП с оценками в таблицу."""
    for item in app.graph_program_table.get_children():
        app.graph_program_table.delete(item)
    
    try:
        history = app.logic.db.fetch_program_vacancy_history()
        unique_programs = {}
        for program_name, univ_short_name, year, _, _ in history:
            key = (program_name, univ_short_name, year)
            if key not in unique_programs:
                program_code = app.logic.db.fetch_program_code(program_name, year, univ_short_name)
                unique_programs[key] = (program_name, program_code, univ_short_name, year)
        
        for program_name, program_code, univ_short_name, year in unique_programs.values():
            app.graph_program_table.insert("", "end", values=(program_name, program_code, univ_short_name, year))
        logging.info("Таблица ОП для графиков успешно загружена")
    except Exception as e:
        logging.error(f"Ошибка загрузки таблицы ОП для графиков: {e}")

def on_program_select(app):
    """Обработка выбора ОП и загрузка связанных вакансий."""
    selected = app.graph_program_table.selection()
    if not selected:
        return
    
    for item in app.vacancy_table.get_children():
        app.vacancy_table.delete(item)
    
    values = app.graph_program_table.item(selected[0], "values")
    program_name, _, univ_short_name, year = values
    
    try:
        history = app.logic.db.fetch_program_vacancy_history()
        for p_name, u_name, p_year, vacancy_name, assessment_date in history:
            if p_name == program_name and u_name == univ_short_name and p_year == year:
                app.vacancy_table.insert("", "end", values=(vacancy_name, assessment_date))
        logging.info(f"Загружены вакансии для ОП: {program_name}")
    except Exception as e:
        logging.error(f"Ошибка загрузки вакансий: {e}")

def display_graph_op_vacancies(app):
    """Построение графиков для выбранных вакансий в отдельном окне."""
    selected_program = app.graph_program_table.selection()
    if not selected_program:
        logging.error("Ошибка: Выберите образовательную программу!")
        return
    
    selected_vacancies = app.vacancy_table.selection()
    if not selected_vacancies:
        logging.error("Ошибка: Выберите хотя бы одну вакансию!")
        return
    
    program_values = app.graph_program_table.item(selected_program[0], "values")
    program_name, program_code, university, year = program_values
    
    vacancy_data = []
    for vacancy_item in selected_vacancies:
        vacancy_name, assessment_date = app.vacancy_table.item(vacancy_item, "values")
        results = app.logic.db.fetch_assessment_results(program_name, vacancy_name, assessment_date)
        
        group_scores = results.get("group_scores", {})
        overall_score = results.get("overall_score", 0.0)
        vacancy_data.append({
            "name": vacancy_name,
            "group_scores": group_scores,
            "overall_score": overall_score
        })
    
    competence_types = sorted(set().union(*[d["group_scores"].keys() for d in vacancy_data]))
    if len(competence_types) > 3:
        logging.warning(f"Более 3 видов компетенций ({len(competence_types)}), будут использованы только первые 3.")
        competence_types = competence_types[:3]
    
    all_scores = []
    for vacancy in vacancy_data:
        scores = [vacancy["group_scores"].get(ctype, 0.0) for ctype in competence_types] + [vacancy["overall_score"]]
        all_scores.extend(scores)
    y_min = max(0, min(all_scores) - 0.05)
    y_max = min(1, max(all_scores) + 0.05)
    
    graph_window = tk.Toplevel(app.root)
    graph_window.title("График соответствия ОП и вакансий")
    graph_window.geometry("800x600")
    
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    colors = ["#FFA500", "#0000FF", "#008000", "#FF0000"]
    bar_width = 0.12
    n_bars = len(competence_types) + 1
    
    total_bars = len(vacancy_data) * n_bars
    x = np.arange(total_bars)
    offsets = np.zeros(total_bars)
    for i in range(len(vacancy_data)):
        start_idx = i * n_bars
        end_idx = start_idx + n_bars
        group_offset = i * (n_bars * bar_width + bar_width * 1.5)
        offsets[start_idx:end_idx] = np.arange(n_bars) * bar_width + group_offset
    
    for i, vacancy in enumerate(vacancy_data):
        start_idx = i * n_bars
        end_idx = start_idx + n_bars
        scores = [vacancy["group_scores"].get(ctype, 0.0) for ctype in competence_types] + [vacancy["overall_score"]]
        bars = ax.bar(offsets[start_idx:end_idx], scores, bar_width, color=[colors[j % len(colors)] for j in range(n_bars)])
        
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.2f}", ha="center", va="bottom", fontsize=8)
    
    ax.set_ylim(y_min, y_max)
    ax.set_xticks(offsets[n_bars // 2::n_bars])
    ax.set_xticklabels([d["name"] for d in vacancy_data], rotation=45, ha="right")
    ax.set_ylabel("Оценка")
    
    legend_labels = competence_types + ["Средняя оценка"]
    ax.legend(labels=legend_labels, handles=[
        plt.Rectangle((0, 0), 1, 1, color=colors[j % len(colors)]) for j in range(len(legend_labels))
    ], loc="upper right", title="Компетенции")
    
    fig.suptitle(f"{program_name} ({program_code}), {university}", fontsize=14)
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    logging.info(f"Графики построены для {len(vacancy_data)} вакансий")

def create_comparison_vacancies_op_tab(frame, app):
    """Создание содержимого вкладки 'Сравнение Вакансий и ОП'."""
    vacancy_frame = ttk.LabelFrame(frame, text="Выберите вакансию для графиков")
    vacancy_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    columns = ("vacancy_name",)
    app.graph_vacancy_table = ttk.Treeview(vacancy_frame, columns=columns, show="headings", height=5)
    app.graph_vacancy_table.pack(fill="both", expand=True, padx=5, pady=5)
    
    app.graph_vacancy_table.heading("vacancy_name", text="Название вакансии", command=lambda: sort_treeview_column(app.graph_vacancy_table, "vacancy_name"))
    
    app.graph_vacancy_table.column("vacancy_name", width=450)
    
    app.graph_vacancy_table.bind("<<TreeviewSelect>>", lambda event: on_vacancy_select(app))
    
    app.program_frame = ttk.LabelFrame(frame, text="Выберите образовательные программы")
    app.program_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    program_columns = ("program_name", "program_code", "university", "year")
    app.program_table = ttk.Treeview(app.program_frame, columns=program_columns, show="headings", selectmode="extended", height=5)
    app.program_table.pack(fill="both", expand=True, padx=5, pady=5)
    
    app.program_table.heading("program_name", text="Название ОП", command=lambda: sort_treeview_column(app.program_table, "program_name"))
    app.program_table.heading("program_code", text="Код", command=lambda: sort_treeview_column(app.program_table, "program_code"))
    app.program_table.heading("university", text="ВУЗ", command=lambda: sort_treeview_column(app.program_table, "university"))
    app.program_table.heading("year", text="Год", command=lambda: sort_treeview_column(app.program_table, "year"))
    
    app.program_table.column("program_name", width=300)
    app.program_table.column("program_code", width=100)
    app.program_table.column("university", width=150)
    app.program_table.column("year", width=50)
    
    app.graph_button_vacancies = ttk.Button(frame, text="Отобразить график", command=lambda: display_graph_vacancies_op(app))
    app.graph_button_vacancies.pack(pady=5)
    
    app.graph_canvas_frame_vacancies = ttk.Frame(frame)
    app.graph_canvas_frame_vacancies.pack(fill="both", expand=True, padx=10, pady=5)
    
    load_graph_vacancy_table(app)

def load_graph_vacancy_table(app):
    """Загрузка списка вакансий с оценками в таблицу."""
    for item in app.graph_vacancy_table.get_children():
        app.graph_vacancy_table.delete(item)
    
    try:
        history = app.logic.db.fetch_program_vacancy_history()
        unique_vacancies = set()
        for _, _, _, vacancy_name, _ in history:
            unique_vacancies.add(vacancy_name)
        
        for vacancy_name in unique_vacancies:
            app.graph_vacancy_table.insert("", "end", values=(vacancy_name,))
        logging.info("Таблица вакансий для графиков успешно загружена")
    except Exception as e:
        logging.error(f"Ошибка загрузки таблицы вакансий для графиков: {e}")

def on_vacancy_select(app):
    """Обработка выбора вакансии и загрузка связанных ОП."""
    selected = app.graph_vacancy_table.selection()
    if not selected:
        return
    
    for item in app.program_table.get_children():
        app.program_table.delete(item)
    
    values = app.graph_vacancy_table.item(selected[0], "values")
    vacancy_name = values[0]
    
    try:
        history = app.logic.db.fetch_program_vacancy_history()
        for program_name, univ_short_name, year, v_name, _ in history:
            if v_name == vacancy_name:
                program_code = app.logic.db.fetch_program_code(program_name, year, univ_short_name)
                app.program_table.insert("", "end", values=(program_name, program_code, univ_short_name, year))
        logging.info(f"Загружены ОП для вакансии: {vacancy_name}")
    except Exception as e:
        logging.error(f"Ошибка загрузки ОП: {e}")

def display_graph_vacancies_op(app):
    """Построение графиков для выбранных ОП в отдельном окне."""
    selected_vacancy = app.graph_vacancy_table.selection()
    if not selected_vacancy:
        logging.error("Ошибка: Выберите вакансию!")
        return
    
    selected_programs = app.program_table.selection()
    if not selected_programs:
        logging.error("Ошибка: Выберите хотя бы одну образовательную программу!")
        return
    
    vacancy_values = app.graph_vacancy_table.item(selected_vacancy[0], "values")
    vacancy_name = vacancy_values[0]
    
    history = app.logic.db.fetch_program_vacancy_history()
    assessment_date = next((a_date for _, _, _, v_name, a_date in history if v_name == vacancy_name), "2025-03-10 00:00")
    
    program_data = []
    for program_item in selected_programs:
        program_name, program_code, university, year = app.program_table.item(program_item, "values")
        results = app.logic.db.fetch_assessment_results(program_name, vacancy_name, assessment_date)
        
        group_scores = results.get("group_scores", {})
        overall_score = results.get("overall_score", 0.0)
        program_data.append({
            "name": program_name,
            "group_scores": group_scores,
            "overall_score": overall_score
        })
    
    competence_types = sorted(set().union(*[d["group_scores"].keys() for d in program_data]))
    if len(competence_types) > 3:
        logging.warning(f"Более 3 видов компетенций ({len(competence_types)}), будут использованы только первые 3.")
        competence_types = competence_types[:3]
    
    all_scores = []
    for program in program_data:
        scores = [program["group_scores"].get(ctype, 0.0) for ctype in competence_types] + [program["overall_score"]]
        all_scores.extend(scores)
    y_min = max(0, min(all_scores) - 0.05)
    y_max = min(1, max(all_scores) + 0.05)
    
    graph_window = tk.Toplevel(app.root)
    graph_window.title("График соответствия вакансии и ОП")
    graph_window.geometry("800x600")
    
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    colors = ["#FFA500", "#0000FF", "#008000", "#FF0000"]
    bar_width = 0.12
    n_bars = len(competence_types) + 1
    
    total_bars = len(program_data) * n_bars
    x = np.arange(total_bars)
    offsets = np.zeros(total_bars)
    for i in range(len(program_data)):
        start_idx = i * n_bars
        end_idx = start_idx + n_bars
        group_offset = i * (n_bars * bar_width + bar_width * 1.5)
        offsets[start_idx:end_idx] = np.arange(n_bars) * bar_width + group_offset
    
    for i, program in enumerate(program_data):
        start_idx = i * n_bars
        end_idx = start_idx + n_bars
        scores = [program["group_scores"].get(ctype, 0.0) for ctype in competence_types] + [program["overall_score"]]
        bars = ax.bar(offsets[start_idx:end_idx], scores, bar_width, color=[colors[j % len(colors)] for j in range(n_bars)])
        
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.2f}", ha="center", va="bottom", fontsize=8)
    
    ax.set_ylim(y_min, y_max)
    ax.set_xticks(offsets[n_bars // 2::n_bars])
    ax.set_xticklabels([d["name"] for d in program_data], rotation=45, ha="right")
    ax.set_ylabel("Оценка")
    
    legend_labels = competence_types + ["Средняя оценка"]
    ax.legend(labels=legend_labels, handles=[
        plt.Rectangle((0, 0), 1, 1, color=colors[j % len(colors)]) for j in range(len(legend_labels))
    ], loc="upper right", title="Компетенции")
    
    fig.suptitle(f"Вакансия: {vacancy_name}, Дата оценки: {assessment_date}", fontsize=14)
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    logging.info(f"Графики построены для {len(program_data)} ОП")