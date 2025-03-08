import requests
import json
import time
import logging
from datetime import datetime


class LaborMarketData:
    """Класс для сбора данных о вакансиях с hh.ru."""

    def __init__(self, query: str, access_token: str, max_vacancies_per_experience=2000):
        """Инициализация объекта для сбора вакансий."""
        self.base_url = "https://api.hh.ru/vacancies"
        self.query = query
        self.access_token = access_token
        self.vacancies = []
        self.max_vacancies_per_experience = max_vacancies_per_experience
        self.temp = []
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        self.rate_limit_delay = 1.0  # Задержка для соблюдения лимитов API

    def fetch_page(self, page: int, experience: str):
        """Синхронный запрос страницы вакансий."""
        params = {
            "text": self.query,
            "area": 113, #113 - вся Россия
            "per_page": 100,
            "page": page,
            "experience": experience
        }
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("items", []), data.get("pages", 1)
            elif response.status_code == 429:  # Too Many Requests
                logging.warning(f"Лимит запросов превышен для {experience}, страница {page}. Увеличиваем задержку.")
                self.rate_limit_delay += 1.0
                time.sleep(self.rate_limit_delay)
                return self.fetch_page(page, experience)
            else:
                logging.error(f"Ошибка {response.status_code} при запросе страницы {page} для {experience}")
                return [], 1
        except Exception as e:
            logging.error(f"Ошибка при запросе страницы {page} для {experience}: {e}")
            return [], 1

    def fetch_vacancies_by_experience(self, experience: str):
        """Сбор вакансий для заданного уровня опыта."""
        page = 0
        max_pages = 20
        experience_vacancies = []

        while page < max_pages and len(experience_vacancies) < self.max_vacancies_per_experience:
            items, total_pages = self.fetch_page(page, experience)
            if not items:
                logging.info(f"Нет больше вакансий для {experience}.")
                break
            experience_vacancies.extend(items)
            logging.info(f"Собрано {len(items)} вакансий с страницы {page} для {experience}")
            page += 1
            max_pages = min(max_pages, total_pages)
            if page >= total_pages:
                logging.info(f"Все страницы собраны для {experience}.")
                break
            time.sleep(self.rate_limit_delay)

        return experience_vacancies[:self.max_vacancies_per_experience]

    def fetch_full_vacancy_data(self, vacancy_id: str):
        """Синхронный запрос полной информации о вакансии."""
        url = f"{self.base_url}/{vacancy_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logging.warning(f"Вакансия {vacancy_id} не найдена.")
                return None
            elif response.status_code == 429:
                logging.warning(f"Лимит запросов для {vacancy_id}. Увеличиваем задержку.")
                self.rate_limit_delay += 1.0
                time.sleep(self.rate_limit_delay)
                return self.fetch_full_vacancy_data(vacancy_id)
            else:
                logging.error(f"Ошибка {response.status_code} для вакансии {vacancy_id}")
                return None
        except Exception as e:
            logging.error(f"Ошибка при запросе вакансии {vacancy_id}: {e}")
            return None

    def collect_all_vacancies(self):
        """Синхронный сбор всех вакансий по уровням опыта."""
        #experience_levels = ["noExperience", "between1And3", "between3And6", "moreThan6"]
        experience_levels = ["noExperience", "between1And3"]
        for exp in experience_levels:
            vacancies = self.fetch_vacancies_by_experience(exp)
            self.vacancies.extend(vacancies)
        logging.info(f"Собрано всего {len(self.vacancies)} вакансий")

    def process_vacancy(self, vacancy, index, total):
        """Обработка одной вакансии с сохранением полной информации."""
        full_data = self.fetch_full_vacancy_data(vacancy["id"])
        if full_data:
            processed_vacancy = {
                "id": vacancy["id"],
                "name": vacancy.get("name", "No name"),
                "employer": vacancy.get("employer", {}).get("name", "No employer"),
                "area": vacancy.get("area", {}).get("name", "No area"),
                "published_at": vacancy.get("published_at", "No date"),
                "salary": vacancy.get("salary", {}),
                "type": vacancy.get("type", {}).get("name", "No type"),
                "experience": vacancy.get("experience", {}).get("name", "No experience"),
                "employment": vacancy.get("employment", {}).get("name", "No employment"),
                "schedule": vacancy.get("schedule", {}).get("name", "No schedule"),
                "full_description": full_data.get("description", "No description available"),
                "key_skills": [skill["name"] for skill in full_data.get("key_skills", [])],
                "tags": [role["name"] for role in full_data.get("professional_roles", [])]
            }
            logging.info(f"Обработана вакансия {index + 1}/{total}")
            return processed_vacancy
        return None

    def save_to_json(self, filename: str):
        """Синхронное сохранение вакансий в JSON с промежуточным сохранением."""
        vacancies_to_save = []
        total_vacancies = len(self.vacancies)
        skipped_vacancies = 0

        for i, vacancy in enumerate(self.vacancies):
            result = self.process_vacancy(vacancy, i, total_vacancies)
            if result:
                vacancies_to_save.append(result)
                self.temp.append(result)
            else:
                skipped_vacancies += 1
                logging.error(f"Пропущена вакансия {i + 1}/{total_vacancies}")

            if len(self.temp) % 50 == 0 or len(self.temp) == total_vacancies - skipped_vacancies:
                self.save_temp_to_json("temp_vacancies.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(vacancies_to_save, f, ensure_ascii=False, indent=4)
        logging.info(f"Данные сохранены в {filename}: {len(vacancies_to_save)} вакансий, {skipped_vacancies} пропущено")
        
    def save_temp_to_json(self, filename: str):
        """Синхронное промежуточное сохранение временных данных."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.temp, f, ensure_ascii=False, indent=4)
        logging.info(f"Временные данные сохранены в {filename} ({len(self.temp)} вакансий)")

#     def run(self):
#         """Запуск синхронных операций сбора и сохранения вакансий."""
#         self.collect_all_vacancies()
#         self.save_to_json(f"vacancies_hh/{self.query} {datetime.now().strftime("%Y-%m-%d %H-%M")}.json")

# if __name__ == "__main__":
#     ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
#     hh_data = LaborMarketData(query="Информатик", access_token=ACCESS_TOKEN)
#     try:
#         hh_data.run()
#     except Exception as e:
#         logging.error(f"Процесс прерван: {e}. Временные данные сохранены в temp_vacancies.json")