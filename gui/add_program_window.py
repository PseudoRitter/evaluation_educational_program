import tkinter as tk
from tkinter import ttk
import logging
from moduls.database import Database  # Абсолютный импорт

def create_add_program_window(root, app):
    """Создание окна для добавления образовательной программы с функционалом работы с ВУЗами, ОП и компетенциями."""
    add_window = tk.Toplevel(root)
    add_window.title("Добавление образовательной программы")
    add_window.geometry("1200x800")  # Сохраняем ширину 1200, высоту 800

    # Основной фрейм для выравнивания
    main_frame = tk.Frame(add_window)
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Блок для ВУЗов (сверху)
    university_frame = tk.Frame(main_frame)
    university_frame.pack(pady=5, fill="x", expand=True)

    # Фрейм для таблицы ВУЗов
    university_table_frame = ttk.LabelFrame(university_frame, text="Выбор или работа с ВУЗами")
    university_table_frame.pack(pady=5, padx=5, fill="x", expand=True)

    # Таблица для ВУЗов (высота 200 пикселей)
    app.university_table = ttk.Treeview(university_table_frame, columns=("full_name", "short_name", "city"), show="headings", height=2)
    app.university_table.heading("full_name", text="Наименование ВУЗа")
    app.university_table.heading("short_name", text="Сокращение")
    app.university_table.heading("city", text="Город")
    app.university_table.column("full_name", width=400)
    app.university_table.column("short_name", width=150)
    app.university_table.column("city", width=150)
    app.university_table.pack(pady=5, fill="x", expand=False)

    # Фрейм для кнопок ВУЗов (под таблицей)
    university_button_frame = tk.Frame(university_frame)
    university_button_frame.pack(pady=5, padx=5)

    # Кнопки для ВУЗов в порядке: Добавить, Редактировать, Удалить
    app.add_university_button = tk.Button(university_button_frame, text="Добавить", command=lambda: add_new_university(app, add_window))
    app.add_university_button.pack(pady=5)

    app.edit_university_button = tk.Button(university_button_frame, text="Редактировать", command=lambda: edit_university(app, add_window))
    app.edit_university_button.pack(pady=5)

    app.delete_university_button = tk.Button(university_button_frame, text="Удалить", command=lambda: delete_university(app, add_window))
    app.delete_university_button.pack(pady=5)

    # Блок для образовательных программ (под ВУЗами)
    program_frame = tk.Frame(main_frame)
    program_frame.pack(pady=5, fill="x", expand=True)

    # Фрейм для таблицы образовательных программ
    program_table_frame = ttk.LabelFrame(program_frame, text="Добавить образовательную программу")
    program_table_frame.pack(pady=5, padx=5, fill="x", expand=True)

    # Таблица для образовательных программ (высота 200 пикселей)
    app.program_table = ttk.Treeview(program_table_frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=2)
    app.program_table.heading("name", text="Наименование ОП")
    app.program_table.heading("code", text="Код ОП")
    app.program_table.heading("year", text="Год ОП")
    app.program_table.heading("university_short", text="Краткое наименование ВУЗа")
    app.program_table.heading("type", text="Вид образовательной программы")
    app.program_table.column("name", width=200)
    app.program_table.column("code", width=100)
    app.program_table.column("year", width=80)  # Уменьшено для отображения текста года
    app.program_table.column("university_short", width=150)
    app.program_table.column("type", width=150)
    app.program_table.pack(pady=5, fill="x", expand=False)
    app.program_table.bind("<<TreeviewSelect>>", lambda event: on_program_table_select(app))

    # Фрейм для кнопок образовательных программ (под таблицей)
    program_button_frame = tk.Frame(program_frame)
    program_button_frame.pack(pady=5, padx=5)

    # Кнопки для образовательных программ в порядке: Добавить, Редактировать, Удалить, Выбрать
    app.add_program_button = tk.Button(program_button_frame, text="Добавить", command=lambda: add_new_program(app, add_window))
    app.add_program_button.pack(pady=5)

    app.edit_program_button = tk.Button(program_button_frame, text="Редактировать", command=lambda: edit_program(app, add_window))
    app.edit_program_button.pack(pady=5)

    app.delete_program_button = tk.Button(program_button_frame, text="Удалить", command=lambda: delete_program(app, add_window))
    app.delete_program_button.pack(pady=5)

    app.select_program_button = tk.Button(program_button_frame, text="Выбрать образовательную программу", command=lambda: confirm_program_selection(app))
    app.select_program_button.pack(pady=5)

    # Поле для отображения выбранной образовательной программы
    app.selected_program_label = tk.Label(program_frame, text="Выбрана программа: Нет")
    app.selected_program_label.pack(pady=5)

    # Блок для компетенций (под образовательными программами)
    competence_frame = tk.Frame(main_frame)
    competence_frame.pack(pady=5, fill="x", expand=True)

    # Фрейм для таблицы компетенций
    competence_table_frame = ttk.LabelFrame(competence_frame, text="Добавить компетенции")
    competence_table_frame.pack(pady=5, padx=5, fill="x", expand=True)

    # Таблица для компетенций (высота 200 пикселей)
    app.competence_table_add = ttk.Treeview(competence_table_frame, columns=("competence", "type"), show="headings", height=2)
    app.competence_table_add.heading("competence", text="Компетенция")
    app.competence_table_add.heading("type", text="Вид компетенции")
    app.competence_table_add.column("competence", width=400)
    app.competence_table_add.column("type", width=300)
    app.competence_table_add.pack(pady=5, fill="x", expand=False)

    # Фрейм для кнопок компетенций (под таблицей)
    competence_button_frame = tk.Frame(competence_frame)
    competence_button_frame.pack(pady=5, padx=5)

    # Кнопки для компетенций в порядке: Добавить, Редактировать, Удалить
    app.add_competence_button = tk.Button(competence_button_frame, text="Добавить", command=lambda: add_new_competence(app, add_window))
    app.add_competence_button.pack(pady=5)

    app.edit_competence_button = tk.Button(competence_button_frame, text="Редактировать", command=lambda: edit_competence(app, add_window))
    app.edit_competence_button.pack(pady=5)

    app.delete_competence_button = tk.Button(competence_button_frame, text="Удалить", command=lambda: delete_competence(app, add_window))
    app.delete_competence_button.pack(pady=5)

    # Стили для подсветки выбранной строки в таблицах
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

    # Заполняем таблицы данными из БД
    load_university_table(app)
    load_program_table(app)
    load_competence_table(app, None)  # Изначально без выбранной программы

