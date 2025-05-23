import torch
import re
import numpy as np
import gc
import logging
import os
import json
import tkinter as tk
from tkinter import messagebox
from moduls.database import Database
from moduls.export_to_excel import ExcelExporter
from moduls.skill_matcher import SkillMatcher
from moduls.text_preprocessor import TextPreprocessor
from concurrent.futures import ThreadPoolExecutor

class Logic:
    def __init__(self, batch_size):  
        self.results = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.batch_size = batch_size  
        self.db = Database(db_path="assessment_database.db", data_dir="vacancies_hh")
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
            competence_types = self.db.get_competence_types(competence_ids)
            return name, description, list(zip(skills, competence_types))
        except Exception as e:
            logging.error(f"Ошибка загрузки программы: {e}")
            return None, "", []

    def calculate_competence_group_scores(self, skills_with_types, similarity_scores):
        group_scores = {}
        for (skill, ctype), score in zip(skills_with_types, similarity_scores):
            group_scores.setdefault(ctype, []).append(score)
        return {ctype: np.mean(scores) if scores else 0.0 for ctype, scores in group_scores.items()}

    def calculate_overall_score(self, group_scores, use_weights, weights):
        if not group_scores:
            return 0.0, {}

        if not use_weights:
            return np.mean(list(group_scores.values())) if group_scores else 0.0, group_scores

        weighted_group_scores = {}
        overall_score = 0.0
        for ctype, score in group_scores.items():
            weight = weights.get(ctype, 0.0) 
            weighted_score = score * weight
            weighted_group_scores[ctype] = weighted_score
            overall_score += weighted_score

        return overall_score, weighted_group_scores

    def load_vacancy_descriptions_field(self, full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as file:
                vacancies = json.load(file)
                descriptions = [vacancy.get("full_description", "") for vacancy in vacancies]
                key_skills = [vacancy.get("key_skills", []) for vacancy in vacancies]
                return descriptions, key_skills
        except Exception as e:
            logging.error(f"Ошибка загрузки описаний из {full_path}: {e}")
            return [], []
        
    def calculate_key_skills_frequency(self, key_skills_list):
        from collections import Counter
        
        total_vacancies_with_skills = sum(1 for skills in key_skills_list if skills)
        total_vacancies = len(key_skills_list)
        
        all_key_skills = [skill for sublist in key_skills_list for skill in sublist]
        frequency_counter = Counter(all_key_skills)
        
        key_skills_data = []
        for skill, count in frequency_counter.most_common():
            percentage = (count / total_vacancies_with_skills) if total_vacancies > 0 else 0
            key_skills_data.append((skill, count, percentage))
        
        return total_vacancies_with_skills, key_skills_data

    def run_analysis(self, program_id, vacancy_id, gui, batch_size, threshold=0.7, use_weights=False, weights=None):
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
            job_descriptions, key_skills_list = self.load_vacancy_descriptions_field(full_path)
            logging.debug(f"Загружено описаний: {len(job_descriptions)}, key_skills: {len(key_skills_list)}")
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
                if gui.stop_analysis_flag:
                    logging.info("Анализ принудительно остановлен на этапе предобработки.")
                    return {}
                clean_html_text = preprocessor.remove_html_tags(desc)
                clean_header = preprocessor.remove_header(clean_html_text)
                clean_list_text = preprocessor.remove_list_tags(clean_header)
                normalize_spaces_text = preprocessor.normalize_spaces(clean_list_text)
                sentences = preprocessor.segment_text(normalize_spaces_text)
                clean_short_sentences = preprocessor.filter_short_sentences(sentences)
                tokenized_texts.append("\n".join(clean_short_sentences))
                filtered_sentences = preprocessor.filter_sentences(clean_short_sentences)
                filtered_texts.append("\n".join(filtered_sentences))

            tokenized_texts = "\n".join(tokenized_texts)
            filtered_texts = "\n".join(filtered_texts)

            gui.show_info("Шаг 1: Классификация и фильтрация предложений...")
            gui.update_status("Классификация предложений")
            sentences = filtered_texts.split("\n")
            classified_results, filtered_sentences = preprocessor.classify_sentences(
                sentences, batch_size=self.batch_size, exclude_category_label=1, stop_flag=gui.stop_analysis_flag
            )
            if gui.stop_analysis_flag:
                logging.info("Анализ принудительно остановлен во время классификации.")
                return {}
            
            logging.debug(f"Классифицировано предложений: {len(classified_results)}")
            gui.update_classification_table(classified_results)
            filtered_texts = "\n".join(filtered_sentences)

            if device == "cuda":
                logging.info("Кэш GPU очищен после классификации.")
                gc.collect()
                torch.cuda.empty_cache()

            if gui.stop_analysis_flag:
                logging.info("Анализ принудительно остановлен после классификации.")
                return {}

            gui.show_info("Шаг 2: Оценка соответствия компетенций...")
            gui.update_status("Оценка соответствия предложений")
            results = self.matcher.match_skills(skills, filtered_texts.split("\n"), batch_size, threshold, stop_flag=gui.stop_analysis_flag)
            if gui.stop_analysis_flag:
                logging.info("Анализ принудительно остановлен во время оценки компетенций.")
                return {}
            similarity_results = {
                skill: (score, ctype) for skill, score, ctype in zip(skills, results["sentence_transformer"].values(), competence_types)
            }
            frequencies = results["frequencies"]
            group_scores = self.calculate_competence_group_scores(skills_with_types, results["sentence_transformer"].values())
            overall_score, weighted_group_scores = self.calculate_overall_score(group_scores, use_weights, weights or {
                "Универсальная компетенция": 0.2,
                "Общепрофессиональная компетенция": 0.4,
                "Профессиональная компетенция": 0.4
            })

            if gui.stop_analysis_flag:
                logging.info("Анализ принудительно остановлен перед завершением.")
                return {}

            total_vacancies_with_skills, key_skills_data = self.calculate_key_skills_frequency(key_skills_list)

            self.results = {
                "similarity_results": similarity_results,
                "frequencies": frequencies,
                "group_scores": weighted_group_scores if use_weights else group_scores,
                "overall_score": overall_score,
                "original_texts": original_texts,
                "tokenized_texts": tokenized_texts,
                "filtered_texts": filtered_texts,
                "classification_results": classified_results,
                "total_vacancies_with_skills": total_vacancies_with_skills,
                "key_skills_data": key_skills_data
            }

            return self.results

        except Exception as e:
            logging.error(f"Ошибка в Logic (run_analysis): {e}", exc_info=True)
            gui.show_error(f"Произошла ошибка: {e}")
            return {}
        finally:
            if hasattr(self, "device") and self.device == "cuda":
                logging.info("Очистка кэш GPU после завершения анализа...")
                if hasattr(self.matcher, "model") and self.matcher.model is not None:
                    self.matcher.model.to("cpu")
                del preprocessor
                gc.collect()
                torch.cuda.empty_cache()

    def export_results_to_excel(self, app):
        selected_program = app.selected_program_label.cget("text").replace("Выбрана программа: ", "")
        selected_vacancy = app.selected_vacancy_label.cget("text").replace("Выбрана вакансия: ", "")
        
        exporter = ExcelExporter(self.results, program_name=selected_program, vacancy_name=selected_vacancy)
        exporter.export_to_excel()