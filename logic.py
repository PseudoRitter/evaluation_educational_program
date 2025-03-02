from moduls.database import Database
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
import os

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class Logic:
    def __init__(self):
        self.results = None
        self.preprocessor = None
        self.matcher = None
        self.device = "cpu"
        self.vacancy_file = None  # Добавляем атрибут для хранения имени файла
        # Параметры подключения к БД
        self.db_params = {
            "database": "postgres",
            "user": "postgres",
            "password": "1111",
            "host": "localhost",
            "port": "5432"
        }
        self.db = Database(self.db_params, data_dir="vacancies_hh")

    def load_vacancies_from_db(self):
        """Получение списка вакансий из БД для отображения в интерфейсе."""
        try:
            vacancies = self.db.fetch_vacancies()
            vacancy_list = [(vacancy[0], vacancy[1]) for vacancy in vacancies]  # (vacancy_id, vacancy_name)
            logging.info(f"Загружено {len(vacancy_list)} вакансий из БД")
            return vacancy_list
        except Exception as e:
            logging.error(f"Ошибка при загрузке списка вакансий из БД: {e}")
            return []

    def load_program_from_db(self, program_id):
        """Загрузка данных образовательной программы из БД."""
        try:
            program_details = self.db.fetch_program_details(program_id)
            if not program_details:
                return None, "", []

            name = program_details[0][0]  # educational_program_name
            description = program_details[0][1]  # educational_program_code (можно использовать как описание или дополнить)
            skills = [row[5] for row in program_details if row[5]]  # competence_name как навыки
            competence_ids = [row[4] for row in program_details if row[5]]  # competence_id для получения типов
            competence_types = self.get_competence_types(competence_ids)  # Получаем типы компетенций
            return name, description, list(zip(skills, competence_types))
        except Exception as e:
            logging.error(f"Ошибка при загрузке программы из БД: {e}")
            return None, "", []

    def get_competence_types(self, competence_ids):
        """Получение типов компетенций по их ID из БД."""
        try:
            if not competence_ids:
                return []
            query = """
                SELECT c.competence_id, tc.type_competence_full_name
                FROM competence c
                JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                WHERE c.competence_id IN %s;
            """
            self.db.cursor.execute(query, (tuple(competence_ids),))
            types = {row[0]: row[1] for row in self.db.cursor.fetchall()}
            return [types.get(cid, "Неизвестно") for cid in competence_ids]
        except Exception as e:
            logging.error(f"Ошибка при получении типов компетенций: {e}")
            return ["Неизвестно"] * len(competence_ids)

    def calculate_competence_group_scores(self, skills_with_types, similarity_scores):
        """Расчёт средней оценки для каждой группы компетенций."""
        group_scores = {}
        for (skill, ctype), score in zip(skills_with_types, similarity_scores):
            if ctype not in group_scores:
                group_scores[ctype] = []
            group_scores[ctype].append(score)
        
        # Вычисляем средние значения для каждой группы
        return {ctype: np.mean(scores) if scores else 0.0 for ctype, scores in group_scores.items()}

    def calculate_overall_score(self, similarity_scores):
        """Расчёт общей средней оценки программы."""
        if not similarity_scores:
            return 0.0
        return np.mean(list(similarity_scores.values()))

    def run_analysis(self, program_id, vacancy_id, gui, batch_size=64):
        try:
            # Устанавливаем имя файла из БД (эквивалент load_vacancy_description)
            vacancy = self.db.fetch_vacancy_details(vacancy_id)
            if not vacancy:
                gui.show_error("Вакансия не найдена в базе данных!")
                logging.error("Вакансия не найдена в базе данных.")
                return {}
            self.vacancy_file = vacancy[3]  # vacancy_file содержит "разработчик.json"

            # Формируем полный путь к файлу
            full_path = os.path.join(self.db.data_dir, self.vacancy_file)  # Например, "vacancies_hh/разработчик.json"
            if not os.path.exists(full_path):
                gui.show_error(f"Файл с вакансиями не найден: {full_path}")
                logging.error(f"Файл с вакансиями не найден: {full_path}")
                return {}
            
            logging.debug(f"Загружаем файл: {full_path}")
            loader = VacancyLoader(full_path)  # Передаем полный путь
            job_descriptions = loader.load_vacancy_descriptions_field()
            logging.debug(f"Загружено описаний: {len(job_descriptions)}")
            if not job_descriptions:
                gui.show_error(f"Файл {full_path} не содержит описаний вакансий!")
                logging.error(f"Файл {full_path} не содержит описаний вакансий!")
                return {}

            # Загружаем данные программы из БД
            title, description, skills_with_types = self.load_program_from_db(program_id)
            if not title or not description or not skills_with_types:
                gui.show_error("Образовательная программа не найдена в базе данных!")
                logging.error("Образовательная программа не найдена в базе данных.")
                return {}
            
            skills = [skill for skill, _ in skills_with_types]  # Извлекаем только названия компетенций для анализа
            competence_types = [ctype for _, ctype in skills_with_types]  # Извлекаем типы компетенций

            preprocessor = TextPreprocessor()
            device = preprocessor.device  
            logging.info(f"Используется устройство: {device}")

            original_texts = "\n".join(job_descriptions)
            tokenized_texts = []
            filtered_texts = []

            for desc in job_descriptions:
                clean_html_text = preprocessor.remove_html_tags(desc)
                clean_list_text = preprocessor.remove_list_tags(clean_html_text)
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
            logging.debug(f"Классифицировано предложений: {len(classified_results)}")
            gui.update_classification_table(classified_results)
            filtered_texts = "\n".join(filtered_sentences)

            if device == "cuda":
                logging.info("Кэш GPU очищен после классификации.")
                gc.collect()  # Вызываем сборщик мусора
                torch.cuda.empty_cache()  # Очищаем кэш GPU
        
            gui.show_info("Шаг 2: Оценка соответствия компетенций...")
            matcher = SkillMatcher(device=device)
            results = matcher.match_skills(skills, filtered_texts.split('\n'), batch_size=64)
            #logging.debug(f"Результаты match_skills: {results}")
            if isinstance(results["sentence_transformer"], (int, float)):
                similarity_results = {skill: (results["sentence_transformer"], ctype) for skill, ctype in zip(skills, competence_types)}
            else:
                similarity_results = {
                    skill: (score, ctype) for skill, score, ctype in zip(skills, results["sentence_transformer"].values(), competence_types)
                }
            group_scores = self.calculate_competence_group_scores(skills_with_types, results["sentence_transformer"].values() if not isinstance(results["sentence_transformer"], (int, float)) else [results["sentence_transformer"]] * len(skills))
            overall_score = self.calculate_overall_score(results["sentence_transformer"])

            self.results = {
                "similarity_results": similarity_results,
                "group_scores": group_scores,
                "overall_score": overall_score,
                "original_texts": original_texts,
                "tokenized_texts": tokenized_texts,
                "filtered_texts": filtered_texts,
                "classification_results": classified_results
            }

            #logging.debug(f"Итоговые результаты: {self.results}")
            return self.results

        except Exception as e:
            logging.error(f"Ошибка в Logic (run_analysis): {e}", exc_info=True)
            gui.show_error(f"Произошла ошибка: {e}")
            return {}
        finally:
            # Очистка кэша GPU после завершения анализа
            if hasattr(self, 'device') and self.device == "cuda":
                logging.info("Очистка кэша GPU после завершения анализа...")
                if 'matcher' in locals() and hasattr(matcher, 'model'):
                    matcher.model.to("cpu")  # Перемещаем модель SkillMatcher на CPU
                del preprocessor  # Удаляем объект TextPreprocessor
                gc.collect()       # Вызываем сборщик мусора
                torch.cuda.empty_cache()  # Очищаем кэш GPU

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