def on_program_table_select(app):
    """Обработка выбора строки в таблице образовательных программ."""
    selected_item = app.program_table.selection()
    if selected_item:
        values = app.program_table.item(selected_item[0])['values']
        name, code, _, _, _ = values  # Наименование и код ОП
        logging.debug(f"Selected program in table: name={name}, code={code}")
        # Сохраняем временно выбранную программу для подтверждения
        app.temp_selected_program = (name, code)

def load_university_table(app):
    """Загрузка данных ВУЗов из БД в таблицу."""
    try:
        universities = app.logic.db.fetch_universities()
        for university in universities:
            app.university_table.insert("", tk.END, values=university)
    except Exception as e:
        logging.error(f"Ошибка при загрузке ВУЗов в таблицу: {e}")

def load_program_table(app):
    """Загрузка данных образовательных программ из БД в таблицу."""
    try:
        programs = app.logic.db.fetch_educational_programs_with_details()
        for program in programs:
            # Изменяем отображение года, чтобы показывать только год как текст (например, "2025")
            year = program[2] if program[2] else ""  # Берем год как есть
            app.program_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))
    except Exception as e:
        logging.error(f"Ошибка при загрузке образовательных программ в таблицу: {e}")

def load_competence_table(app, program_id):
    """Загрузка данных компетенций для выбранной образовательной программы из БД в таблицу."""
    try:
        if program_id:
            competences = app.logic.db.fetch_competences_for_program(program_id)
            app.competence_table_add.delete(*app.competence_table_add.get_children())
            for competence in competences:
                app.competence_table_add.insert("", tk.END, values=competence)
        else:
            app.competence_table_add.delete(*app.competence_table_add.get_children())
    except Exception as e:
        logging.error(f"Ошибка при загрузке компетенций в таблицу: {e}")

