import tkinter as tk
import re
import torch
import logging
from tkinter import ttk, filedialog, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor

class App:
    def __init__(self, root, logic):
        self.root = root
        self.logic = logic  # Логика приложения
        self.root.title("Оценка соответствия образовательной программы")
        self.root.geometry("1100x1000")  # Увеличиваем размер окна для нового поля
        self.create_widgets()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def create_widgets(self):
        # Поля для ввода данных
        self.title_label = tk.Label(self.root, text="Название программы:")
        self.title_label.pack()
        self.title_entry = tk.Entry(self.root, width=50)
        self.title_entry.pack()
        self.setup_paste_handler(self.title_entry)

        self.description_label = tk.Label(self.root, text="Описание программы:")
        self.description_label.pack()
        self.description_entry = tk.Entry(self.root, width=50)
        self.description_entry.pack()
        self.setup_paste_handler(self.title_entry)

        self.skills_label = tk.Label(self.root, text="Навыки программы (через запятую):")
        self.skills_label.pack()
        self.skills_entry = tk.Entry(self.root, width=50)
        self.skills_entry.pack()
        self.setup_paste_handler(self.title_entry)

        # Кнопка для выбора файла с вакансиями
        self.file_label = tk.Label(self.root, text="Файл с вакансиями:")
        self.file_label.pack()
        self.file_button = tk.Button(self.root, text="Выбрать файл", command=self.logic.load_file)
        self.file_button.pack()

        # Кнопка для запуска анализа
        self.run_button = tk.Button(self.root, text="Запустить анализ", command=self.start_analysis)
        self.run_button.pack()

        # # Кнопка для экспорта результатов в Excel
        self.export_button = tk.Button(self.root, text="Экспорт в Excel", command=self.logic.export_results_to_excel)
        self.export_button.pack()

        # Прогресс-бар
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        self.progress_bar.pack(pady=10)

        # Поле для вывода исходного текста вакансии
        self.original_text_label = tk.Label(self.root, text="Исходный текст вакансии:")
        self.original_text_label.pack()
        self.original_text_area = scrolledtext.ScrolledText(self.root, width=120, height=5)
        self.original_text_area.pack()

        # Поле для вывода текста, разделенного на токены
        self.tokenized_text_label = tk.Label(self.root, text="Текст, разделенный на токены:")
        self.tokenized_text_label.pack()
        self.tokenized_text_area = scrolledtext.ScrolledText(self.root, width=120, height=5)
        self.tokenized_text_area.pack()

        # Таблица для вывода результатов классификации
        self.classification_table_label = tk.Label(self.root, text="Результаты классификации:")
        self.classification_table_label.pack()

        self.classification_table = ttk.Treeview(self.root, columns=("sentence", "category", "score"), show="headings")
        self.classification_table.heading("sentence", text="Предложение")
        self.classification_table.heading("category", text="Категория")
        self.classification_table.heading("score", text="Оценка")
        self.classification_table.column("sentence", width=800)
        self.classification_table.column("category", width=150)
        self.classification_table.column("score", width=100)
        self.classification_table.pack()

        # Кнопка для экспорта результатов в TXT
        self.export_txt_button = tk.Button(self.root, text="Экспорт в TXT", command=self.export_to_txt)
        self.export_txt_button.pack(pady=10)

        # Поле для вывода текста после удаления стоп-слов и стоп-фраз
        self.filtered_text_label = tk.Label(self.root, text="Текст после удаления стоп-слов и стоп-фраз:")
        self.filtered_text_label.pack()
        self.filtered_text_area = scrolledtext.ScrolledText(self.root, width=120, height=5)
        self.filtered_text_area.pack()

        # Поле для вывода результатов анализа
        self.result_text_label = tk.Label(self.root, text="Результаты анализа:")
        self.result_text_label.pack()
        self.result_text_area = scrolledtext.ScrolledText(self.root, width=120, height=5)
        self.result_text_area.pack()

    def start_analysis(self):
        try:
            title = self.title_entry.get()
            description = self.description_entry.get()
            skills = self.skills_entry.get().split(";")
            batch_size = 64

            if not title or not description or not skills:
                self.show_error("Заполните все поля перед запуском анализа!")
                return

            self.progress_bar.start(10)
            self.root.update_idletasks()

            future = self.executor.submit(
                self.logic.run_analysis,
                title, description, skills, self, batch_size
            )
            future.add_done_callback(self.on_analysis_complete)
        except Exception as e:
            logging.error(f"Ошибка в GUI (start_analysis): {e}", exc_info=True)
            self.show_error(f"Произошла ошибка: {e}")

    def on_analysis_complete(self, future):
        self.progress_bar.stop()
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
            self.original_text_area.delete(1.0, tk.END)
            self.tokenized_text_area.delete(1.0, tk.END)
            self.filtered_text_area.delete(1.0, tk.END)
            self.result_text_area.delete(1.0, tk.END)

            self.original_text_area.insert(tk.END, results["original_texts"])
            self.tokenized_text_area.insert(tk.END, results["tokenized_texts"])
            self.filtered_text_area.insert(tk.END, results["filtered_texts"])

            self.result_text_area.insert(tk.END, "Средние значения схожести для каждого навыка (SentenceTransformer):\n")
            for skill, avg_similarity in results["similarity_results"].items():
                self.result_text_area.insert(tk.END, f"Навык: {skill} - Средняя схожесть: {avg_similarity:.6f}\n")
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

