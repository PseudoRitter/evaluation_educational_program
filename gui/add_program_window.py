import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import re
from moduls.table_sort import sort_treeview_column  

def create_add_program_window(root, app):
    """Создание окна для добавления образовательной программы."""
    add_window = tk.Toplevel(root)
    add_window.title("Добавление образовательной программы")
    add_window.geometry("1100x800")

    main_frame = tk.Frame(add_window)
    main_frame.pack(pady=2, padx=4, fill="both", expand=True)

    create_university_section(main_frame, app, add_window)
    create_program_section(main_frame, app, add_window)
    create_competence_section(main_frame, app, add_window)

    load_tables(app)
    configure_treeview_style()

def configure_treeview_style():
    """Настройка стиля для Treeview."""
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

def load_tables(app):
    if not hasattr(app, "universities"):
        app.universities = app.logic.db.fetch_universities()
    load_table(app.university_table, app.universities)

    if not hasattr(app, "programs"):
        app.programs = app.logic.db.fetch_educational_programs_with_details()
    programs_data = [(p[0], p[1], p[2] or "", p[3], p[4]) for p in app.programs]
    load_table(app.program_table, programs_data)

    if hasattr(app, "last_selected_program_data") and app.last_selected_program_data:
        name, code, university_short = app.last_selected_program_data
        for item in app.program_table.get_children():
            values = app.program_table.item(item)["values"]
            if values[0] == name and values[1] == code and values[3] == university_short:
                app.program_table.selection_set(item)
                app.program_table.focus(item)
                on_program_table_select(app)  # Обновляем компетенции для выбранной программы
                break
    else:
        # Если выбора не было, очищаем таблицу компетенций
        app.competence_table_add.delete(*app.competence_table_add.get_children())

    competences = (
        app.logic.db.fetch_competences_for_program(app.selected_program_id)
        if hasattr(app, "selected_program_id")
        else []
    )
    load_table(app.competence_table_add, competences)
    
def load_table(table, data):
    """Универсальная загрузка данных в Treeview."""
    try:
        table.delete(*table.get_children())
        for row in data:
            table.insert("", tk.END, values=row)
    except Exception as e:
        logging.error(f"Ошибка загрузки таблицы: {e}")

def create_university_section(parent_frame, app, window):
    """Создание секции для работы с университетами."""
    frame = tk.Frame(parent_frame)
    frame.pack(pady=2, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=2, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Работа с ВУЗами")
    table_frame.pack(side=tk.LEFT, pady=2, padx=4, fill="both", expand=True)

    app.university_table = ttk.Treeview(table_frame, columns=("full_name", "short_name", "city"), show="headings", height=6)
    app.university_table.heading("full_name", text="Наименование ВУЗа", command=lambda: sort_treeview_column(app.university_table, "full_name", False))
    app.university_table.heading("short_name", text="Сокращение", command=lambda: sort_treeview_column(app.university_table, "short_name", False))
    app.university_table.heading("city", text="Город", command=lambda: sort_treeview_column(app.university_table, "city", False))
    app.university_table.column("full_name", width=400)
    app.university_table.column("short_name", width=70)
    app.university_table.column("city", width=70)
    app.university_table.pack(pady=2, fill="both", expand=True)

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=2, pady=4, fill="y")
    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "university", "add")).pack(pady=4)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "university", "edit")).pack(pady=4)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "university")).pack(pady=4)

def create_program_section(parent_frame, app, window):
    """Создание секции для добавления образовательных программ."""
    frame = tk.Frame(parent_frame)
    frame.pack(pady=2, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=2, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Добавить образовательную программу")
    table_frame.pack(side=tk.LEFT, pady=2, padx=4, fill="both", expand=True)

    app.program_table = ttk.Treeview(table_frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=7)
    app.program_table.heading("name", text="Наименование ОП", command=lambda: sort_treeview_column(app.program_table, "name", False))
    app.program_table.heading("code", text="Код ОП", command=lambda: sort_treeview_column(app.program_table, "code", False))
    app.program_table.heading("year", text="Год ОП", command=lambda: sort_treeview_column(app.program_table, "year", False))
    app.program_table.heading("university_short", text="ВУЗ", command=lambda: sort_treeview_column(app.program_table, "university_short", False))
    app.program_table.heading("type", text="Вид ОП", command=lambda: sort_treeview_column(app.program_table, "name", False))
    app.program_table.column("name", width=280)
    app.program_table.column("code", width=50)
    app.program_table.column("year", width=50)
    app.program_table.column("university_short", width=50)
    app.program_table.column("type", width=100)
    app.program_table.pack(pady=2, fill="both", expand=True)
    app.program_table.bind("<<TreeviewSelect>>", lambda event: on_program_table_select(app))

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=2, pady=2, fill="y")
    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "program", "add")).pack(pady=4)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "program", "edit")).pack(pady=4)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "program")).pack(pady=4)

    app.add_window_selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")
    app.add_window_selected_program_label.pack(pady=4)

