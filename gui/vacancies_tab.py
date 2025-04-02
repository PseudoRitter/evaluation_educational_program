import tkinter as tk
from tkinter import ttk, filedialog
import logging
from moduls.labor_market_data import LaborMarketData
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
from moduls.table_processing import sort_treeview_column, sort_competence_type_column, add_tooltip_to_treeview

def create_vacancies_tab(frame, app):
    app.vac_executor = ThreadPoolExecutor(max_workers=1)

    container_frame = tk.Frame(frame)
    container_frame.pack(pady=5, padx=5, fill="both", expand=False)

    vacancies_frame = ttk.LabelFrame(container_frame, text="Вакансии с сайта")
    vacancies_frame.pack(side=tk.LEFT, pady=5, padx=5, fill="both", expand=True)

    app.vacancies_table = ttk.Treeview(vacancies_frame, columns=("id", "name", "quantity", "collection_date", "file"), show="headings", height=17)
    app.vacancies_table.heading("id", text="ID")
    app.vacancies_table.heading("name", text="Название вакансии", command=lambda: sort_treeview_column(app.vacancies_table, "name", False))
    app.vacancies_table.heading("quantity", text="Количество вакансий", command=lambda: sort_treeview_column(app.vacancies_table, "quantity", False))
    app.vacancies_table.heading("collection_date", text="Дата сбора", command=lambda: sort_treeview_column(app.vacancies_table, "collection_date", False))
    app.vacancies_table.heading("file", text="Файл вакансий", command=lambda: sort_treeview_column(app.vacancies_table, "file", False))
    app.vacancies_table.column("id", width=0, stretch=False)
    app.vacancies_table.column("name", width=330)
    app.vacancies_table.column("quantity", width=120)
    app.vacancies_table.column("collection_date", width=100)
    app.vacancies_table.column("file", width=250)
    app.vacancies_table.pack(pady=5, fill="both", expand=True)

    add_tooltip_to_treeview(app.vacancies_table)

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
    app.search_query_entry = tk.Entry(search_vacancies_frame, width=60)
    app.search_query_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(search_vacancies_frame, text="Поиск вакансий", command=lambda: start_search(app)).pack(side=tk.LEFT, padx=5)

    # Добавляем скрытый Label для прогресса
    app.progress_label = tk.Label(frame, text="")
    app.progress_label.pack(pady=5)
    app.progress_label.pack_forget()  # Скрываем изначально

    load_vacancies_table(app)

def start_search(app):
    query = app.search_query_entry.get().strip()
    if not query:
        app.show_error("Введите поисковый запрос!")
        return

    app.show_info("Поиск вакансий начат...")
    app.progress_label.config(text="Прогресс сбора вакансий: Инициализация... 0% (0/0)")
    app.progress_label.pack()  # Показываем прогресс

    def callback(future):
        try:
            vacancy_id = future.result()
            if vacancy_id:
                app.root.after(0, lambda: load_vacancies_table(app))
                app.show_info(f"Вакансии сохранены (ID: {vacancy_id})")
            else:
                app.show_error("Ошибка сохранения в БД!")
        except Exception as e:
            app.show_error(f"Ошибка сбора вакансий: {e}")
            logging.error(f"Ошибка в callback поиска вакансий: {e}")
        finally:
            app.root.after(0, lambda: app.progress_label.pack_forget())  # Скрываем прогресс после завершения

    future = app.vac_executor.submit(search_vacancies, app)
    future.add_done_callback(callback)

    # Запускаем обновление прогресса
    app.root.after(100, lambda: update_progress(app))

def update_progress(app):
    if hasattr(app, "labor_market_instance") and app.labor_market_instance:
        total = len(app.labor_market_instance.vacancies)
        current = len(app.labor_market_instance.temp)
        if total > 0:
            percentage = (current / total) * 100
            progress_text = f"Прогресс сбора вакансий: {app.search_query_entry.get()} {percentage:.1f}% ({current}/{total})"
            app.progress_label.config(text=progress_text)
        else:
            app.progress_label.config(text="Прогресс сбора вакансий: Сбор данных... 0% (0/0)")
        
        # Продолжаем обновление каждые 100 мс, если процесс еще идет
        if app.vac_executor._threads:  # Проверяем, что поток еще активен
            app.root.after(100, lambda: update_progress(app))

def search_vacancies(app):
    query = app.search_query_entry.get().strip()
    if not query:
        app.show_error("Введите поисковый запрос!")
        return None

    ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
    hh_data = LaborMarketData(query=query, access_token=ACCESS_TOKEN)
    app.labor_market_instance = hh_data  # Сохраняем экземпляр в app
    try:
        hh_data.collect_all_vacancies()
        current_date_time = datetime.now().strftime("%Y-%m-%d %H-%M")
        filename = f"{query} {current_date_time}.json"
        full_path = f"vacancies_hh/{filename}"

        os.makedirs("vacancies_hh", exist_ok=True)
        
        hh_data.save_to_json(full_path)

        vacancy_id = app.logic.db.save_vacancy(query, len(hh_data.vacancies), current_date_time, filename)
        if vacancy_id:
            return vacancy_id
        else:
            app.show_error("Ошибка сохранения в БД!")
            return None
    except Exception as e:
        app.show_error(f"Ошибка сбора вакансий: {e}")
        logging.error(f"Ошибка сбора вакансий '{query}': {e}")
        return None
    finally:
        app.labor_market_instance = None  # Очищаем после завершения

def on_vacancy_select(app):
    selected_item = app.vacancies_table.selection()
    if not selected_item:
        app.show_error("Выберите вакансию!")
        return

    values = app.vacancies_table.item(selected_item[0])["values"]
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
    tk.Button(window, text="Выбрать файл", command=lambda: file_entry.delete(0, tk.END) or file_entry.insert(tk.END, os.path.basename(filedialog.askopenfilename()))).pack(pady=5)

    if action == "edit":
        values = app.vacancies_table.item(selected_item[0])["values"]
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
            values = app.vacancies_table.item(selected_item[0])["values"]
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

    values = app.vacancies_table.item(selected_item[0])["values"]
    try:
        if app.logic.db.delete_vacancy(values[0]):
            load_vacancies_table(app)
            logging.info(f"Вакансия '{values[1]}' удалена!")
    except Exception as e:
        logging.error(f"Ошибка удаления: {e}")