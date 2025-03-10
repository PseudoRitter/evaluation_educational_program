import torch
import re
import numpy as np
import gc
import logging
import os
import json
from moduls.database import Database
from moduls.export_to_excel import ExcelExporter
from moduls.skill_matcher import SkillMatcher
from moduls.text_preprocessor import TextPreprocessor
from concurrent.futures import ThreadPoolExecutor

BATCH_SIZE = 64

class Logic:
    def __init__(self):
        self.results = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.db_params = {
            "database": "postgres",
            "user": "postgres",
            "password": "1111",
            "host": "localhost",
            "port": "5432"
        }
        self.db = Database(self.db_params, data_dir="vacancies_hh")
        self.preprocessor = TextPreprocessor()
        self.matcher = SkillMatcher(device=self.device)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def load_vacancies_from_db(self):
        try:
            vacancies = self.db.fetch_vacancies()
            return [(vacancy[0], vacancy[1]) for vacancy in vacancies]
        except Exception as e:
            logging.error(f"Ошибка загрузки вакансий: {e}")
            return []

    def load_program_from_db(self, program_id):
        try:
            program_details = self.db.fetch_program_details(program_id)
            if not program_details:
                return None, "", []
            name = program_details[0][0]
            description = program_details[0][1]
            skills = [row[5] for row in program_details if row[5]]
            competence_ids = [row[4] for row in program_details if row[5]]
            competence_types = self.get_competence_types(competence_ids)
            return name, description, list(zip(skills, competence_types))
        except Exception as e:
            logging.error(f"Ошибка загрузки программы: {e}")
            return None, "", []

    def get_competence_types(self, competence_ids):
        try:
            if not competence_ids:
                return []
            query = """
                SELECT c.competence_id, tc.type_competence_full_name
                FROM competence c
                JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                WHERE c.competence_id IN %s;
            """
            conn = self.db.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, (tuple(competence_ids),))
                types = dict(cursor.fetchall())
            self.db.release_connection(conn)
            return [types.get(cid, "Неизвестно") for cid in competence_ids]
        except Exception as e:
            logging.error(f"Ошибка получения типов компетенций: {e}")
            return ["Неизвестно"] * len(competence_ids)

    def calculate_competence_group_scores(self, skills_with_types, similarity_scores):
        group_scores = {}
        for (skill, ctype), score in zip(skills_with_types, similarity_scores):
            group_scores.setdefault(ctype, []).append(score)
        return {ctype: np.mean(scores) if scores else 0.0 for ctype, scores in group_scores.items()}

    def calculate_overall_score(self, similarity_scores):
        return np.mean(list(similarity_scores.values())) if similarity_scores else 0.0

    def load_vacancy_descriptions_field(self, full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as file:
                vacancies = json.load(file)
                return [vacancy.get("full_description", "") for vacancy in vacancies]
        except Exception as e:
            logging.error(f"Ошибка загрузки описаний из {full_path}: {e}")
            return []

    def run_analysis(self, program_id, vacancy_id, gui, BATCH_SIZE):
        try:
            vacancy = self.db.fetch_vacancy_details(vacancy_id)
            if not vacancy:
                gui.show_error("Вакансия не найдена в базе данных!")
                logging.error("Вакансия не найдена в базе данных.")
                return {}
            self.vacancy_file = vacancy[3] 

            full_path = os.path.join(self.db.data_dir, self.vacancy_file)  
            if not os.path.exists(full_path):
                gui.show_error(f"Файл с вакансиями не найден: {full_path}")
                logging.error(f"Файл с вакансиями не найден: {full_path}")
                return {}
            
            logging.debug(f"Загружаем файл: {full_path}")
            job_descriptions = self.load_vacancy_descriptions_field(full_path)  
            logging.debug(f"Загружено описаний: {len(job_descriptions)}")
            if not job_descriptions:
                gui.show_error(f"Файл {full_path} не содержит описаний вакансий!")
                logging.error(f"Файл {full_path} не содержит описаний вакансий!")
                return {}

            title, description, skills_with_types = self.load_program_from_db(program_id)
            if not title or not description or not skills_with_types:
                gui.show_error("Образовательная программа не найдена в базе данных!")
                logging.error("Образовательная программа не найдена в базе данных.")
                return {}
            
            skills = [skill for skill, _ in skills_with_types]  
            competence_types = [ctype for _, ctype in skills_with_types]  

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
                filtered_texts.split("\n"), BATCH_SIZE=BATCH_SIZE, exclude_category_label=1
            )
            logging.debug(f"Классифицировано предложений: {len(classified_results)}")
            gui.update_classification_table(classified_results)
            filtered_texts = "\n".join(filtered_sentences)

            if device == "cuda":
                logging.info("Кэш GPU очищен после классификации.")
                gc.collect() 
                torch.cuda.empty_cache()  
        
            gui.show_info("Шаг 2: Оценка соответствия компетенций...")
            matcher = SkillMatcher(device=device)
            results = matcher.match_skills(skills, filtered_texts.split("\n"), BATCH_SIZE)
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
            if hasattr(self, "device") and self.device == "cuda":
                logging.info("Очистка кэша GPU после завершения анализа...")
                if "matcher" in locals() and hasattr(matcher, "model"):
                    matcher.model.to("cpu")  
                del preprocessor  
                gc.collect()       
                torch.cuda.empty_cache()  

    def export_results_to_excel(self, app):
        """Экспорт результатов анализа в Excel."""
        from tkinter import messagebox
        if not self.results:
            messagebox.showerror("Ошибка", "Нет данных для экспорта!")
            return

        selected_program = app.selected_program_label.cget("text").replace("Выбрана программа: ", "")
        selected_vacancy = app.selected_vacancy_label.cget("text").replace("Выбрана вакансия: ", "")
        
        exporter = ExcelExporter(self.results, program_name=selected_program, vacancy_name=selected_vacancy)
        exporter.export_to_excel()

    def validate(self, possible_new_value):
        """Проверка ввода на соответствие шестнадцатеричному формату."""
        return bool(re.match(r"^[0-9a-fA-F]*$", possible_new_value))