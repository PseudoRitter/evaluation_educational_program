import tkinter as tk
from tkinter import ttk
import logging
from .add_program_window import create_add_program_window  # Импорт только create_add_program_window

def create_education_tab(frame, app):
    education_program_frame = tk.Frame(frame)
    education_program_frame.pack(pady=4, fill="x", expand=False)

    education_table_frame = ttk.LabelFrame(education_program_frame, text="Выбор программы")
    education_table_frame.pack(pady=4, padx=4, fill="both", expand=False)

    app.education_table = ttk.Treeview(education_table_frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=8)
    app.education_table.heading("name", text="Наименование ОП")
    app.education_table.heading("code", text="Код ОП")
    app.education_table.heading("year", text="Год ОП")
    app.education_table.heading("university_short", text="ВУЗ")
    app.education_table.heading("type", text="Вид программы")
    app.education_table.column("name", width=310)
    app.education_table.column("code", width=100)
    app.education_table.column("year", width=80)
    app.education_table.column("university_short", width=40)
    app.education_table.column("type", width=150)
    app.education_table.pack(pady=4, fill="x", expand=False)
    app.education_table.bind("<<TreeviewSelect>>", lambda event: preview_competences(app))

    app.select_button = tk.Button(frame, text="Выбрать", command=lambda: on_table_select(app))
    app.select_button.pack(pady=4)

    app.selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")
    app.selected_program_label.pack(pady=4)

    app.competence_frame = ttk.LabelFrame(frame, text="Компетенции программы")
    app.competence_frame.pack(pady=4, padx=4, fill="both", expand=False)

    app.competence_table = ttk.Treeview(app.competence_frame, columns=("competence", "competence_type"), show="headings", height=12)
    app.competence_table.heading("competence", text="Компетенция")
    app.competence_table.heading("competence_type", text="Вид компетенции")
    app.competence_table.column("competence", width=550, stretch=True)  # stretch=True для гибкости ширины
    app.competence_table.column("competence_type", width=150)
    app.competence_table.pack(pady=4, fill="both", expand=False)

    app.add_program_button = tk.Button(frame, text="Добавить программу", command=lambda: create_add_program_window(app.root, app))
    app.add_program_button.pack(pady=10)

    style = ttk.Style()
    style.configure("Treeview", rowheight=25, wraplength=540)  # wraplength для переноса текста (хотя работает только с text)
    style.configure("Treeview.Heading")
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

    load_education_table(app)

def load_education_table(app):
    """Загрузка данных в таблицу education_table с кэшированием."""
    try:
        if not hasattr(app, 'education_programs'):
            app.education_programs = app.logic.db.fetch_educational_programs_with_details()
        app.education_table.delete(*app.education_table.get_children())
        for program in app.education_programs:
            year = program[2] if program[2] else ""
            app.education_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))
    except Exception as e:
        logging.error(f"Ошибка загрузки программ в education_table: {e}")
        app.show_error(f"Не удалось загрузить программы: {e}")

def sync_program_tables(app):
    """Синхронизация таблиц education_table и program_table."""
    try:
        # Обновляем кэш программ
        app.education_programs = app.logic.db.fetch_educational_programs_with_details()
        app.programs = app.education_programs  # Единый кэш для обеих таблиц

        # Обновляем education_table
        app.education_table.delete(*app.education_table.get_children())
        for program in app.education_programs:
            year = program[2] if program[2] else ""
            app.education_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))

        # Обновляем program_table, если она существует
        if hasattr(app, 'program_table') and app.program_table.winfo_exists():
            app.program_table.delete(*app.program_table.get_children())
            for program in app.programs:
                year = program[2] if program[2] else ""
                app.program_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))

        # Обновляем competence_table_add, если выбрана программа и таблица существует
        if hasattr(app, 'selected_program_id') and hasattr(app, 'competence_table_add') and app.competence_table_add.winfo_exists():
            app.competence_table_add.delete(*app.competence_table_add.get_children())
            competences = app.logic.db.fetch_competences_for_program(app.selected_program_id)
            for competence in competences:
                app.competence_table_add.insert("", tk.END, values=(competence[0], competence[1]))

        # Принудительное обновление интерфейса
        app.root.update_idletasks()
    except Exception as e:
        logging.error(f"Ошибка синхронизации таблиц: {e}")

def preview_competences(app):
    selected_item = app.education_table.selection()
    if not selected_item:
        app.competence_table.delete(*app.competence_table.get_children())
        return

    values = app.education_table.item(selected_item[0])['values']
    program_id = get_program_id(app, values)
    if not program_id:
        logging.error(f"Не удалось найти ID для программы: {values[0]}, код: {values[1]}")
        return

    try:
        competences = app.logic.db.fetch_program_details(program_id)
        app.competence_table.delete(*app.competence_table.get_children())
        
        max_chars_per_line = 120 
        
        for competence in competences:
            competence_name, competence_type = competence[5], competence[6]
            if competence_name:
                # Разбиваем длинный текст на несколько строк
                if len(competence_name) > max_chars_per_line:
                    wrapped_lines = []
                    current_line = ""
                    for word in competence_name.split():
                        if len(current_line) + len(word) + 1 <= max_chars_per_line:
                            current_line += (word + " ")
                        else:
                            wrapped_lines.append(current_line.strip())
                            current_line = word + " "
                    if current_line:
                        wrapped_lines.append(current_line.strip())
                    
                    # Вставляем первую строку с типом компетенции
                    app.competence_table.insert("", tk.END, values=(wrapped_lines[0], competence_type or "Неизвестно"))
                    # Вставляем остальные строки без типа
                    for line in wrapped_lines[1:]:
                        app.competence_table.insert("", tk.END, values=(line, ""))
                else:
                    # Если текст короткий, вставляем как есть
                    app.competence_table.insert("", tk.END, values=(competence_name, competence_type or "Неизвестно"))
    except Exception as e:
        logging.error(f"Ошибка загрузки компетенций: {e}")

def on_table_select(app):
    selected_item = app.education_table.selection()
    if not selected_item:
        app.show_error("Выберите программу!")
        return

    values = app.education_table.item(selected_item[0])['values']
    program_id = get_program_id(app, values)
    if program_id:
        app.selected_program_label.config(text=f"Выбрана программа: {values[0]}")
        app.program_id = program_id
        logging.info(f"Выбрана программа: {values[0]}, ID: {program_id}")
        preview_competences(app)

def get_program_id(app, values):
    try:
        name, code = values[0], values[1]
        result = app.logic.db.fetch_program_id_by_name_and_code(name, code)
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Ошибка получения ID программы: {e}")
        return None