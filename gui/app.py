import tkinter as tk
from tkinter import ttk
from .education_tab import create_education_tab
from .vacancies_tab import create_vacancies_tab
from .debug_tab import create_debug_tab
from .assessment_tab import create_assessment_tab
from concurrent.futures import ThreadPoolExecutor
import logging
import re
import torch
from tkinter import ttk, filedialog, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor

class App:
    def __init__(self, root, logic):
        self.root = root
        self.logic = logic  # Логика приложения
        self.root.title("Оценка соответствия образовательной программы")
        self.root.geometry("1100x800")  # Увеличиваем размер окна для нового поля
        self.create_widgets()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.load_programs()  # Загружаем список программ из БД при инициализации
        self.load_vacancies()  # Загружаем список вакансий из БД

    def create_widgets(self):
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        # Вкладка "ОП"
        self.education_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.education_tab, text="ОП")
        create_education_tab(self.education_tab, self)

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

    def load_programs(self):
        """Загрузка списка образовательных программ из БД."""
        try:
            programs = self.logic.db.fetch_educational_programs()
            program_list = [f"{p[1]} (ID: {p[0]})" for p in programs]  # Формат: "Название (ID)"
            self.program_combobox['values'] = program_list
            if program_list:
                self.program_combobox.set(program_list[0])  # Устанавливаем значение по умолчанию
        except Exception as e:
            logging.error(f"Ошибка при загрузке программ из БД: {e}")
            self.show_error(f"Не удалось загрузить программы: {e}")

    def load_vacancies(self):
        """Загрузка списка вакансий из БД."""
        try:
            vacancies = self.logic.load_vacancies_from_db()
            vacancy_list = [f"{v[1]} (ID: {v[0]})" for v in vacancies]  # Формат: "Название (ID)"
            self.vacancy_combobox['values'] = vacancy_list
            if vacancy_list:
                self.vacancy_combobox.set(vacancy_list[0])  # Устанавливаем значение по умолчанию
        except Exception as e:
            logging.error(f"Ошибка при загрузке вакансий из БД: {e}")
            self.show_error(f"Не удалось загрузить вакансии: {e}")

    def on_program_select(self, event):
        """Обработка выбора программы из выпадающего списка."""
        selected = self.program_var.get()
        if selected:
            program_id = int(selected.split("ID: ")[1].split(")")[0])  # Извлекаем ID из строки
            logging.info(f"Выбрана программа с ID: {program_id}")

    def on_vacancy_select(self, event):
        """Обработка выбора вакансии из выпадающего списка."""
        selected = self.vacancy_var.get()
        if selected:
            vacancy_id = int(selected.split("ID: ")[1].split(")")[0])  # Извлекаем ID из строки
            logging.info(f"Выбрана вакансия с ID: {vacancy_id}")

    def start_analysis(self):
        try:
            program_selected = self.program_var.get()
            vacancy_selected = self.vacancy_var.get()
            if not program_selected or not vacancy_selected:
                self.show_error("Выберите образовательную программу и вакансию!")
                return

            program_id = int(program_selected.split("ID: ")[1].split(")")[0])  # Извлекаем ID программы
            vacancy_id = int(vacancy_selected.split("ID: ")[1].split(")")[0])  # Извлекаем ID вакансии
            batch_size = 64

            # self.progress_bar.start(10)
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
        # self.progress_bar.stop()
        try:
            results = future.result()
            self.update_results(results)
            self.update_classification_table(results["classification_results"])
        except Exception as e:
            logging.error(f"Ошибка в GUI (on_analysis_complete): {e}", exc_info=True)
            self.show_error(f"Ошибка во время выполнения анализа: {e}")
        finally:
            if hasattr(self.logic, 'device') and self.logic.device == "cuda":
                torch.cuda.empty_cache()

    def show_error(self, message):
        messagebox.showerror("Ошибка", message)
        logging.error(f"GUI Error: {message}")

    def show_info(self, message):
        self.result_text_area.insert(tk.END, message + "\n")
        logging.info(f"GUI Info: {message}")

    def update_results(self, results):
        try:
            self.result_text_area.delete(1.0, tk.END)
            self.skill_results_table.delete(*self.skill_results_table.get_children())
            self.group_scores_area.delete(1.0, tk.END)

            # Вывод результатов оценки компетенций в таблицу
            for skill, (score, ctype) in results["similarity_results"].items():
                self.skill_results_table.insert("", tk.END, values=(skill, ctype, f"{score:.6f}"))

            # Вывод оценок групп компетенций и общей оценки
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
            
    def validate(possible_new_value):
        if re.match(r'^[0-9a-fA-F]*$', possible_new_value):
            return True
        return False

    def export_to_txt(self):
        try:
            # Открываем диалоговое окно для выбора пути сохранения файла
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if not file_path:
                return  # Если пользователь отменил выбор файла

            # Собираем данные из таблицы
            data = []
            for item in self.classification_table.get_children():
                values = self.classification_table.item(item, "values")
                
                # Проверяем количество значений и дополняем недостающие
                if len(values) == 2:  # Если нет значения "score"
                    sentence, category = values
                    score = ""  # Устанавливаем пустую строку для "score"
                elif len(values) == 3:
                    sentence, category, score = values
                else:
                    logging.warning(f"Неправильное количество значений в строке: {values}")
                    continue  # Пропускаем некорректные строки

                # Формируем строку для записи в файл
                data.append(f"Предложение: {sentence}\nКатегория: {category}\nОценка: {score}\n\n")

            # Сохраняем данные в выбранный файл
            with open(file_path, "w", encoding="utf-8") as file:
                file.writelines(data)

            self.show_info(f"Данные успешно экспортированы в файл: {file_path}")
        except Exception as e:
            logging.error(f"Ошибка при экспорте в TXT: {e}", exc_info=True)
            self.show_error(f"Ошибка при экспорте в TXT: {e}")