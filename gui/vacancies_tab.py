import tkinter as tk
import os
from tkinter import filedialog
from tkinter import ttk
import logging
from moduls.database import Database
from moduls.labor_market_data import LaborMarketData  # Новый импорт
from datetime import datetime

def create_vacancies_tab(frame, app):
    container_frame = tk.Frame(frame)
    container_frame.pack(pady=5, padx=5, fill="both", expand=False)

    vacancies_frame = ttk.LabelFrame(container_frame, text="Вакансии с сайта")
    vacancies_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=False)

    # Убираем "id" из отображаемых колонок
    app.vacancies_table = ttk.Treeview(vacancies_frame, columns=("id", "name", "quantity", "collection_date", "file"), show="headings", height=10, selectmode="browse")
    app.vacancies_table.heading("id", text="ID")
    app.vacancies_table.heading("name", text="Название вакансии")
    app.vacancies_table.heading("quantity", text="Количество вакансий")
    app.vacancies_table.heading("collection_date", text="Дата сбора")
    app.vacancies_table.heading("file", text="Файл вакансий")
    app.vacancies_table.column("id", width=0, stretch=False)  # Скрываем столбец "id"
    app.vacancies_table.column("name", width=200)  # Увеличено для общей ширины ~900
    app.vacancies_table.column("quantity", width=150)
    app.vacancies_table.column("collection_date", width=150)
    app.vacancies_table.column("file", width=400)
    app.vacancies_table.pack(pady=5, fill="both", expand=True)

    button_frame = tk.Frame(container_frame)
    button_frame.pack(side=tk.LEFT, padx=10, fill="y")

    tk.Button(button_frame, text="Добавить", command=lambda: edit_vacancy_window(app, None, "add")).pack(pady=5)
    tk.Button(button_frame, text="Редактировать", command=lambda: edit_vacancy_window(app, app.vacancies_table.selection(), "edit")).pack(pady=5)
    tk.Button(button_frame, text="Удалить", command=lambda: delete_vacancy(app)).pack(pady=5)

    select_frame = tk.Frame(frame)
    select_frame.pack(pady=5)

    app.select_vacancy_button = tk.Button(select_frame, text="Выбрать", command=lambda: on_vacancy_select(app))
    app.select_vacancy_button.pack(side=tk.LEFT, padx=5)

    app.selected_vacancy_label = tk.Label(select_frame, text="Выбрана вакансия: Нет")
    app.selected_vacancy_label.pack(side=tk.LEFT, padx=5)

    # Создаём новый фрейм для поиска вакансий
    search_vacancies_frame = tk.Frame(frame)
    search_vacancies_frame.pack(pady=5)

    # Добавляем текст, поле ввода и кнопку поиска в новый фрейм
    tk.Label(search_vacancies_frame, text="Поисковый запрос вакансии:").pack(side=tk.LEFT, padx=5)
    app.search_query_entry = tk.Entry(search_vacancies_frame)
    app.search_query_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(search_vacancies_frame, text="Поиск вакансий", command=lambda: search_vacancies(app)).pack(side=tk.LEFT, padx=5)
    load_vacancies_table(app)

def search_vacancies(app):
    """Функция для поиска вакансий через LaborMarketData и добавления в таблицу после полного сбора."""
    query = app.search_query_entry.get().strip()
    if not query:
        app.show_error("Введите поисковый запрос!")
        return

    ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
    hh_data = LaborMarketData(query=query, access_token=ACCESS_TOKEN)
    try:
        hh_data.collect_all_vacancies()
        current_date_time = datetime.now().strftime("%Y-%m-%d %H-%M")  # Формат YYYY-MM-DD HH-MI
        filename = f"vacancies_hh/{query} {current_date_time}.json"
        hh_data.save_to_json(filename)  # Сначала собираем и сохраняем все вакансии
        
        # После сбора всех вакансий добавляем запись в БД
        vacancy_name = query
        vacancy_quantity = len(hh_data.vacancies)
        vacancy_date = current_date_time
        vacancy_file = f"{query} {current_date_time}.json"

        vacancy_id = app.logic.db.save_vacancy(vacancy_name, vacancy_quantity, vacancy_date, vacancy_file)
        if vacancy_id:
            app.show_info(f"Вакансии сохранены в {filename} и добавлены в БД (ID: {vacancy_id})")
        else:
            app.show_error("Не удалось сохранить вакансию в БД!")
        
        # Обновляем таблицу после добавления в БД
        load_vacancies_table(app)
    except Exception as e:
        app.show_error(f"Ошибка при сборе вакансий: {e}")
        logging.error(f"Ошибка при сборе вакансий для запроса '{query}': {e}")