def add_new_university(app, parent_window):
    """Открытие окна для добавления нового ВУЗа."""
    add_university_window = tk.Toplevel(parent_window)
    add_university_window.title("Добавление нового ВУЗа")
    add_university_window.geometry("400x300")

    # Поля ввода для нового ВУЗа
    tk.Label(add_university_window, text="Наименование ВУЗа:").pack(pady=5)
    full_name_entry = tk.Entry(add_university_window)
    full_name_entry.pack(pady=5)

    tk.Label(add_university_window, text="Сокращение:").pack(pady=5)
    short_name_entry = tk.Entry(add_university_window)
    short_name_entry.pack(pady=5)

    tk.Label(add_university_window, text="Город:").pack(pady=5)
    city_entry = tk.Entry(add_university_window)
    city_entry.pack(pady=5)

    # Кнопка для сохранения нового ВУЗа
    tk.Button(add_university_window, text="Сохранить", command=lambda: save_new_university(app, add_university_window, parent_window, full_name_entry, short_name_entry, city_entry)).pack(pady=10)

def save_new_university(app, window, parent_window, full_name_entry, short_name_entry, city_entry):
    """Сохранение нового ВУЗа в БД."""
    full_name = full_name_entry.get().strip()
    short_name = short_name_entry.get().strip()
    city = city_entry.get().strip()

    if not full_name or not short_name or not city:
        logging.error("Все поля должны быть заполнены!")
        return

    try:
        university_id = app.logic.db.save_university(full_name, short_name, city)
        if university_id:
            # Обновляем таблицу ВУЗов в основном окне
            app.university_table.delete(*app.university_table.get_children())
            load_university_table(app)
            logging.info(f"ВУЗ '{full_name}' успешно добавлен!")
            window.destroy()  # Закрываем окно добавления ВУЗа
        else:
            logging.error("Не удалось добавить ВУЗ. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении ВУЗа: {e}")

def edit_university(app, parent_window):
    """Открытие окна для редактирования выбранного ВУЗа."""
    selected_item = app.university_table.selection()
    if not selected_item:
        logging.error("Выберите ВУЗ в таблице для редактирования!")
        return

    values = app.university_table.item(selected_item[0])['values']
    full_name, short_name, city = values  # Текущие данные ВУЗа

    edit_window = tk.Toplevel(parent_window)
    edit_window.title("Редактирование ВУЗа")
    edit_window.geometry("400x300")

    # Поля ввода для редактирования ВУЗа
    tk.Label(edit_window, text="Наименование ВУЗа:").pack(pady=5)
    full_name_entry = tk.Entry(edit_window)
    full_name_entry.insert(0, full_name)
    full_name_entry.pack(pady=5)

    tk.Label(edit_window, text="Сокращение:").pack(pady=5)
    short_name_entry = tk.Entry(edit_window)
    short_name_entry.insert(0, short_name)
    short_name_entry.pack(pady=5)

    tk.Label(edit_window, text="Город:").pack(pady=5)
    city_entry = tk.Entry(edit_window)
    city_entry.insert(0, city)
    city_entry.pack(pady=5)

    # Кнопка для сохранения изменений
    tk.Button(edit_window, text="Сохранить", command=lambda: save_edited_university(app, edit_window, parent_window, full_name_entry, short_name_entry, city_entry, full_name, short_name, city)).pack(pady=10)

def save_edited_university(app, window, parent_window, full_name_entry, short_name_entry, city_entry, old_full_name, old_short_name, old_city):
    """Сохранение отредактированного ВУЗа в БД."""
    new_full_name = full_name_entry.get().strip()
    new_short_name = short_name_entry.get().strip()
    new_city = city_entry.get().strip()

    if not new_full_name or not new_short_name or not new_city:
        logging.error("Все поля должны быть заполнены!")
        return

    try:
        # Получаем university_id по старым данным
        university_id = app.logic.db.fetch_university_id_by_details(old_full_name, old_short_name, old_city)
        if not university_id:
            logging.error("Не удалось найти ВУЗ для редактирования. Проверь данные.")
            return

        # Обновляем ВУЗ в БД
        success = app.logic.db.update_university(university_id[0], new_full_name, new_short_name, new_city)
        if success:
            # Обновляем таблицу ВУЗов в основном окне
            app.university_table.delete(*app.university_table.get_children())
            load_university_table(app)
            logging.info(f"ВУЗ обновлён: {new_full_name}")
            window.destroy()  # Закрываем окно редактирования
        else:
            logging.error("Не удалось обновить ВУЗ. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при редактировании ВУЗа: {e}")

