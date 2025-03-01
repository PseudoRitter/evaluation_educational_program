import tkinter as tk
from tkinter import ttk
from .education_tab import create_education_tab, load_education_table, preview_competences, on_table_select, _get_program_id_from_table
from .vacancies_tab import create_vacancies_tab
from .debug_tab import create_debug_tab
from .assessment_tab import create_assessment_tab
from .add_program_window import create_add_program_window
from .rating_history_tab import create_rating_history_tab  # Новый импорт
from concurrent.futures import ThreadPoolExecutor
import logging
import re
import torch
from tkinter import filedialog, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor

class App:
    def __init__(self, root, logic):
        self.root = root
        self.logic = logic
        self.root.title("Оценка соответствия образовательной программы")
        self.root.geometry("1100x800")
        self.program_id = None
        self.selected_vacancy_id = None  # Явно устанавливаем None
        self.create_widgets()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.load_programs()
        self.load_vacancies()

    def create_widgets(self):
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        # Вкладка "ОП"
        self.education_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.education_tab, text="ОП")
        from .education_tab import create_education_tab, on_table_select, load_education_table, preview_competences
        create_education_tab(self.education_tab, self)
        # Привязываем кнопку "Выбрать" к методу on_table_select из education_tab
        self.select_button = tk.Button(self.education_tab, text="Выбрать", command=lambda: on_table_select(self))
        self.select_button.pack(pady=5)
        # Привязываем событие переключения вкладок
        self.notebook.bind("<<NotebookTabChanged>>", lambda event: load_education_table(self) if self.notebook.tab(self.notebook.select())['text'] == "ОП" else None)
        # Обработчик события для обновления таблицы компетенций
        self.root.bind("<<UpdateCompetences>>", lambda event: preview_competences(self) if self.notebook.tab(self.notebook.select())['text'] == "ОП" else None)

        # Вкладка "Вакансии"
        self.vacancies_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.vacancies_tab, text="Вакансии")
        create_vacancies_tab(self.vacancies_tab, self)

        # Вкладка "Отладка"
        self.debug_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.debug_tab, text="Отладка")
        create_debug_tab(self.debug_tab, self)

        # Вкладка "Оценки"
        self.assessment_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.assessment_tab, text="Оценки")
        create_assessment_tab(self.assessment_tab, self)

        # Вкладка "История оценок"
        self.rating_history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.rating_history_tab, text="История оценок")
        create_rating_history_tab(self.rating_history_tab, self)
        
    def _restore_competence_table(self):
        """Восстановление таблицы компетенций, если она недоступна."""
        if not hasattr(self, 'competence_table') or not self.competence_table.winfo_exists():
            logging.warning("Восстанавливаем таблицу компетенций.")
            from .education_tab import create_education_tab
            create_education_tab(self.education_tab, self)  # Пересоздаём вкладку для восстановления

    def load_programs(self):
        """Загрузка списка образовательных программ из БД (для совместимости, если нужно)."""
        try:
            programs = self.logic.db.fetch_educational_programs()
            program_list = [f"{p[1]} (ID: {p[0]})" for p in programs]  # Формат: "Название (ID)"
            # Здесь можно использовать для других целей, если нужно, но таблица теперь в education_tab
        except Exception as e:
            logging.error(f"Ошибка при загрузке программ из БД: {e}")
            self.show_error(f"Не удалось загрузить программы: {e}")

    def load_vacancies(self):
        """Загрузка списка вакансий из БД."""
        try:
            vacancies = self.logic.db.fetch_vacancies()
            logging.info(f"Загружено {len(vacancies)} вакансий из БД")
            # Удаляем автоматический выбор
            # if vacancies:
            #     self.selected_vacancy_id = vacancies[0][0]
            #     self.selected_vacancy_label.config(text=f"Выбрана вакансия: {vacancies[0][1]} (ID: {vacancies[0][0]})")
        except Exception as e:
            logging.error(f"Ошибка при загрузке вакансий из БД: {e}")
            self.show_error(f"Не удалось загрузить вакансии: {e}")

    def on_program_select(self, event):
        """Обработка выбора программы из выпадающего списка (теперь не используется, но оставляем для совместимости)."""
        pass  # Этот метод больше не нужен, но оставлен для совместимости с текущей логикой

    # def on_vacancy_select(self, event):
    #     """Обработка выбора вакансии из выпадающего списка."""
    #     selected = self.vacancy_var.get()
    #     if selected:
    #         vacancy_id = int(selected.split("ID: ")[1].split(")")[0])  # Извлекаем ID из строки
    #         logging.info(f"Выбрана вакансия с ID: {vacancy_id}")

    def start_analysis(self):
        try:
            if not hasattr(self, 'program_id') or not hasattr(self, 'selected_vacancy_id'):
                self.show_error("Выберите образовательную программу и вакансию!")
                return

            program_id = self.program_id
            vacancy_id = self.selected_vacancy_id
            batch_size = 64

            self.root.update_idletasks()

            future = self.executor.submit(
                self.logic.run_analysis,
                program_id, vacancy_id, self, batch_size
            )
            future.add_done_callback(self.on_analysis_complete)
        except Exception as e:
            logging.error(f"Ошибка в GUI (start_analysis): {e}", exc_info=True)
            self.show_error(f"Произошла ошибка: {e}")

    def on_analysis_complete(self, future):
        try:
            results = future.result()
            if results is None or 'similarity_results' not in results:
                logging.error("Результаты анализа отсутствуют или некорректны")
                self.show_error("Не удалось выполнить анализ: данные вакансии недоступны")
                return
            self.update_results(results)
            self.update_classification_table(results["classification_results"])
        except Exception as e:
            logging.error(f"Ошибка в GUI (on_analysis_complete): {e}", exc_info=True)
            self.show_error(f"Ошибка во время выполнения анализа: {e}")
        finally:
            if hasattr(self.logic, 'device') and self.logic.device == "cuda":
                torch.cuda.empty_cache()

    def show_error(self, message):
        logging.error(f"GUI Error: {message}")

    def show_info(self, message):
        logging.info(f"GUI Info: {message}")

    def update_results(self, results):
        try:
            if not results or 'similarity_results' not in results:
                logging.error("Результаты анализа пусты или отсутствует 'similarity_results'")
                self.show_error("Не удалось обновить результаты: данные недоступны")
                return
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
            logging.error(f"Ошибка в GUI (update_results): {e}", exc_info=True)
            self.show_error(f"Ошибка при обновлении результатов: {e}")

    def setup_paste_handler(self, entry_widget):
        # Настройка обработки горячих клавиш для вставки, копирования и вырезания
        entry_widget.bind("<Control-v>", lambda event: self.paste_text(event, entry_widget))
        entry_widget.bind("<Control-c>", lambda event: self.copy_text(event, entry_widget))
        entry_widget.bind("<Control-x>", lambda event: self.cut_text(event, entry_widget))

    def update_classification_table(self, classified_sentences):
        try:
            self.classification_table.delete(*self.classification_table.get_children())
            category_mapping = {
                0: "Требования",
                1: "О компании/условия"
            }
            for sentence, label in classified_sentences:
                category = category_mapping.get(label, "Неизвестно")
                self.classification_table.insert("", tk.END, values=(sentence, category))
        except Exception as e:
            logging.error(f"Ошибка в GUI (update_classification_table): {e}", exc_info=True)
            self.show_error(f"Ошибка при обновлении таблицы классификации: {e}")
            
    @staticmethod
    def validate(possible_new_value):
        if re.match(r'^[0-9a-fA-F]*$', possible_new_value):
            return True
        return False