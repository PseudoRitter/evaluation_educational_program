import tkinter as tk
from tkinter import ttk
import logging
from .add_program_window import create_add_program_window, update_competence_table  # Обновлён импорт

def create_education_tab(frame, app):
    """Создание вкладки для образовательных программ."""
    # Фрейм для заголовка и таблицы образовательных программ
    education_program_frame = tk.Frame(frame)
    education_program_frame.pack(pady=4, fill="x", expand=False)

    # Фрейм для таблицы образовательных программ
    education_table_frame = ttk.LabelFrame(education_program_frame, text="Выбор образовтельной программы")
    education_table_frame.pack(pady=4, padx=4, fill="both", expand=False)

    # Таблица образовательных программ
    app.education_table = ttk.Treeview(education_table_frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=8 )
    app.education_table.heading("name", text="Наименование ОП")
    app.education_table.heading("code", text="Код ОП")
    app.education_table.heading("year", text="Год ОП")
    app.education_table.heading("university_short", text="Краткое наименование ВУЗа")
    app.education_table.heading("type", text="Вид образовательной программы")
    app.education_table.column("name", width=200)
    app.education_table.column("code", width=100)
    app.education_table.column("year", width=80)
    app.education_table.column("university_short", width=150)
    app.education_table.column("type", width=150)
    app.education_table.pack(pady=4, fill="x", expand=False)

    # Кнопка "Выбрать"
    app.select_button = tk.Button(frame, text="Выбрать", command=lambda: on_table_select(app))
    app.select_button.pack(pady=4)

    # Надпись для отображения выбранной программы
    app.selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")
    app.selected_program_label.pack(pady=4)

    # Фрейм для таблицы компетенций
    app.competence_frame = ttk.LabelFrame(frame, text="Компетенции программы")
    app.competence_frame.pack(pady=4, padx=4, fill="both", expand=False)

    # Таблица компетенций
    app.competence_table = ttk.Treeview(app.competence_frame, columns=("competence", "competence_type"), show="headings", height=12)
    app.competence_table.heading("competence", text="Компетенция")
    app.competence_table.heading("competence_type", text="Вид компетенции")
    app.competence_table.column("competence", width=400)
    app.competence_table.column("competence_type", width=300)
    app.competence_table.pack(pady=4, fill="both", expand=False)

    # Кнопка "Добавить образовательную программу"
    app.add_program_button = tk.Button(frame, text="Добавить образовательную программу", command=lambda: create_add_program_window(app.root, app))
    app.add_program_button.pack(pady=10)

    # Стиль для подсветки выбранной строки
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

    # Загрузка данных в таблицу
    load_education_table(app)

    # Привязка события выбора строки
    app.education_table.bind("<<TreeviewSelect>>", lambda event: update_competence_table(app, _get_program_id_from_table(app, app.education_table.item(app.education_table.selection()[0])['values'] if app.education_table.selection() else None)))

    

def load_education_table(app):
    """Загрузка данных образовательных программ в таблицу из БД."""
    try:
        programs = app.logic.db.fetch_educational_programs_with_details()
        app.education_table.delete(*app.education_table.get_children())
        for program in programs:
            year = program[2] if program[2] else ""
            app.education_table.insert("", tk.END, values=(program[0], program[1], year, program[3], program[4]))
    except Exception as e:
        logging.error(f"Ошибка при загрузке образовательных программ: {e}")
        app.show_error(f"Не удалось загрузить программы: {e}")

def preview_competences(app):
    """Предварительное отображение компетенций выбранной программы."""
    selected_item = app.education_table.selection()
    if not selected_item:
        app.show_error("Выберите строку в таблице!")
        return

    values = app.education_table.item(selected_item[0])['values']
    program_name, program_code = values[0], values[1]
    program_id = _get_program_id_from_table(app, values)

    if not program_id:
        logging.error(f"Не удалось найти ID для программы: {program_name}, код: {program_code}")
        return

    if not hasattr(app, 'competence_table') or not app.competence_table.winfo_exists():
        logging.warning("Таблица компетенций недоступна. Инициализация новой.")
        app.competence_frame = ttk.LabelFrame(app.education_tab, text="Компетенции программы")
        app.competence_frame.pack(pady=4, padx=4, fill="both", expand=False)
        app.competence_table = ttk.Treeview(app.competence_frame, columns=("competence", "competence_type"), show="headings", height=14)
        app.competence_table.heading("competence", text="Компетенция")
        app.competence_table.heading("competence_type", text="Вид компетенции")
        app.competence_table.column("competence", width=400)
        app.competence_table.column("competence_type", width=300)
        app.competence_table.pack(pady=4, fill="both", expand=False)

    app.competence_table.delete(*app.competence_table.get_children())
    competences = app.logic.db.fetch_program_details(program_id)
    for competence in competences:
        competence_name, competence_type = competence[5], competence[6]
        if competence_name:
            app.competence_table.insert("", tk.END, values=(competence_name, competence_type or "Неизвестно"))

def on_table_select(app):
    """Обработка выбора образовательной программы из таблицы."""
    selected_item = app.education_table.selection()
    if not selected_item:
        app.show_error("Выберите строку в таблице!")
        return

    values = app.education_table.item(selected_item[0])['values']
    program_name = values[0]
    program_id = _get_program_id_from_table(app, values)

    if program_id:
        if app.selected_program_label.winfo_exists():  # Проверка существования
            app.selected_program_label.config(text=f"Выбрана программа: {program_name}")
        app.program_id = program_id
        logging.info(f"Выбрана программа: {program_name}, ID: {program_id}")
        preview_competences(app)
    else:
        logging.error(f"Не удалось найти ID для программы: {program_name}")
        app.show_error("Не удалось определить ID программы.")

def _get_program_id_from_table(app, values):
    """Получение program_id на основе данных из таблицы."""
    try:
        name, code = values[0], values[1]
        query_result = app.logic.db.fetch_program_id_by_name_and_code(name, code)
        if query_result is None:
            logging.error(f"Программа с именем '{name}' и кодом '{code}' не найдена в БД.")
            return None
        return query_result[0]
    except Exception as e:
        logging.error(f"Ошибка при получении ID программы: {e}")
        return None