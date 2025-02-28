import tkinter as tk
from tkinter import ttk
import logging

def create_add_program_window(root, app):
    """Создание окна для добавления образовательной программы с функционалом работы с ВУЗами, ОП и компетенциями."""
    add_window = tk.Toplevel(root)
    add_window.title("Добавление образовательной программы")
    add_window.geometry("1200x800")

    main_frame = tk.Frame(add_window)
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Создание блоков для ВУЗов, программ и компетенций
    create_university_section(main_frame, app, add_window)
    create_program_section(main_frame, app, add_window)
    create_competence_section(main_frame, app, add_window)

    # Загрузка начальных данных
    load_university_table(app)
    load_program_table(app)
    load_competence_table(app, None)

    # Стили для таблиц
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

def create_university_section(parent_frame, app, window):
    """Создание секции для управления ВУЗами."""
    frame = tk.Frame(parent_frame)
    frame.pack(pady=5, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=5, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Работа с ВУЗами")
    table_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=True)

    app.university_table = ttk.Treeview(table_frame, columns=("full_name", "short_name", "city"), show="headings", height=6)
    app.university_table.heading("full_name", text="Наименование ВУЗа")
    app.university_table.heading("short_name", text="Сокращение")
    app.university_table.heading("city", text="Город")
    app.university_table.column("full_name", width=300)
    app.university_table.column("short_name", width=120)
    app.university_table.column("city", width=120)
    app.university_table.pack(pady=5, fill="both", expand=True)

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill="y")

    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "university", "add")).pack(pady=5)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "university", "edit")).pack(pady=5)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "university")).pack(pady=5)

def create_program_section(parent_frame, app, window):
    frame = tk.Frame(parent_frame)
    frame.pack(pady=5, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=5, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Добавить образовательную программу")
    table_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=True)

    app.program_table = ttk.Treeview(table_frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=6)
    app.program_table.heading("name", text="Наименование ОП")
    app.program_table.heading("code", text="Код ОП")
    app.program_table.heading("year", text="Год ОП")
    app.program_table.heading("university_short", text="Краткое наименование ВУЗа")
    app.program_table.heading("type", text="Вид образовательной программы")
    app.program_table.column("name", width=150)
    app.program_table.column("code", width=80)
    app.program_table.column("year", width=60)
    app.program_table.column("university_short", width=120)
    app.program_table.column("type", width=120)
    app.program_table.pack(pady=5, fill="both", expand=True)
    app.program_table.bind("<<TreeviewSelect>>", lambda event: on_program_table_select(app))

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill="y")

    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "program", "add")).pack(pady=5)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "program", "edit")).pack(pady=5)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "program")).pack(pady=5)

    tk.Button(frame, text="Выбрать программу", command=lambda: confirm_program_selection(app)).pack(pady=5)
    app.add_window_selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")  # Переименована
    app.add_window_selected_program_label.pack(pady=5)

def create_competence_section(parent_frame, app, window):
    """Создание секции для управления компетенциями."""
    frame = tk.Frame(parent_frame)
    frame.pack(pady=5, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=5, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Добавить компетенции")
    table_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=True)

    app.competence_table_add = ttk.Treeview(table_frame, columns=("competence", "type"), show="headings", height=6)
    app.competence_table_add.heading("competence", text="Компетенция")
    app.competence_table_add.heading("type", text="Вид компетенции")
    app.competence_table_add.column("competence", width=300)
    app.competence_table_add.column("type", width=200)
    app.competence_table_add.pack(pady=5, fill="both", expand=True)

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill="y")

    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "competence", "add")).pack(pady=5)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "competence", "edit")).pack(pady=5)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "competence")).pack(pady=5)

def on_program_table_select(app):
    """Обработка выбора строки в таблице образовательных программ."""
    selected_item = app.program_table.selection()
    if selected_item:
        values = app.program_table.item(selected_item[0])['values']
        app.temp_selected_program = (values[0], values[1])  # name, code

def load_university_table(app):
    """Загрузка данных ВУЗов в таблицу."""
    try:
        app.university_table.delete(*app.university_table.get_children())
        for university in app.logic.db.fetch_universities():
            app.university_table.insert("", tk.END, values=university)
    except Exception as e:
        logging.error(f"Ошибка при загрузке ВУЗов: {e}")

def load_program_table(app):
    """Загрузка данных образовательных программ в таблицу."""
    try:
        app.program_table.delete(*app.program_table.get_children())
        for program in app.logic.db.fetch_educational_programs_with_details():
            year = program[2] if program[2] else ""
            app.program_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))
    except Exception as e:
        logging.error(f"Ошибка при загрузке программ: {e}")