def on_vacancy_select(app):
    selected_item = app.vacancies_table.selection()
    if not selected_item:
        logging.error("Выберите вакансию в таблице!")
        app.show_error("Выберите вакансию в таблице!")
        return

    values = app.vacancies_table.item(selected_item[0])['values']
    vacancy_id = values[0]
    vacancy_name = values[1]
    app.selected_vacancy_id = vacancy_id  # Сохраняем ID для анализа
    app.selected_vacancy_label.config(text=f"Выбрана вакансия: {vacancy_name} (ID: {vacancy_id})")
    logging.info(f"Выбрана вакансия: {vacancy_name}, ID: {vacancy_id}")

def load_vacancies_table(app):
    try:
        vacancies = app.logic.db.fetch_vacancies()
        app.vacancies_table.delete(*app.vacancies_table.get_children())
        for vacancy in vacancies:
            app.vacancies_table.insert("", tk.END, values=(vacancy[0], vacancy[1], vacancy[2], vacancy[3], vacancy[4]))
    except Exception as e:
        logging.error(f"Ошибка при загрузке вакансий: {e}")

def edit_vacancy_window(app, selected_item, action):
    if action == "edit" and not selected_item:
        logging.error("Выберите вакансию для редактирования!")
        return

    window = tk.Toplevel(app.root)
    window.title(f"{action.capitalize()} вакансии")
    window.geometry("400x400")

    tk.Label(window, text="Название вакансии:").pack(pady=5)
    name_entry = tk.Entry(window)
    name_entry.pack(pady=5)

    tk.Label(window, text="Количество вакансий:").pack(pady=5)
    quantity_entry = tk.Entry(window)
    quantity_entry.pack(pady=5)

    tk.Label(window, text="Дата сбора (YYYY-MM-DD):").pack(pady=5)
    date_entry = tk.Entry(window)
    date_entry.pack(pady=5)

    tk.Label(window, text="Файл вакансий:").pack(pady=5)
    file_entry = tk.Entry(window)
    file_entry.pack(pady=5)
    tk.Button(window, text="Выбрать файл", command=lambda: file_entry.insert(tk.END, os.path.basename(filedialog.askopenfilename()))).pack(pady=5)
    
    if action == "edit":
        values = app.vacancies_table.item(selected_item[0])['values']
        name_entry.insert(0, values[1])
        quantity_entry.insert(0, values[2])
        date_entry.insert(0, values[3])
        file_entry.insert(0, values[4])

    tk.Button(window, text="Сохранить", command=lambda: save_vacancy(app, window, name_entry.get(), quantity_entry.get(), date_entry.get(), file_entry.get(), action, selected_item)).pack(pady=10)

def save_vacancy(app, window, name, quantity, date, file_path, action, selected_item=None):
    try:
        if not all([name, quantity, date, file_path]):
            logging.error("Все поля должны быть заполнены!")
            return

        quantity = int(quantity)
        if action == "add":
            vacancy_id = app.logic.db.save_vacancy(name, quantity, date, file_path)
            if vacancy_id:
                load_vacancies_table(app)
                logging.info(f"Вакансия '{name}' добавлена!")
        elif action == "edit":
            if selected_item:
                values = app.vacancies_table.item(selected_item[0])['values']
                vacancy_id = values[0]
                if app.logic.db.update_vacancy(vacancy_id, name, quantity, date, file_path):
                    load_vacancies_table(app)
                    logging.info(f"Вакансия '{name}' обновлена!")
        window.destroy()
    except ValueError as ve:
        logging.error(f"Неверный формат данных: {ve}")
        app.show_error("Количество вакансий должно быть числом!")
    except Exception as e:
        logging.error(f"Ошибка при сохранении вакансии: {e}")
        app.show_error("Произошла ошибка при сохранении вакансии!")

def delete_vacancy(app):
    selected_item = app.vacancies_table.selection()
    if not selected_item:
        logging.error("Выберите вакансию для удаления!")
        return

    try:
        values = app.vacancies_table.item(selected_item[0])['values']
        vacancy_id = values[0]
        if app.logic.db.delete_vacancy(vacancy_id):
            load_vacancies_table(app)
            logging.info(f"Вакансия '{values[1]}' удалена!")
    except Exception as e:
        logging.error(f"Ошибка при удалении вакансии: {e}")