def delete_university(app, parent_window):
    """Удаление выбранного ВУЗа из БД и таблицы."""
    selected_item = app.university_table.selection()
    if not selected_item:
        logging.error("Выберите ВУЗ в таблице для удаления!")
        return

    values = app.university_table.item(selected_item[0])['values']
    full_name, short_name, city = values  # Данные ВУЗа

    try:
        university_id = app.logic.db.fetch_university_id_by_details(full_name, short_name, city)
        if not university_id:
            logging.error("Не удалось найти ВУЗ для удаления. Проверь данные.")
            return

        # Удаляем ВУЗ из БД
        success = app.logic.db.delete_university(university_id[0])
        if success:
            # Обновляем таблицу ВУЗов в основном окне
            app.university_table.delete(*app.university_table.get_children())
            load_university_table(app)
            logging.info(f"ВУЗ '{full_name}' удалён!")
        else:
            logging.error("Не удалось удалить ВУЗ. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при удалении ВУЗа: {e}")

def add_new_program(app, parent_window):
    """Открытие окна для добавления новой образовательной программы."""
    add_program_window = tk.Toplevel(parent_window)
    add_program_window.title("Добавление новой образовательной программы")
    add_program_window.geometry("500x400")

    # Поля ввода для новой образовательной программы
    tk.Label(add_program_window, text="Наименование ОП:").pack(pady=5)
    name_entry = tk.Entry(add_program_window)
    name_entry.pack(pady=5)

    tk.Label(add_program_window, text="Код ОП:").pack(pady=5)
    code_entry = tk.Entry(add_program_window)
    code_entry.pack(pady=5)

    tk.Label(add_program_window, text="Год ОП:").pack(pady=5)
    year_entry = tk.Entry(add_program_window)
    year_entry.pack(pady=5)

    # Выпадающий список для ВУЗа (краткое наименование)
    tk.Label(add_program_window, text="Краткое наименование ВУЗа:").pack(pady=5)
    university_short_names = [u[1] for u in app.logic.db.fetch_universities()]  # Получаем краткие наименования ВУЗов
    university_var = tk.StringVar()
    university_combobox = ttk.Combobox(add_program_window, textvariable=university_var, values=university_short_names, state="readonly")
    university_combobox.pack(pady=5)

    # Выпадающий список для типа программы
    tk.Label(add_program_window, text="Вид образовательной программы:").pack(pady=5)
    program_types = [t[1] for t in app.logic.db.fetch_educational_program_types()]  # Получаем типы программ
    type_var = tk.StringVar()
    type_combobox = ttk.Combobox(add_program_window, textvariable=type_var, values=program_types, state="readonly")
    type_combobox.pack(pady=5)

    # Кнопка для сохранения новой образовательной программы
    tk.Button(add_program_window, text="Сохранить", command=lambda: save_new_program(app, add_program_window, parent_window, name_entry, code_entry, year_entry, university_var, type_var)).pack(pady=10)