def create_competence_section(parent_frame, app, window):
    """Создание секции для добавления компетенций."""
    frame = tk.Frame(parent_frame)
    frame.pack(pady=2, fill="x", expand=True)

    container = tk.Frame(frame)
    container.pack(pady=2, fill="x", expand=True)

    table_frame = ttk.LabelFrame(container, text="Добавить компетенции")
    table_frame.pack(side=tk.LEFT, pady=2, padx=4, fill="both", expand=True)

    app.competence_table_add = ttk.Treeview(table_frame, columns=("competence", "type"), show="headings", height=14)
    app.competence_table_add.heading("competence", text="Компетенция", command=lambda: sort_treeview_column(app.competence_table_add, "competence", False))
    app.competence_table_add.heading("type", text="Вид компетенции", command=lambda: sort_treeview_column(app.competence_table_add, "type", False))
    app.competence_table_add.column("competence", width=430)
    app.competence_table_add.column("type", width=70)
    app.competence_table_add.pack(pady=2, fill="both", expand=True)

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=4, pady=2, fill="y")
    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "competence", "add")).pack(pady=4)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "competence", "edit")).pack(pady=4)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "competence")).pack(pady=4)

def on_program_table_select(app):
    selected_item = app.program_table.selection()
    if not selected_item:
        app.competence_table_add.delete(*app.competence_table_add.get_children())
        app.add_window_selected_program_label.config(text="Выбрана программа: Нет")
        app.last_selected_program_data = None  
        return

    values = app.program_table.item(selected_item[0])["values"]
    name, code, year, university_short = values[0], values[1], values[2], values[3]
    university = app.logic.db.fetch_university_by_short_name(university_short)
    if not university:
        logging.error(f"Университет с коротким именем {university_short} не найден")
        app.competence_table_add.delete(*app.competence_table_add.get_children())
        app.add_window_selected_program_label.config(text="Выбрана программа: Нет")
        app.last_selected_program_data = None
        return

    university_id = university[0]
    program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code, year, university_id)

    if program_id:
        app.temp_selected_program = (name, code)
        app.add_window_selected_program_label.config(text=f"Выбрана программа: {name}")
        app.selected_program_id = program_id[0]
        app.last_selected_program_data = (name, code)  # Сохраняем данные выбранной программы

        try:
            competences = app.logic.db.fetch_competences_for_program(app.selected_program_id)
            app.competence_table_add.delete(*app.competence_table_add.get_children())
            for competence in competences:
                app.competence_table_add.insert("", tk.END, values=(competence[0], competence[1]))
            logging.info(f"Компетенции для программы '{name}' (ID: {program_id[0]}) загружены")
        except Exception as e:
            logging.error(f"Ошибка загрузки компетенций: {e}")
            app.competence_table_add.delete(*app.competence_table_add.get_children())
    else:
        logging.error(f"Не удалось найти ID для программы: {name}, код: {code}, год: {year}, университет: {university_short}")
        app.competence_table_add.delete(*app.competence_table_add.get_children())
        app.add_window_selected_program_label.config(text="Выбрана программа: Нет")
        app.last_selected_program_data = None

