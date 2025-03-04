import tkinter as tk
import moduls.database as db
from tkinter import ttk, scrolledtext
import logging
import re

def create_add_program_window(root, app):
    add_window = tk.Toplevel(root)
    add_window.title("Добавление образовательной программы")
    add_window.geometry("1100x800")

    main_frame = tk.Frame(add_window)
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)

    create_university_section(main_frame, app, add_window)
    create_program_section(main_frame, app, add_window)
    create_competence_section(main_frame, app, add_window)

    load_tables(app)
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

def load_tables(app):
    if not hasattr(app, 'universities'):
        app.universities = app.logic.db.fetch_universities()
    load_table(app.university_table, app.universities)

    if not hasattr(app, 'programs'):
        app.programs = app.logic.db.fetch_educational_programs_with_details()
    load_table(app.program_table, [(p[0], p[1], p[2] or "", p[3], p[4]) for p in app.programs])

    load_table(app.competence_table_add, 
               app.logic.db.fetch_competences_for_program(app.selected_program_id) 
               if hasattr(app, 'selected_program_id') else [])

def load_table(table, data):
    try:
        table.delete(*table.get_children())
        for row in data:
            table.insert("", tk.END, values=row)
    except Exception as e:
        logging.error(f"Ошибка загрузки таблицы: {e}")

def create_university_section(parent_frame, app, window):
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
    app.program_table.heading("university_short", text=" ВУЗ")
    app.program_table.heading("type", text="Вид образовательной программы")
    app.program_table.column("name", width=210)
    app.program_table.column("code", width=80)
    app.program_table.column("year", width=60)
    app.program_table.column("university_short", width=60)
    app.program_table.column("type", width=120)
    app.program_table.pack(pady=5, fill="both", expand=True)
    app.program_table.bind("<<TreeviewSelect>>", lambda event: on_program_table_select(app))  # Обновляем привязку

    button_frame = tk.Frame(container)
    button_frame.pack(side=tk.LEFT, padx=5, pady=5, fill="y")

    tk.Button(button_frame, text="Добавить", command=lambda: edit_entity_window(app, window, "program", "add")).pack(pady=5)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_entity_window(app, window, "program", "edit")).pack(pady=5)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_entity(app, window, "program")).pack(pady=5)

    tk.Button(frame, text="Выбрать программу", command=lambda: confirm_program_selection(app)).pack(pady=5)
    app.add_window_selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")
    app.add_window_selected_program_label.pack(pady=5)

def create_competence_section(parent_frame, app, window):
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
    selected_item = app.program_table.selection()
    if not selected_item:
        app.competence_table_add.delete(*app.competence_table_add.get_children())  # Очищаем таблицу, если ничего не выбрано
        return

    values = app.program_table.item(selected_item[0])['values']
    name, code = values[0], values[1]
    program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code)
    
    if program_id:
        app.temp_selected_program = (name, code)  # Сохраняем временный выбор
        app.add_window_selected_program_label.config(text=f"Выбрана программа: {name}")  # Обновляем метку
        app.selected_program_id = program_id[0]   # Сохраняем ID программы
        
        # Обновляем таблицу компетенций
        try:
            competences = app.logic.db.fetch_competences_for_program(app.selected_program_id)
            app.competence_table_add.delete(*app.competence_table_add.get_children())
            for competence in competences:
                app.competence_table_add.insert("", tk.END, values=(competence[0], competence[1]))
            logging.info(f"Компетенции для программы '{name}' (ID: {program_id[0]}) загружены в competence_table_add")
        except Exception as e:
            logging.error(f"Ошибка загрузки компетенций: {e}")
    else:
        logging.error(f"Не удалось найти ID для программы: {name}, код: {code}")
        app.competence_table_add.delete(*app.competence_table_add.get_children())