def save_new_program(app, window, parent_window, name_entry, code_entry, year_entry, university_var, type_var):
    """Сохранение новой образовательной программы в БД."""
    name = name_entry.get().strip()
    code = code_entry.get().strip()
    year = year_entry.get().strip()
    university_short = university_var.get()
    type_name = type_var.get()

    if not name or not code or not year or not university_short or not type_name:
        logging.error("Все поля должны быть заполнены!")
        return

    # Сохраняем год как текст (например, "2025") без проверки
    formatted_year = year

    try:
        # Получаем university_id по краткому наименованию
        university = app.logic.db.fetch_university_by_short_name(university_short)
        if not university:
            logging.error(f"Не найден ВУЗ с кратким наименованием '{university_short}'. Проверь данные.")
            return
        university_id = university[0]

        # Получаем type_educational_program_id по названию типа
        program_type = app.logic.db.fetch_educational_program_type_by_name(type_name)
        if not program_type:
            logging.error(f"Не найден тип программы '{type_name}'. Проверь данные.")
            return
        type_program_id = program_type[0]

        # Сохранение образовательной программы (предполагаем, что компетенции пока пустые)
        program_id = app.logic.db.save_educational_program(name, code, university_id, formatted_year, type_program_id, [])
        if program_id:
            # Обновляем таблицу образовательных программ в основном окне
            app.program_table.delete(*app.program_table.get_children())
            load_program_table(app)
            # Обновляем таблицу образовательных программ на вкладке "ОП"
            app.load_education_table()  # Вызываем метод из app.py для обновления таблицы на вкладке "ОП"
            logging.info(f"Образовательная программа '{name}' успешно добавлена!")
            window.destroy()  # Закрываем окно добавления ОП
        else:
            logging.error("Не удалось добавить образовательную программу. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении образовательной программы: {e}")

def edit_program(app, parent_window):
    """Открытие окна для редактирования выбранной образовательной программы."""
    selected_item = app.program_table.selection()
    if not selected_item:
        logging.error("Выберите образовательную программу в таблице для редактирования!")
        return

    values = app.program_table.item(selected_item[0])['values']
    name, code, year, university_short, type_name = values  # Текущие данные ОП

    edit_window = tk.Toplevel(parent_window)
    edit_window.title("Редактирование образовательной программы")
    edit_window.geometry("500x400")

    # Поля ввода для редактирования ОП (те же, что и при добавлении)
    tk.Label(edit_window, text="Наименование ОП:").pack(pady=5)
    name_entry = tk.Entry(edit_window)
    name_entry.insert(0, name)
    name_entry.pack(pady=5)

    tk.Label(edit_window, text="Код ОП:").pack(pady=5)
    code_entry = tk.Entry(edit_window)
    code_entry.insert(0, code)
    code_entry.pack(pady=5)

    tk.Label(edit_window, text="Год ОП:").pack(pady=5)
    year_entry = tk.Entry(edit_window)
    year_entry.insert(0, year)  # Теперь показываем год как есть (например, "2025")
    year_entry.pack(pady=5)

    # Выпадающий список для ВУЗа (краткое наименование)
    tk.Label(edit_window, text="Краткое наименование ВУЗа:").pack(pady=5)
    university_short_names = [u[1] for u in app.logic.db.fetch_universities()]
    university_var = tk.StringVar(value=university_short)
    university_combobox = ttk.Combobox(edit_window, textvariable=university_var, values=university_short_names, state="readonly")
    university_combobox.pack(pady=5)

    # Выпадающий список для типа программы
    tk.Label(edit_window, text="Вид образовательной программы:").pack(pady=5)
    program_types = [t[1] for t in app.logic.db.fetch_educational_program_types()]
    type_var = tk.StringVar(value=type_name)
    type_combobox = ttk.Combobox(edit_window, textvariable=type_var, values=program_types, state="readonly")
    type_combobox.pack(pady=5)

    # Кнопка для сохранения изменений
    tk.Button(edit_window, text="Сохранить", command=lambda: save_edited_program(app, edit_window, parent_window, name_entry, code_entry, year_entry, university_var, type_var, name, code, year, university_short, type_name)).pack(pady=10)