def load_competence_table(app, program_id):
    """Загрузка данных компетенций в таблицу."""
    try:
        app.competence_table_add.delete(*app.competence_table_add.get_children())
        if program_id:
            for competence in app.logic.db.fetch_competences_for_program(program_id):
                app.competence_table_add.insert("", tk.END, values=competence)
    except Exception as e:
        logging.error(f"Ошибка при загрузке компетенций: {e}")

def edit_entity_window(app, parent_window, entity_type, action):
    """Универсальное окно для добавления или редактирования сущности."""
    entity_configs = {
        "university": {
            "title": "ВУЗ" if action == "add" else "Редактирование ВУЗа",
            "fields": [("Наименование ВУЗа:", tk.Entry), ("Сокращение:", tk.Entry), ("Город:", tk.Entry)],
            "size": "400x300",
            "fetch": lambda: app.university_table.item(app.university_table.selection()[0])['values'] if app.university_table.selection() else None
        },
        "program": {
            "title": "Программа" if action == "add" else "Редактирование программы",
            "fields": [
                ("Наименование ОП:", tk.Entry),
                ("Код ОП:", tk.Entry),
                ("Год ОП:", tk.Entry),
                ("Краткое наименование ВУЗа:", lambda w: ttk.Combobox(w, values=[u[1] for u in app.logic.db.fetch_universities()], state="readonly")),
                ("Вид программы:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_educational_program_types()], state="readonly"))
            ],
            "size": "500x400",
            "fetch": lambda: app.program_table.item(app.program_table.selection()[0])['values'] if app.program_table.selection() else None
        },
        "competence": {
            "title": "Компетенция" if action == "add" else "Редактирование компетенции",
            "fields": [
                ("Компетенция:", tk.Entry),
                ("Вид компетенции:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_competence_types()], state="readonly"))
            ],
            "size": "400x300",
            "fetch": lambda: app.competence_table_add.item(app.competence_table_add.selection()[0])['values'] if app.competence_table_add.selection() else None,
            "requires_program": True
        }
    }

    config = entity_configs[entity_type]
    if action == "edit" and not config["fetch"]():
        logging.error(f"Выберите {entity_type} для редактирования!")
        return
    if entity_type == "competence" and config["requires_program"] and not hasattr(app, 'selected_program_id'):
        logging.error("Сначала выберите образовательную программу!")
        return

    window = tk.Toplevel(parent_window)
    window.title(f"{action.capitalize()} {config['title']}")
    window.geometry(config["size"])

    entries = []
    for label, widget_type in config["fields"]:
        tk.Label(window, text=label).pack(pady=5)
        widget = widget_type(window) if callable(widget_type) else widget_type(window)
        widget.pack(pady=5)
        entries.append(widget)
        if action == "edit" and isinstance(widget, ttk.Combobox):
            widget.set(config["fetch"]()[config["fields"].index((label, widget_type))])

    if action == "edit":
        old_values = config["fetch"]()
        for entry, value in zip(entries, old_values):
            if isinstance(entry, tk.Entry):
                entry.insert(0, value)

    tk.Button(window, text="Сохранить", command=lambda: save_entity(app, window, parent_window, entity_type, action, entries, old_values if action == "edit" else None)).pack(pady=10)

def save_entity(app, window, parent_window, entity_type, action, entries, old_values=None):
    """Сохранение сущности в БД."""
    values = [e.get().strip() if isinstance(e, tk.Entry) else e.get() for e in entries]
    if not all(values):
        logging.error("Все поля должны быть заполнены!")
        return

    try:
        if entity_type == "university":
            save_university(app, values, old_values, action)
        elif entity_type == "program":
            save_program(app, values, old_values, action)
        elif entity_type == "competence":
            save_competence(app, values, old_values, action)
        window.destroy()
    except Exception as e:
        logging.error(f"Ошибка при保存 {entity_type}: {e}")

def save_university(app, values, old_values, action):
    """Сохранение ВУЗа."""
    full_name, short_name, city = values
    if action == "add":
        university_id = app.logic.db.save_university(full_name, short_name, city)
        if university_id:
            load_university_table(app)
            logging.info(f"ВУЗ '{full_name}' добавлен!")
    else:
        university_id = app.logic.db.fetch_university_id_by_details(*old_values)[0]
        if app.logic.db.update_university(university_id, full_name, short_name, city):
            load_university_table(app)
            logging.info(f"ВУЗ обновлён: {full_name}")

def save_program(app, values, old_values, action):
    """Сохранение образовательной программы."""
    name, code, year, university_short, type_name = values
    university = app.logic.db.fetch_university_by_short_name(university_short)
    type_program = app.logic.db.fetch_educational_program_type_by_name(type_name)
    if not university or not type_program:
        logging.error("ВУЗ или тип программы не найден!")
        return

    university_id, type_program_id = university[0], type_program[0]
    if action == "add":
        program_id = app.logic.db.save_educational_program(name, code, university_id, year, type_program_id, [])
        if program_id:
            load_program_table(app)
            from .education_tab import load_education_table
            load_education_table(app)
            logging.info(f"Программа '{name}' добавлена!")
    else:
        program_id = app.logic.db.fetch_program_id_by_name_and_code(old_values[0], old_values[1])
        if program_id is None:
            logging.error(f"Не удалось найти программу для обновления: {old_values[0]}, код: {old_values[1]}")
            return
        program_id = program_id[0]
        if app.logic.db.update_educational_program(program_id, name, code, university_id, year, type_program_id):
            load_program_table(app)
            from .education_tab import load_education_table
            load_education_table(app)
            logging.info(f"Программа '{name}' обновлена!")

def save_competence(app, values, old_values, action):
    """Сохранение компетенции."""
    competence_name, type_name = values
    type_id = next((t[0] for t in app.logic.db.fetch_competence_types() if t[1] == type_name), None)
    if not type_id:
        logging.error(f"Тип компетенции '{type_name}' не найден!")
        return

    competence = app.logic.db.fetch_competence_by_name(competence_name)
    competence_id = app.logic.db.save_competence(competence_name, type_id) if not competence else competence[0]

    if action == "add":
        if app.logic.db.save_competence_for_program(competence_id, type_id, app.selected_program_id):
            load_competence_table(app, app.selected_program_id)
            logging.info(f"Компетенция '{competence_name}' добавлена!")
    else:
        old_competence = app.logic.db.fetch_competence_by_name(old_values[0])
        if app.logic.db.update_competence_for_program(old_competence[0], old_competence[2], app.selected_program_id, competence_id, type_id):
            load_competence_table(app, app.selected_program_id)
            logging.info(f"Компетенция '{competence_name}' обновлена!")

def delete_entity(app, parent_window, entity_type):
    """Удаление сущности из БД."""
    table_map = {"university": app.university_table, "program": app.program_table, "competence": app.competence_table_add}
    table = table_map[entity_type]
    selected_item = table.selection()
    if not selected_item:
        logging.error(f"Выберите {entity_type} для удаления!")
        return

    values = table.item(selected_item[0])['values']
    try:
        if entity_type == "university":
            university_id = app.logic.db.fetch_university_id_by_details(*values)[0]
            if app.logic.db.delete_university(university_id):
                load_university_table(app)
                logging.info(f"ВУЗ '{values[0]}' удалён!")
        elif entity_type == "program":
            program_id = app.logic.db.fetch_program_id_by_name_and_code(values[0], values[1])[0]
            if app.logic.db.delete_educational_program(program_id):
                load_program_table(app)
                from .education_tab import load_education_table
                load_education_table(app)
                logging.info(f"Программа '{values[0]}' удалена!")
        elif entity_type == "competence":
            if not hasattr(app, 'selected_program_id'):
                logging.error("Сначала выберите программу!")
                return
            competence = app.logic.db.fetch_competence_by_name(values[0])
            if app.logic.db.delete_competence_for_program(competence[0], competence[2], app.selected_program_id):
                load_competence_table(app, app.selected_program_id)
                logging.info(f"Компетенция '{values[0]}' удалена!")
    except Exception as e:
        logging.error(f"Ошибка при удалении {entity_type}: {e}")

def confirm_program_selection(app):
    if not hasattr(app, 'temp_selected_program'):
        logging.error("Выберите программу в таблице!")
        return

    name, code = app.temp_selected_program
    program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code)
    if program_id:
        app.add_window_selected_program_label.config(text=f"Выбрана программа: {name}")  # Используем новое имя
        app.selected_program_id = program_id[0]
        load_competence_table(app, program_id[0])
        logging.info(f"Выбрана программа: {name}, ID: {program_id[0]}")
        delattr(app, 'temp_selected_program')
    else:
        logging.error(f"Не удалось найти ID для программы: {name}, код: {code}")