def edit_entity_window(app, parent_window, entity_type, action):
    entity_configs = {
        "university": {
            "title": "ВУЗ" if action == "add" else " ",
            "fields": [("Наименование ВУЗа:", lambda w: tk.Entry(w, width=60)), ("Сокращение:", tk.Entry), ("Город:", tk.Entry)],
            "size": "400x300",
            "fetch": lambda: app.university_table.item(app.university_table.selection()[0])["values"] if app.university_table.selection() else None
        },
        "program": {
            "title": "Программа" if action == "add" else " ",
            "fields": [
                ("Наименование ОП:", lambda w: tk.Entry(w, width=60)),
                ("Код ОП:", tk.Entry),
                ("Год ОП:", tk.Entry),
                ("Краткое наименование ВУЗа:", lambda w: ttk.Combobox(w, values=[u[1] for u in app.universities], state="readonly")),
                ("Вид программы:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_educational_program_types()], state="readonly"))
            ],
            "size": "500x400",
            "fetch": lambda: app.program_table.item(app.program_table.selection()[0])["values"] if app.program_table.selection() else None
        },
        "competence": {
            "title": "Компетенция" if action == "add" else " ",
            "fields": [
                ("Компетенция:", lambda w: scrolledtext.ScrolledText(w, width=80, height=8)),
                ("Вид компетенции:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_competence_types()], state="readonly"))
            ],
            "size": "400x400",
            "fetch": lambda: app.competence_table_add.item(app.competence_table_add.selection()[0])["values"] if app.competence_table_add.selection() else None,
            "requires_program": True
        }
    }

    config = entity_configs[entity_type]
    if action == "edit" and not config["fetch"]():
        logging.error(f"Выберите {entity_type} для редактирования!")
        return
    if entity_type == "competence" and config["requires_program"] and not hasattr(app, "selected_program_id"):
        logging.error("Сначала выберите программу!")
        return

    selected_program = app.program_table.selection()
    if selected_program:
        values = app.program_table.item(selected_program[0])["values"]
        app.last_selected_program_data = (values[0], values[1])
    else:
        app.last_selected_program_data = None

    window = tk.Toplevel(parent_window)
    window.title(f"{action.capitalize()} {config['title']}")
    window.geometry(config["size"])

    entries = []
    for label, widget_type in config["fields"]:
        tk.Label(window, text=label).pack(pady=4)
        widget = widget_type(window) if callable(widget_type) else widget_type(window)
        widget.pack(pady=4)
        entries.append(widget)

        if label == "Компетенция:" and isinstance(widget, scrolledtext.ScrolledText):
            tk.Button(window, text="Удаление символов", command=lambda w=widget: remove_newlines(w)).pack(pady=4)

        if action == "edit" and isinstance(widget, ttk.Combobox):
            widget.set(config["fetch"]()[config["fields"].index((label, widget_type))])

    if action == "edit":
        old_values = config["fetch"]()
        for entry, value in zip(entries, old_values):
            if isinstance(entry, tk.Entry):
                entry.insert(0, value)
            elif isinstance(entry, scrolledtext.ScrolledText):
                entry.insert("1.0", value)

    tk.Button(window, text="Сохранить", command=lambda: save_entity(app, window, parent_window, entity_type, action, entries, old_values if action == "edit" else None)).pack(pady=5)

def remove_newlines(text_widget):
    """Удаление символов новой строки из текста."""
    try:
        current_text = text_widget.get("1.0", tk.END).strip()
        cleaned_text = current_text.replace("\n", " ")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", cleaned_text)
    except Exception as e:
        logging.error(f"Ошибка удаления символов: {e}")

def save_entity(app, window, parent_window, entity_type, action, entries, old_values=None):
    """Сохранение данных сущности в базе данных."""
    values = [e.get().strip() if isinstance(e, (tk.Entry, ttk.Combobox)) else e.get("1.0", tk.END).strip() for e in entries]
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
        if entity_type == "program":
            from .education_tab import sync_program_tables  # Локальный импорт
            sync_program_tables(app)
        else:
            load_tables(app)
    except Exception as e:
        logging.error(f"Ошибка сохранения {entity_type}: {e}")

def save_university(app, values, old_values, action):
    """Сохранение данных университета."""
    full_name, short_name, city = values
    if action == "add":
        university_id = app.logic.db.save_university(full_name, short_name, city)
        if university_id:
            app.universities = app.logic.db.fetch_universities()
            logging.info(f"ВУЗ '{full_name}' добавлен!")
    else:
        university_id = app.logic.db.fetch_university_id_by_details(*old_values)[0]
        if app.logic.db.update_university(university_id, full_name, short_name, city):
            app.universities = app.logic.db.fetch_universities()
            logging.info(f"ВУЗ обновлён: {full_name}")

def save_program(app, values, old_values, action):
    """Сохранение данных образовательной программы."""
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
            app.programs = app.logic.db.fetch_educational_programs_with_details()
            logging.info(f"Программа '{name}' добавлена!")
    else:
        try:
            old_name, old_code, old_year, old_university_short = old_values[0], old_values[1], old_values[2], old_values[3]
            old_university = app.logic.db.fetch_university_by_short_name(old_university_short)
            if not old_university:
                logging.error(f"Старый университет с коротким именем {old_university_short} не найден")
                return
            old_university_id = old_university[0]
            program_id = app.logic.db.fetch_program_id_by_name_and_code(old_name, old_code, old_year, old_university_id)
            if program_id and app.logic.db.update_educational_program(program_id[0], name, code, university_id, year, type_program_id):
                app.programs = app.logic.db.fetch_educational_programs_with_details()
                logging.info(f"Программа '{name}' обновлена!")
            else:
                logging.error(f"Не удалось найти программу для обновления: {old_name}, код: {old_code}, год: {old_year}")
        except Exception as e:
            logging.error(f"Ошибка обновления программы: {e}")

def save_competence(app, values, old_values, action):
    """Сохранение данных компетенции."""
    competence_name, type_name = values
    type_id = next((t[0] for t in app.logic.db.fetch_competence_types() if t[1] == type_name), None)
    if not type_id:
        logging.error(f"Тип компетенции '{type_name}' не найден!")
        return

    if action == "add":
        competence = app.logic.db.fetch_competence_by_name(competence_name)
        competence_id = app.logic.db.save_competence(competence_name, type_id) if not competence else competence[0]
        if app.logic.db.save_competence_for_program(competence_id, type_id, app.selected_program_id):
            logging.info(f"Компетенция '{competence_name}' добавлена!")
    else:
        old_competence_name = old_values[0]
        old_competence = app.logic.db.fetch_competence_by_name(old_competence_name)
        if not old_competence:
            logging.error(f"Компетенция '{old_competence_name}' не найдена!")
            return
        competence_id = old_competence[0]
        if app.logic.db.update_competence(competence_id, competence_name, type_id):
            if app.logic.db.update_competence_for_program(competence_id, old_competence[2], app.selected_program_id, competence_id, type_id):
                logging.info(f"Компетенция '{competence_name}' обновлена!")
            else:
                logging.error("Ошибка обновления связи компетенции с программой!")

def delete_entity(app, parent_window, entity_type):
    """Удаление сущности из базы данных."""
    table_map = {"university": app.university_table, "program": app.program_table, "competence": app.competence_table_add}
    table = table_map[entity_type]
    selected_item = table.selection()
    if not selected_item:
        logging.error(f"Выберите {entity_type} для удаления!")
        return

    values = table.item(selected_item[0])["values"]
    try:
        if entity_type == "university":
            university_id = app.logic.db.fetch_university_id_by_details(*values)[0]
            if app.logic.db.delete_university(university_id):
                app.universities = app.logic.db.fetch_universities()
                logging.info(f"ВУЗ '{values[0]}' удалён!")
        elif entity_type == "program":
            name, code, year, university_short = values[0], values[1], values[2], values[3]
            university = app.logic.db.fetch_university_by_short_name(university_short)
            if not university:
                logging.error(f"Университет с коротким именем {university_short} не найден")
                return
            university_id = university[0]
            program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code, year, university_id)
            if program_id and app.logic.db.delete_educational_program(program_id[0]):
                app.programs = app.logic.db.fetch_educational_programs_with_details()
                logging.info(f"Программа '{name}' удалена!")
            else:
                logging.error(f"Не удалось найти программу для удаления: {name}, код: {code}, год: {year}")
        elif entity_type == "competence":
            if not hasattr(app, "selected_program_id"):
                logging.error("Сначала выберите программу!")
                return
            competence = app.logic.db.fetch_competence_by_name(values[0])
            if app.logic.db.delete_competence_for_program(competence[0], competence[2], app.selected_program_id):
                logging.info(f"Компетенция '{values[0]}' удалена!")

        if entity_type == "program":
            from .education_tab import sync_program_tables  # Локальный импорт
            sync_program_tables(app)
        else:
            load_tables(app)
    except Exception as e:
        logging.error(f"Ошибка удаления {entity_type}: {e}")

def validate(possible_new_value):
    """Проверка ввода на соответствие шестнадцатеричному формату."""
    return bool(re.match(r"^[0-9a-fA-F]*$", possible_new_value))