def save_edited_program(app, window, parent_window, name_entry, code_entry, year_entry, university_var, type_var, old_name, old_code, old_year, old_university_short, old_type_name):
    """Сохранение отредактированной образовательной программы в БД."""
    new_name = name_entry.get().strip()
    new_code = code_entry.get().strip()
    new_year = year_entry.get().strip()
    new_university_short = university_var.get()
    new_type_name = type_var.get()

    if not new_name or not new_code or not new_year or not new_university_short or not new_type_name:
        logging.error("Все поля должны быть заполнены!")
        return

    # Сохраняем год как текст (например, "2025") без проверки
    formatted_year = new_year

    try:
        # Получаем program_id по старым данным
        program_id = app.logic.db.fetch_program_id_by_name_and_code(old_name, old_code)
        if not program_id:
            logging.error("Не удалось найти образовательную программу для редактирования. Проверь данные.")
            return

        # Получаем university_id по новому краткому наименованию
        university = app.logic.db.fetch_university_by_short_name(new_university_short)
        if not university:
            logging.error(f"Не найден ВУЗ с кратким наименованием '{new_university_short}'. Проверь данные.")
            return
        university_id = university[0]

        # Получаем type_educational_program_id по новому названию типа
        program_type = app.logic.db.fetch_educational_program_type_by_name(new_type_name)
        if not program_type:
            logging.error(f"Не найден тип программы '{new_type_name}'. Проверь данные.")
            return
        type_program_id = program_type[0]

        # Обновляем образовательную программу в БД
        success = app.logic.db.update_educational_program(program_id[0], new_name, new_code, university_id, formatted_year, type_program_id)
        if success:
            # Обновляем таблицу образовательных программ в основном окне
            app.program_table.delete(*app.program_table.get_children())
            load_program_table(app)
            # Обновляем таблицу образовательных программ на вкладке "ОП"
            app.load_education_table()  # Вызываем метод из app.py для обновления таблицы на вкладке "ОП"
            logging.info(f"Образовательная программа '{new_name}' обновлена!")
            window.destroy()  # Закрываем окно редактирования
        else:
            logging.error("Не удалось обновить образовательную программу. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при редактировании образовательной программы: {e}")

def delete_program(app, parent_window):
    """Удаление выбранной образовательной программы из БД и таблицы."""
    selected_item = app.program_table.selection()
    if not selected_item:
        logging.error("Выберите образовательную программу в таблице для удаления!")
        return

    values = app.program_table.item(selected_item[0])['values']
    name, code, _, _, _ = values  # Данные ОП (берем только название и код для поиска)

    try:
        program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code)
        if not program_id:
            logging.error("Не удалось найти образовательную программу для удаления. Проверь данные.")
            return

        # Удаляем образовательную программу из БД
        success = app.logic.db.delete_educational_program(program_id[0])
        if success:
            # Обновляем таблицу образовательных программ в основном окне
            app.program_table.delete(*app.program_table.get_children())
            load_program_table(app)
            # Обновляем таблицу образовательных программ на вкладке "ОП"
            app.load_education_table()  # Вызываем метод из app.py для обновления таблицы на вкладке "ОП"
            logging.info(f"Образовательная программа '{name}' удалена!")
        else:
            logging.error("Не удалось удалить образовательную программу. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при удалении образовательной программы: {e}")

def select_program(app, parent_window):
    """Открытие окна для выбора образовательной программы."""
    select_window = tk.Toplevel(parent_window)
    select_window.title("Выбор образовательной программы")
    select_window.geometry("500x400")

    # Таблица для выбора образовательной программы
    program_select_table = ttk.Treeview(select_window, columns=("name", "code", "year", "university_short", "type"), show="headings", height=4)
    program_select_table.heading("name", text="Наименование ОП")
    program_select_table.heading("code", text="Код ОП")
    program_select_table.heading("year", text="Год ОП")
    program_select_table.heading("university_short", text="Краткое наименование ВУЗа")
    program_select_table.heading("type", text="Вид образовательной программы")
    program_select_table.column("name", width=200)
    program_select_table.column("code", width=100)
    program_select_table.column("year", width=80)
    program_select_table.column("university_short", width=150)
    program_select_table.column("type", width=150)
    program_select_table.pack(pady=5, fill="x", expand=False)

    # Заполняем таблицу данными из БД
    try:
        programs = app.logic.db.fetch_educational_programs_with_details()
        for program in programs:
            year = program[2] if program[2] else ""  # Берем год как есть
            program_select_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))
    except Exception as e:
        logging.error(f"Ошибка при загрузке образовательных программ для выбора: {e}")

    # Кнопка для подтверждения выбора
    tk.Button(select_window, text="Выбрать", command=lambda: confirm_program_selection(app, select_window, program_select_table, parent_window)).pack(pady=10)

