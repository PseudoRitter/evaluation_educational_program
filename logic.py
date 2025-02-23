import torch.multiprocessing as mp
import torch
import re
import pandas as pd
import numpy as np
import gc
import logging
from moduls.export_to_excel import ExcelExporter
from moduls.vacancy_loader import VacancyLoader
from moduls.skill_matcher import SkillMatcher
from moduls.text_preprocessor import TextPreprocessor
from tkinter import filedialog, messagebox
import traceback

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class Logic:
    def __init__(self):
        self.filename = None
        self.results = None
        self.preprocessor = None
        self.matcher = None
        self.device = "cpu"

    def load_file(self):
        try:
            self.filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if self.filename:
                logging.info(f"Файл успешно выбран: {self.filename}")
                return self.filename
            else:
                logging.warning("Файл не выбран.")
                return None
        except Exception as e:
            logging.error(f"Ошибка при выборе файла: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось выбрать файл: {e}")
            return None

    def run_analysis(self, title, description, skills, gui, batch_size=64):
        try:
            if not self.filename:
                gui.show_error("Файл с вакансиями не выбран!")
                logging.error("Файл с вакансиями не выбран.")
                return {}

            loader = VacancyLoader(self.filename)
            job_descriptions = loader.load_vacancy_descriptions_field()

            preprocessor = TextPreprocessor()
            device = preprocessor.device
            logging.info(f"Используется устройство: {device}")

            original_texts = "\n".join(job_descriptions)
            tokenized_texts = []
            filtered_texts = []

            for desc in job_descriptions:
                clean_html_text = preprocessor.remove_html_tags(desc)
                clean_list_text = preprocessor.remove_list_tags(clean_html_text)  # Исправлено имя метода
                if clean_list_text is None:  # Проверка на None
                    clean_list_text = ""
                normalize_spaces_text = preprocessor.normalize_spaces(clean_list_text)
                sentences = preprocessor.segment_text(normalize_spaces_text)
                clean_short_sentences = preprocessor.filter_short_sentences(sentences)
                tokenized_texts.append("\n".join(clean_short_sentences))
                filtered_sentences = preprocessor.filter_sentences(sentences)
                filtered_texts.append("\n".join(filtered_sentences))

            tokenized_texts = "\n".join(tokenized_texts)
            filtered_texts = "\n".join(filtered_texts)

            gui.show_info("Шаг 1: Классификация и фильтрация предложений...")
            classified_results, filtered_sentences = preprocessor.classify_sentences(
                filtered_texts.split('\n'), batch_size=batch_size, exclude_category_label=1
            )
            gui.update_classification_table(classified_results)
            filtered_texts = "\n".join(filtered_sentences)

            if device == "cuda":
                logging.info("Кэш GPU очищен после классификации.")
                gc.collect()
                torch.cuda.empty_cache()

            gui.show_info("Шаг 2: Оценка соответствия компетенций...")
            matcher = SkillMatcher(device=device)
            results = matcher.match_skills(skills, filtered_texts.split('\n'), batch_size=64)
            self.results = results["sentence_transformer"]

            return {
                "original_texts": original_texts,
                "tokenized_texts": tokenized_texts,
                "filtered_texts": filtered_texts,
                "similarity_results": self.results,
                "classification_results": classified_results
            }
        except Exception as e:
            logging.error(f"Ошибка в Logic (run_analysis): {e}", exc_info=True)
            gui.show_error(f"Произошла ошибка: {e}")
            return {}
        finally:
            if hasattr(self, 'device') and self.device == "cuda":
                logging.info("Очистка кэша GPU после завершения анализа...")
                if 'matcher' in locals() and hasattr(matcher, 'model'):
                    matcher.model.to("cpu")
                del preprocessor
                gc.collect()
                torch.cuda.empty_cache()

    def export_results_to_excel(self):
        if not self.results:
            messagebox.showerror("Ошибка", "Нет данных для экспорта! Сначала запустите анализ.")
            return

        exporter = ExcelExporter(self.results)
        result_message = exporter.export_to_excel()
        # if result_message.startswith("Данные успешно экспортированы"):
        #     messagebox.showinfo("Успех", result_message)
        # else:
        #     messagebox.showwarning("Предупреждение", result_message)

    @staticmethod
    def validate(possible_new_value):
        if re.match(r'^[0-9a-fA-F]*$', possible_new_value):
            return True
        return False