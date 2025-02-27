import tkinter as tk
from tkinter import ttk
import logging
from .add_program_window import create_add_program_window

def create_education_tab(frame, app):
    """Создание вкладки для образовательных программ."""
    # Заголовок для таблицы
    label = tk.Label(frame, text="Выберите образовательную программу:")
    label.pack(pady=5)

    # Верхняя таблица для образовательных программ (высота 250 пикселей)
    app.education_table = ttk.Treeview(frame, columns=("name", "code", "year", "university_short", "type"), show="headings", height=8)
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
    app.education_table.pack(pady=5, fill="x", expand=False)

    # Кнопка "Выбрать"
    app.select_button = tk.Button(frame, text="Выбрать", command=lambda: app.on_table_select())
    app.select_button.pack(pady=5)

    # Надпись для отображения выбранной программы
    app.selected_program_label = tk.Label(frame, text="Выбрана программа: Нет")
    app.selected_program_label.pack(pady=5)

    # Фрейм для таблицы компетенций
    competence_frame = ttk.LabelFrame(frame, text="Компетенции программы")
    competence_frame.pack(pady=5, padx=5, fill="both", expand=True)

    # Нижняя таблица для компетенций (высота 300 пикселей)
    app.competence_table = ttk.Treeview(competence_frame, columns=("competence", "competence_type"), show="headings", height=10)
    app.competence_table.heading("competence", text="Компетенция")
    app.competence_table.heading("competence_type", text="Вид компетенции")
    app.competence_table.column("competence", width=400)
    app.competence_table.column("competence_type", width=300)
    app.competence_table.pack(pady=5, fill="both", expand=True)

    # Стиль для подсветки выбранной строки в таблицах
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[("selected", "blue")], foreground=[("selected", "white")])

    # Заполняем верхнюю таблицу данными из БД
    app.load_education_table()

    # Привязываем событие выбора строки в верхней таблице для предварительного отображения компетенций
    app.education_table.bind("<<TreeviewSelect>>", lambda event: app.preview_competences())

    # Кнопка "Добавить образовательную программу"
    app.add_program_button = tk.Button(frame, text="Добавить образовательную программу", command=lambda: create_add_program_window(app.root, app))
    app.add_program_button.pack(pady=10)
    
def load_education_table(self):
    """Загрузка данных образовательных программ в таблицу из БД."""
    try:
        programs = self.logic.db.fetch_educational_programs_with_details()
        for program in programs:
            self.education_table.insert("", tk.END, values=program)
    except Exception as e:
        logging.error(f"Ошибка при загрузке образовательных программ в таблицу: {e}")
        self.show_error(f"Не удалось загрузить программы: {e}")

def preview_competences(self):
    """Предварительное отображение компетенций выбранной программы при выборе строки в таблице."""
    selected_item = self.education_table.selection()
    if selected_item:
        values = self.education_table.item(selected_item[0])['values']
        program_name, program_code = values[0], values[1]  # Наименование и код ОП
        program_id = self._get_program_id_from_table(values)
        if program_id:
            competences = self.logic.db.fetch_program_details(program_id)
            self.competence_table.delete(*self.competence_table.get_children())
            for competence in competences:
                competence_name, competence_type = competence[5], competence[6]  # competence_name, type_competence_full_name
                if competence_name:  # Убедимся, что компетенция существует
                    self.competence_table.insert("", tk.END, values=(competence_name, competence_type or "Неизвестно"))

def on_table_select(self):
    """Обработка выбора образовательной программы из таблицы."""
    selected_item = self.education_table.selection()
    if selected_item:
        values = self.education_table.item(selected_item[0])['values']
        program_name = values[0]  # Наименование ОП
        self.selected_program_label.config(text=f"Выбрана программа: {program_name}")
        program_id = self._get_program_id_from_table(values)
        self.program_id = program_id  # Сохраняем ID для использования в start_analysis
        logging.info(f"Выбрана программа с наименованием: {program_name}, ID: {program_id}")
        self.preview_competences()
    else:
        self.show_error("Выберите строку в таблице!")

def _get_program_id_from_table(self, values):
    """Получение program_id на основе данных из таблицы."""
    try:
        name, code = values[0], values[1]
        query_result = self.logic.db.fetch_program_id_by_name_and_code(name, code)
        return query_result[0] if query_result else None
    except Exception as e:
        logging.error(f"Ошибка при получении ID программы: {e}")
        return None