def confirm_program_selection(app):
    """Подтверждение выбора образовательной программы из таблицы и обновление метки."""
    if not hasattr(app, 'temp_selected_program'):
        logging.error("Сначала выберите строку в таблице образовательных программ!")
        return

    name, code = app.temp_selected_program
    program_id = app.logic.db.fetch_program_id_by_name_and_code(name, code)
    if program_id:
        app.selected_program_label.config(text=f"Выбрана программа: {name}")
        app.selected_program_id = program_id[0]  # Сохраняем ID выбранной программы
        logging.info(f"Выбрана программа: {name}, ID: {program_id[0]}")
        from .competence_utils import update_competence_table
        update_competence_table(app, program_id[0], table_name="competence_table_add")  # Обновляем таблицу в основном окне
        delattr(app, 'temp_selected_program')  # Очищаем временное значение
    else:
        logging.error(f"Не удалось найти ID для программы: {name}, код: {code}")

def add_new_competence(app, parent_window):
    """Открытие окна для добавления новой компетенции."""
    if not hasattr(app, 'selected_program_id') or not app.selected_program_id:
        logging.error("Сначала выберите образовательную программу!")
        return

    add_competence_window = tk.Toplevel(parent_window)
    add_competence_window.title("Добавление новой компетенции")
    add_competence_window.geometry("400x300")

    # Поле ввода для компетенции
    tk.Label(add_competence_window, text="Компетенция:").pack(pady=5)
    competence_entry = tk.Entry(add_competence_window)
    competence_entry.pack(pady=5)

    # Выпадающий список для вида компетенции
    tk.Label(add_competence_window, text="Вид компетенции:").pack(pady=5)
    competence_types = [t[1] for t in app.logic.db.fetch_competence_types()]  # Получаем виды компетенций
    type_var = tk.StringVar()
    type_combobox = ttk.Combobox(add_competence_window, textvariable=type_var, values=competence_types, state="readonly")
    type_combobox.pack(pady=5)

    # Кнопка для сохранения новой компетенции
    tk.Button(add_competence_window, text="Сохранить", command=lambda: save_new_competence(app, add_competence_window, parent_window, competence_entry, type_var)).pack(pady=10)

def save_new_competence(app, window, parent_window, competence_entry, type_var):
    """Сохранение новой компетенции и её связи с выбранной образовательной программой в БД."""
    competence_name = competence_entry.get().strip()
    competence_type_name = type_var.get()

    if not competence_name or not competence_type_name:
        logging.error("Все поля должны быть заполнены!")
        return

    try:
        # Проверяем, существует ли компетенция
        competence = app.logic.db.fetch_competence_by_name(competence_name)
        if not competence:
            # Если компетенции нет, создаём новую
            competence_types = app.logic.db.fetch_competence_types()
            type_competence_id = next((t[0] for t in competence_types if t[1] == competence_type_name), None)
            if not type_competence_id:
                logging.error(f"Не найден тип компетенции '{competence_type_name}'. Проверь данные.")
                return
            competence_id = app.logic.db.save_competence(competence_name, type_competence_id)
        else:
            competence_id, _, type_competence_id = competence  # Извлекаем type_competence_id из существующей компетенции

        # Сохраняем связь с образовательной программой
        if app.logic.db.save_competence_for_program(competence_id, type_competence_id, app.selected_program_id):
            # Обновляем таблицу компетенций в основном окне
            from .competence_utils import update_competence_table
            update_competence_table(app, app.selected_program_id, table_name="competence_table_add")
            logging.info(f"Компетенция '{competence_name}' успешно добавлена к программе!")
            window.destroy()  # Закрываем окно добавления компетенции
        else:
            logging.error("Не удалось добавить компетенцию к программе. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении компетенции: {e}")
        