def edit_entity_window(app, parent_window, entity_type, action):
    entity_configs = {
        "university": {
            "title": "ВУЗ" if action == "add" else "Редактирование ВУЗа",
            "fields": [("Наименование ВУЗа:", lambda w: tk.Entry(w, width=60)), ("Сокращение:", tk.Entry), ("Город:", tk.Entry)],
            "size": "400x300",
            "fetch": lambda: app.university_table.item(app.university_table.selection()[0])['values'] if app.university_table.selection() else None
        },
        "program": {
            "title": "Программа" if action == "add" else "Редактирование программы",
            "fields": [
                ("Наименование ОП:", lambda w: tk.Entry(w, width=60)),
                ("Код ОП:", tk.Entry),
                ("Год ОП:", tk.Entry),
                ("Краткое наименование ВУЗа:", lambda w: ttk.Combobox(w, values=[u[1] for u in app.universities], state="readonly")),
                ("Вид программы:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_educational_program_types()], state="readonly"))
            ],
            "size": "500x400",
            "fetch": lambda: app.program_table.item(app.program_table.selection()[0])['values'] if app.program_table.selection() else None
        },
        "competence": {
            "title": "Компетенция" if action == "add" else "Редактирование компетенции",
            "fields": [
                ("Компетенция:", lambda w: scrolledtext.ScrolledText(w, width=80, height=8)),
                ("Вид компетенции:", lambda w: ttk.Combobox(w, values=[t[1] for t in app.logic.db.fetch_competence_types()], state="readonly"))
            ],
            "size": "400x400",
            "fetch": lambda: app.competence_table_add.item(app.competence_table_add.selection()[0])['values'] if app.competence_table_add.selection() else None,
            "requires_program": True
        }
    }

    config = entity_configs[entity_type]
    if action == "edit" and not config["fetch"]():
        logging.error(f"Выберите {entity_type} для редактирования!")
        return
    if entity_type == "competence" and config["requires_program"] and not hasattr(app, 'selected_program_id'):
        logging.error("Сначала выберите программу!")
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
        
        # Добавляем кнопку "Удаление символов" только для ScrolledText в "Компетенция"
        if label == "Компетенция:" and isinstance(widget, scrolledtext.ScrolledText):
            def remove_newlines(text_widget=widget):  # Передаём widget как параметр по умолчанию
                if not isinstance(text_widget, scrolledtext.ScrolledText):
                    logging.error(f"Ожидался ScrolledText, получен {type(text_widget)}")
                    return
                current_text = text_widget.get("1.0", tk.END).strip()
                cleaned_text = current_text.replace("\n", " ")
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", cleaned_text)
            
            remove_button = tk.Button(window, text="Удаление символов", command=remove_newlines)
            remove_button.pack(pady=5)
        elif label == "Компетенция:" and not isinstance(widget, scrolledtext.ScrolledText):
            logging.warning(f"Поле 'Компетенция' не является ScrolledText, а {type(widget)}")

        if action == "edit" and isinstance(widget, ttk.Combobox):
            widget.set(config["fetch"]()[config["fields"].index((label, widget_type))])

    if action == "edit":
        old_values = config["fetch"]()
        for entry, value in zip(entries, old_values):
            if isinstance(entry, tk.Entry):
                entry.insert(0, value)
            elif isinstance(entry, scrolledtext.ScrolledText):
                entry.insert("1.0", value)

    tk.Button(window, text="Сохранить", command=lambda: save_entity(app, window, parent_window, entity_type, action, entries, old_values if action == "edit" else None)).pack(pady=10)

def save_entity(app, window, parent_window, entity_type, action, entries, old_values=None):
    values = []
    for e in entries:
        if isinstance(e, tk.Entry) or isinstance(e, ttk.Combobox):
            values.append(e.get().strip())
        elif isinstance(e, scrolledtext.ScrolledText):
            values.append(e.get("1.0", tk.END).strip())
            
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
        logging.error(f"Ошибка при сохранении {entity_type}: {e}")

def save_university(app, values, old_values, action):
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
        program_id = app.logic.db.fetch_program_id_by_name_and_code(old_values[0], old_values[1])[0]
        if app.logic.db.update_educational_program(program_id, name, code, university_id, year, type_program_id):
            app.programs = app.logic.db.fetch_educational_programs_with_details()
            logging.info(f"Программа '{name}' обновлена!")

def save_competence(app, values, old_values, action):
    competence_name, type_name = values
    type_id = next((t[0] for t in app.logic.db.fetch_competence_types() if t[1] == type_name), None)
    if not type_id:
        logging.error(f"Тип компетенции '{type_name}' не найден!")
        return

    if action == "add":
        # Добавление новой компетенции
        competence = app.logic.db.fetch_competence_by_name(competence_name)
        competence_id = app.logic.db.save_competence(competence_name, type_id) if not competence else competence[0]
        if app.logic.db.save_competence_for_program(competence_id, type_id, app.selected_program_id):
            logging.info(f"Компетенция '{competence_name}' добавлена!")
    else:  # action == "edit"
        # Обновление существующей компетенции
        old_competence_name = old_values[0]  # Исходное имя компетенции из таблицы
        old_competence = app.logic.db.fetch_competence_by_name(old_competence_name)
        if not old_competence:
            logging.error(f"Существующая компетенция '{old_competence_name}' не найдена!")
            return
        
        competence_id = old_competence[0]  # Используем ID существующей компетенции
        # Обновляем компетенцию в базе данных
        if app.logic.db.update_competence(competence_id, competence_name, type_id):
            # Обновляем связь с программой, если нужно
            if app.logic.db.update_competence_for_program(competence_id, old_competence[2], app.selected_program_id, competence_id, type_id):
                logging.info(f"Компетенция '{competence_name}' обновлена!")
            else:
                logging.error("Ошибка при обновлении связи компетенции с программой!")
        else:
            logging.error(f"Ошибка при обновлении компетенции '{competence_name}'!")

def delete_entity(app, parent_window, entity_type):
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
                app.universities = app.logic.db.fetch_universities()
                logging.info(f"ВУЗ '{values[0]}' удалён!")
        elif entity_type == "program":
            program_id = app.logic.db.fetch_program_id_by_name_and_code(values[0], values[1])[0]
            if app.logic.db.delete_educational_program(program_id):
                app.programs = app.logic.db.fetch_educational_programs_with_details()
                logging.info(f"Программа '{values[0]}' удалена!")
        elif entity_type == "competence":
            if not hasattr(app, 'selected_program_id'):
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
        logging.error(f"Ошибка при удалении {entity_type}: {e}")


def confirm_program_selection(app):
    if not hasattr(app, 'temp_selected_program'):
        logging.error("Выберите программу в таблице!")
        return

    name, code = app.temp_selected_program
    program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code)
    if program_id:
        app.add_window_selected_program_label.config(text=f"Выбрана программа: {name}")
        app.selected_program_id = program_id[0]
        logging.info(f"Программа '{name}' подтверждена, ID: {program_id[0]}")
        delattr(app, 'temp_selected_program')  # Удаляем временный выбор после подтверждения
    else:
        logging.error(f"Не удалось найти ID для программы: {name}, код: {code}")


# @staticmethod
def validate(possible_new_value):
    return bool(re.match(r'^[0-9a-fA-F]*$', possible_new_value))