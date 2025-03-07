import tkinter as tk
from tkinter import ttk
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from .education_tab import create_education_tab
from .vacancies_tab import create_vacancies_tab
from .debug_tab import create_debug_tab
from .assessment_tab import create_assessment_tab
from .assessment_history_tab import create_rating_history_tab

class App:
    """Основной класс приложения для оценки соответствия образовательных программ."""

    def __init__(self, root, logic):
        """Инициализация приложения с главным окном и логикой."""
        self.root = root
        self.logic = logic
        self.root.title("Оценка соответствия образовательной программы")
        self.root.geometry("1100x800")
        self.program_id = None
        self.selected_vacancy_id = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        """Создание вкладок интерфейса."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        self.education_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.education_tab, text="ОП")
        create_education_tab(self.education_tab, self)

        self.vacancies_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.vacancies_tab, text="Вакансии")
        create_vacancies_tab(self.vacancies_tab, self)

        self.debug_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.debug_tab, text="Отладка")
        create_debug_tab(self.debug_tab, self)

        self.assessment_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.assessment_tab, text="Оценки")
        create_assessment_tab(self.assessment_tab, self)

        self.rating_history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.rating_history_tab, text="История оценок")
        create_rating_history_tab(self.rating_history_tab, self)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """Обработка смены вкладки."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "ОП":
            from .education_tab import load_education_table
            load_education_table(self)

    def load_initial_data(self):
        """Асинхронная загрузка начальных данных."""
        self.executor.submit(self.load_programs)
        self.executor.submit(self.load_vacancies)

    def load_programs(self):
        """Загрузка образовательных программ."""
        try:
            programs = self.logic.db.fetch_educational_programs()
            logging.info(f"Загружено {len(programs)} программ")
        except Exception as e:
            logging.error(f"Ошибка загрузки программ: {e}")
            self.show_error(f"Не удалось загрузить программы: {e}")

    def load_vacancies(self):
        """Загрузка вакансий."""
        try:
            vacancies = self.logic.db.fetch_vacancies()
            logging.info(f"Загружено {len(vacancies)} вакансий")
        except Exception as e:
            logging.error(f"Ошибка загрузки вакансий: {e}")
            self.show_error(f"Не удалось загрузить вакансии: {e}")

    def start_analysis(self):
        """Запуск анализа соответствия."""
        future = self.executor.submit(self.logic.run_analysis, self.program_id, self.selected_vacancy_id, self, 64)
        future.add_done_callback(self.on_analysis_complete)

    def on_analysis_complete(self, future):
        """Обработка завершения анализа."""
        try:
            results = future.result()
            if not results or "similarity_results" not in results:
                self.show_error("Анализ не выполнен: данные недоступны")
                return
            self.update_results(results)
        except Exception as e:
            logging.error(f"Ошибка анализа: {e}", exc_info=True)
            self.show_error(f"Ошибка: {e}")

    def show_error(self, message):
        """Отображение сообщения об ошибке."""
        logging.error(f"GUI Error: {message}")

    def show_info(self, message):
        """Отображение информационного сообщения."""
        logging.info(f"GUI Info: {message}")

    def update_results(self, results):
        """Обновление интерфейса результатами анализа."""
        try:
            self.result_text_area.delete(1.0, tk.END)
            self.skill_results_table.delete(*self.skill_results_table.get_children())
            self.group_scores_area.delete(1.0, tk.END)

            for skill, (score, ctype) in results["similarity_results"].items():
                self.skill_results_table.insert("", tk.END, values=(skill, ctype, f"{score:.6f}"))

            self.group_scores_area.insert(tk.END, "Оценки групп компетенций:\n")
            for ctype, score in results["group_scores"].items():
                self.group_scores_area.insert(tk.END, f"{ctype}: {score:.6f}\n")
            self.group_scores_area.insert(tk.END, f"\nОбщая оценка программы: {results['overall_score']:.6f}\n")
        except Exception as e:
            logging.error(f"Ошибка обновления результатов: {e}", exc_info=True)
            self.show_error(f"Ошибка обновления: {e}")

    def update_classification_table(self, classified_sentences):
        """Обновление таблицы классификации."""
        try:
            self.classification_table.delete(*self.classification_table.get_children())
            category_mapping = {0: "Требования", 1: "О компании/условия"}
            for sentence, label in classified_sentences:
                self.classification_table.insert("", tk.END, values=(sentence, category_mapping.get(label, "Неизвестно")))
        except Exception as e:
            logging.error(f"Ошибка обновления классификации: {e}", exc_info=True)
            self.show_error(f"Ошибка классификации: {e}")

    def validate(self, possible_new_value):
        """Проверка ввода на соответствие шестнадцатеричному формату."""
        return bool(re.match(r"^[0-9a-fA-F]*$", possible_new_value))