def edit_competence(app, parent_window):
    """Открытие окна для редактирования выбранной компетенции."""
    if not hasattr(app, 'selected_program_id') or not app.selected_program_id:
        logging.error("Сначала выберите образовательную программу!")
        return

    selected_item = app.competence_table_add.selection()
    if not selected_item:
        logging.error("Выберите компетенцию в таблице для редактирования!")
        return

    values = app.competence_table_add.item(selected_item[0])['values']
    competence_name, competence_type_name = values  # Текущие данные компетенции

    edit_window = tk.Toplevel(parent_window)
    edit_window.title("Редактирование компетенции")
    edit_window.geometry("400x300")

    # Поле ввода для компетенции
    tk.Label(edit_window, text="Компетенция:").pack(pady=5)
    competence_entry = tk.Entry(edit_window)
    competence_entry.insert(0, competence_name)
    competence_entry.pack(pady=5)

    # Выпадающий список для вида компетенции
    tk.Label(edit_window, text="Вид компетенции:").pack(pady=5)
    competence_types = [t[1] for t in app.logic.db.fetch_competence_types()]  # Получаем виды компетенций
    type_var = tk.StringVar(value=competence_type_name)
    type_combobox = ttk.Combobox(edit_window, textvariable=type_var, values=competence_types, state="readonly")
    type_combobox.pack(pady=5)

    # Кнопка для сохранения изменений
    tk.Button(edit_window, text="Сохранить", command=lambda: save_edited_competence(app, edit_window, parent_window, competence_entry, type_var, competence_name, competence_type_name)).pack(pady=10)

def save_edited_competence(app, window, parent_window, competence_entry, type_var, old_competence_name, old_competence_type_name):
    """Сохранение отредактированной компетенции и её связи с образовательной программой в БД."""
    new_competence_name = competence_entry.get().strip()
    new_competence_type_name = type_var.get()

    if not new_competence_name or not new_competence_type_name:
        logging.error("Все поля должны быть заполнены!")
        return

    try:
        # Получаем текущие данные компетенции
        old_competence = app.logic.db.fetch_competence_by_name(old_competence_name)
        if not old_competence:
            logging.error(f"Не найдена компетенция '{old_competence_name}' для редактирования.")
            return
        old_competence_id, _, old_type_competence_id = old_competence

        # Проверяем или создаём новую компетенцию
        new_competence = app.logic.db.fetch_competence_by_name(new_competence_name)
        if not new_competence:
            new_type_competence = app.logic.db.fetch_competence_types()
            new_type_id = next((t[0] for t in new_type_competence if t[1] == new_competence_type_name), None)
            if not new_type_id:
                logging.error(f"Не найден тип компетенции '{new_competence_type_name}'. Проверь данные.")
                return
            new_competence_id = app.logic.db.save_competence(new_competence_name, new_type_id)
        else:
            new_competence_id, _, new_type_competence_id = new_competence

        # Обновляем связь с образовательной программой
        if app.logic.db.update_competence_for_program(old_competence_id, old_type_competence_id, app.selected_program_id, new_competence_id, new_type_competence_id):
            # Обновляем таблицу компетенций в основном окне
            from .competence_utils import update_competence_table
            update_competence_table(app, app.selected_program_id, table_name="competence_table_add")
            logging.info(f"Компетенция обновлена: {new_competence_name}")
            window.destroy()  # Закрываем окно редактирования компетенции
        else:
            logging.error("Не удалось обновить компетенцию. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при редактировании компетенции: {e}")

def delete_competence(app, parent_window):
    """Удаление выбранной компетенции из связи с образовательной программой."""
    if not hasattr(app, 'selected_program_id') or not app.selected_program_id:
        logging.error("Сначала выберите образовательную программу!")
        return

    selected_item = app.competence_table_add.selection()
    if not selected_item:
        logging.error("Выберите компетенцию в таблице для удаления!")
        return

    values = app.competence_table_add.item(selected_item[0])['values']
    competence_name, competence_type_name = values  # Данные компетенции

    try:
        competence = app.logic.db.fetch_competence_by_name(competence_name)
        if not competence:
            logging.error(f"Не найдена компетенция '{competence_name}' для удаления.")
            return
        competence_id, _, type_competence_id = competence

        # Удаляем связь с образовательной программой
        if app.logic.db.delete_competence_for_program(competence_id, type_competence_id, app.selected_program_id):
            # Обновляем таблицу компетенций в основном окне
            from .competence_utils import update_competence_table
            update_competence_table(app, app.selected_program_id, table_name="competence_table_add")
            logging.info(f"Компетенция '{competence_name}' удалена из программы!")
        else:
            logging.error("Не удалось удалить компетенцию из программы. Проверь данные.")
    except Exception as e:
        logging.error(f"Ошибка при удалении компетенции: {e}")