import tkinter as tk
from tkinter import filedialog, ttk
import logging
from moduls.labor_market_data import LaborMarketData
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

def create_vacancies_tab(frame, app):
    app.vac_executor = ThreadPoolExecutor(max_workers=1)  # Для асинхронных задач

    container_frame = tk.Frame(frame)
    container_frame.pack(pady=5, padx=5, fill="both", expand=False)

    vacancies_frame = ttk.LabelFrame(container_frame, text="Вакансии с сайта")
    vacancies_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=False)

    app.vacancies_table = ttk.Treeview(vacancies_frame, columns=("id", "name", "quantity", "collection_date", "file"), show="headings", height=10, selectmode="browse")
    app.vacancies_table.heading("id", text="ID")
    app.vacancies_table.heading("name", text="Название вакансии")
    app.vacancies_table.heading("quantity", text="Количество вакансий")
    app.vacancies_table.heading("collection_date", text="Дата сбора")
    app.vacancies_table.heading("file", text="Файл вакансий")
    app.vacancies_table.column("id", width=0, stretch=False)
    app.vacancies_table.column("name", width=200)
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

    search_vacancies_frame = tk.Frame(frame)
    search_vacancies_frame.pack(pady=5)

    tk.Label(search_vacancies_frame, text="Поисковый запрос:").pack(side=tk.LEFT, padx=5)
    app.search_query_entry = tk.Entry(search_vacancies_frame)
    app.search_query_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(search_vacancies_frame, text="Поиск вакансий", command=lambda: app.vac_executor.submit(search_vacancies, app)).pack(side=tk.LEFT, padx=5)

    load_vacancies_table(app)

async def search_vacancies(app):
    query = app.search_query_entry.get().strip()
    if not query:
        app.show_error("Введите поисковый запрос!")
        return

    ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
    hh_data = LaborMarketData(query=query, access_token=ACCESS_TOKEN)
    try:
        await hh_data.collect_all_vacancies()
        current_date_time = datetime.now().strftime("%Y-%m-%d %H-%M")
        filename = f"vacancies_hh/{query} {current_date_time}.json"
        await hh_data.save_to_json(filename)

        vacancy_id = app.logic.db.save_vacancy(query, len(hh_data.vacancies), current_date_time, filename)
        if vacancy_id:
            app.show_info(f"Вакансии сохранены в {filename} (ID: {vacancy_id})")
            load_vacancies_table(app)
        else:
            app.show_error("Ошибка сохранения в БД!")
    except Exception as e:
        app.show_error(f"Ошибка сбора вакансий: {e}")
        logging.error(f"Ошибка сбора вакансий '{query}': {e}")

def on_vacancy_select(app):
    selected_item = app.vacancies_table.selection()
    if not selected_item:
        app.show_error("Выберите вакансию!")
        return

    values = app.vacancies_table.item(selected_item[0])['values']
    app.selected_vacancy_id = values[0]
    app.selected_vacancy_label.config(text=f"Выбрана вакансия: {values[1]}")
    logging.info(f"Выбрана вакансия: {values[1]}, ID: {values[0]}")

def load_vacancies_table(app):
    try:
        vacancies = app.logic.db.fetch_vacancies()
        app.vacancies_table.delete(*app.vacancies_table.get_children())
        for vacancy in vacancies:
            app.vacancies_table.insert("", tk.END, values=vacancy)
    except Exception as e:
        logging.error(f"Ошибка загрузки вакансий: {e}")

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
    tk.Button(window, text="Выбрать файл", command=lambda: file_entry.insert(tk.END, filedialog.askopenfilename())).pack(pady=5)

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
        elif action == "edit" and selected_item:
            values = app.vacancies_table.item(selected_item[0])['values']
            if app.logic.db.update_vacancy(values[0], name, quantity, date, file_path):
                load_vacancies_table(app)
                logging.info(f"Вакансия '{name}' обновлена!")
        window.destroy()
    except ValueError as ve:
        logging.error(f"Неверный формат: {ve}")
        app.show_error("Количество должно быть числом!")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")
        app.show_error("Ошибка сохранения!")

def delete_vacancy(app):
    selected_item = app.vacancies_table.selection()
    if not selected_item:
        logging.error("Выберите вакансию для удаления!")
        return

    values = app.vacancies_table.item(selected_item[0])['values']
    try:
        if app.logic.db.delete_vacancy(values[0]):
            load_vacancies_table(app)
            logging.info(f"Вакансия '{values[1]}' удалена!")
    except Exception as e:
        logging.error(f"Ошибка удаления: {e}")