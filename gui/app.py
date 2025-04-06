import tkinter as tk
from tkinter import ttk
import logging
from concurrent.futures import ThreadPoolExecutor
from .education_tab import create_education_tab
from .vacancies_tab import create_vacancies_tab
from .debug_tab import create_debug_tab
from .assessment_tab import create_assessment_tab
from .assessment_history_tab import create_rating_history_tab
from .graph_tab import create_graph_tab
from moduls.table_processing import sort_treeview_column, sort_competence_type_column

class App:
    def __init__(self, root, logic, batch_size):
        """Инициализация приложения с главным окном и логикой."""
        self.root = root
        self.logic = logic
        self.batch_size = batch_size
        self.last_selected_program_data = None
        self.root.title("Оценка соответствия образовательной программы")
        self.root.geometry("1100x800")
        self.program_id = None
        self.selected_vacancy_id = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
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

        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text="Графики")
        create_graph_tab(self.graph_tab, self)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "ОП":
            from .education_tab import load_education_table
            load_education_table(self)

    def load_initial_data(self):
        self.executor.submit(self.load_programs)
        self.executor.submit(self.load_vacancies)

    def load_programs(self):
        try:
            programs = self.logic.db.fetch_educational_programs()
            logging.info(f"Загружено {len(programs)} программ")
        except Exception as e:
            logging.error(f"Ошибка загрузки программ: {e}")
            self.show_error(f"Не удалось загрузить программы: {e}")

    def load_vacancies(self):
        try:
            vacancies = self.logic.db.fetch_vacancies()
            logging.info(f"Загружено {len(vacancies)} вакансий")
        except Exception as e:
            logging.error(f"Ошибка загрузки вакансий: {e}")
            self.show_error(f"Не удалось загрузить вакансии: {e}")

    def update_status(self, status_text):
        """Обновление текста статуса в status_label в главном потоке."""
        def set_status():
            if hasattr(self, 'status_label'):
                self.status_label.config(text=status_text)
            self.root.update_idletasks()  # Обновляем GUI немедленно
        self.root.after(0, set_status)  # Выполняем в главном потоке

    def start_analysis(self):
        """Запуск анализа соответствия программы и вакансии с учетом весов."""
        if not self.program_id or not self.selected_vacancy_id:
            self.show_error("Выберите образовательную программу и вакансию перед запуском анализа!")
            return

        try:
            threshold_str = self.threshold_entry.get()
            threshold = float(threshold_str) if threshold_str.strip() else 0.5
            if not (0 <= threshold <= 1):
                self.show_error("Пороговое значение должно быть от 0 до 1!")
                return

            use_weights = self.use_weights_var.get()
            weights = None
            if use_weights:
                weights = {
                    "Универсальная компетенция": float(self.uni_weight_entry.get() or "0.2"),
                    "Общепрофессиональная компетенция": float(self.gen_weight_entry.get() or "0.4"),
                    "Профессиональная компетенция": float(self.prof_weight_entry.get() or "0.4")
                }
                total_weight = sum(weights.values())
                if not abs(total_weight - 1.0) < 1e-6:
                    self.show_error(f"Сумма весов должна равняться 1, текущая сумма: {total_weight:.2f}")
                    return
                for key, val in weights.items():
                    if not (0 <= val <= 1):
                        self.show_error(f"Вес для {key} должен быть от 0 до 1!")
                        return

            logging.debug(f"Запуск анализа с порогом: {threshold}, использование весов: {use_weights}, веса: {weights}")
            self.show_info("Запуск анализа...")
            self.update_status("Классификация предложений")  # Начало анализа
            future = self.executor.submit(self.logic.run_analysis, self.program_id, self.selected_vacancy_id, self, self.batch_size, threshold, use_weights, weights)
            future.add_done_callback(self.on_analysis_complete)
        except ValueError:
            self.show_error("Введите корректные числовые значения для порога и весов (от 0 до 1)!")
        except Exception as e:
            logging.error(f"Ошибка при запуске анализа: {e}", exc_info=True)
            self.show_error(f"Ошибка при запуске анализа: {e}")

    def on_analysis_complete(self, future):
        try:
            results = future.result()
            if not results or "similarity_results" not in results:
                self.show_error("Анализ не выполнен: данные недоступны")
                self.update_status("Не запущен")  # Сброс статуса при ошибке
                return
            self.update_results(results)
            self.update_status("Анализ завершен")  # Успешное завершение
        except Exception as e:
            logging.error(f"Ошибка анализа: {e}", exc_info=True)
            self.show_error(f"Ошибка: {e}")
            self.update_status("Не запущен")  # Сброс статуса при ошибке

    def show_error(self, message):
        logging.error(f"GUI Error: {message}")
        # self.root.after(0, lambda: tk.messagebox.showerror("Ошибка", message))

    def show_info(self, message):
        logging.info(f"GUI Info: {message}")
        # self.root.after(0, lambda: tk.messagebox.showinfo("Информация", message))

    def update_results(self, results):
        try:
            self.skill_results_table.delete(*self.skill_results_table.get_children())
            self.group_scores_area.delete(1.0, tk.END)

            for skill, (score, ctype) in results["similarity_results"].items():
                self.skill_results_table.insert("", tk.END, values=(skill, ctype, f"{score:.6f}"))

            use_weights = self.use_weights_var.get()
            weights = None
            if use_weights:
                weights = {
                    "Универсальная компетенция": float(self.uni_weight_entry.get() or "0.2"),
                    "Общепрофессиональная компетенция": float(self.gen_weight_entry.get() or "0.4"),
                    "Профессиональная компетенция": float(self.prof_weight_entry.get() or "0.4")
                }
                total_weight = sum(weights.values())
                if not abs(total_weight - 1.0) < 1e-6:
                    self.show_error(f"Сумма весов должна равняться 1, текущая сумма: {total_weight:.2f}")
                    return
                for key, val in weights.items():
                    if not (0 <= val <= 1):
                        self.show_error(f"Вес для {key} должен быть от 0 до 1!")
                        return
            overall_score, weighted_group_scores = self.logic.calculate_overall_score(results["group_scores"], use_weights, weights)
            sort_competence_type_column(self.skill_results_table, "competence_type")

            self.group_scores_area.insert(tk.END, "Оценки групп компетенций:\n")
            for ctype, score in (weighted_group_scores if use_weights else results["group_scores"]).items():
                self.group_scores_area.insert(tk.END, f"{ctype}: {score:.6f}\n")
            self.group_scores_area.insert(tk.END, f"\nОбщая оценка программы: {overall_score:.6f}\n")
        except ValueError:
            self.show_error("Введите корректные числовые значения для весов (от 0 до 1)!")
        except Exception as e:
            logging.error(f"Ошибка обновления результатов: {e}", exc_info=True)
            self.show_error(f"Ошибка обновления: {e}")

    def update_classification_table(self, classified_sentences):
        try:
            self.classification_table.delete(*self.classification_table.get_children())
            category_mapping = {0: "Требования", 1: "О компании/условия"}
            for sentence, label in classified_sentences:
                self.classification_table.insert("", tk.END, values=(sentence, category_mapping.get(label, "Неизвестно")))
        except Exception as e:
            logging.error(f"Ошибка обновления классификации: {e}", exc_info=True)
            self.show_error(f"Ошибка классификации: {e}")