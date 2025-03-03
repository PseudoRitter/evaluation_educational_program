import aiohttp
import asyncio
import json
import time
import random
import logging
from aiohttp import ClientSession

class LaborMarketData:
    def __init__(self, query: str, access_token: str, max_vacancies_per_experience=2000):
        self.base_url = "https://api.hh.ru/vacancies"
        self.query = query
        self.access_token = access_token
        self.vacancies = []
        self.max_vacancies_per_experience = max_vacancies_per_experience
        self.temp = []
        self.headers = {'Authorization': f'Bearer {self.access_token}'}
        self.rate_limit_delay = 1.0  # Начальная задержка для соблюдения лимитов API

    async def fetch_page(self, session: ClientSession, page: int, experience: str):
        """Асинхронный запрос страницы вакансий."""
        params = {
            'text': self.query,
            'area': 90,  # Можно сделать параметром в будущем
            'per_page': 100,
            'page': page,
            'experience': experience
        }
        try:
            async with session.get(self.base_url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', []), data.get('pages', 1)
                elif response.status == 429:  # Too Many Requests
                    logging.warning(f"Лимит запросов превышен для {experience}, страница {page}. Увеличиваем задержку.")
                    self.rate_limit_delay += 1.0
                    await asyncio.sleep(self.rate_limit_delay)
                    return await self.fetch_page(session, page, experience)  # Повторяем запрос
                else:
                    logging.error(f"Ошибка {response.status} при запросе страницы {page} для {experience}")
                    return [], 1
        except Exception as e:
            logging.error(f"Ошибка при запросе страницы {page} для {experience}: {e}")
            return [], 1

    async def fetch_vacancies_by_experience(self, session: ClientSession, experience: str):
        """Сбор вакансий для заданного уровня опыта."""
        page = 0
        max_pages = 20
        experience_vacancies = []

        while page < max_pages and len(experience_vacancies) < self.max_vacancies_per_experience:
            items, total_pages = await self.fetch_page(session, page, experience)
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
            await asyncio.sleep(self.rate_limit_delay)  # Задержка для соблюдения лимитов API

        # Ограничиваем количество вакансий
        return experience_vacancies[:self.max_vacancies_per_experience]

    async def fetch_full_vacancy_data(self, session: ClientSession, vacancy_id: str):
        """Асинхронный запрос полной информации о вакансии."""
        url = f"{self.base_url}/{vacancy_id}"
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logging.warning(f"Вакансия {vacancy_id} не найдена.")
                    return None
                elif response.status == 429:
                    logging.warning(f"Лимит запросов для {vacancy_id}. Увеличиваем задержку.")
                    self.rate_limit_delay += 1.0
                    await asyncio.sleep(self.rate_limit_delay)
                    return await self.fetch_full_vacancy_data(session, vacancy_id)
                else:
                    logging.error(f"Ошибка {response.status} для вакансии {vacancy_id}")
                    return None
        except Exception as e:
            logging.error(f"Ошибка при запросе вакансии {vacancy_id}: {e}")
            return None

    async def collect_all_vacancies(self):
        """Асинхронный сбор всех вакансий по уровням опыта."""
        experience_levels = ['noExperience', 'between1And3', 'between3And6', 'moreThan6']
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_vacancies_by_experience(session, exp) for exp in experience_levels]
            results = await asyncio.gather(*tasks)
            self.vacancies = [vacancy for sublist in results for vacancy in sublist]
            logging.info(f"Собрано всего {len(self.vacancies)} вакансий")

    async def process_vacancy(self, session: ClientSession, vacancy, index, total):
        """Обработка одной вакансии с сохранением полной информации."""
        full_data = await self.fetch_full_vacancy_data(session, vacancy['id'])
        if full_data:
            processed_vacancy = {
                "id": vacancy['id'],
                "name": vacancy.get('name', 'No name'),
                "employer": vacancy.get('employer', {}).get('name', 'No employer'),
                "area": vacancy.get('area', {}).get('name', 'No area'),
                "published_at": vacancy.get('published_at', 'No date'),
                "salary": vacancy.get('salary', {}),
                "type": vacancy.get('type', {}).get('name', 'No type'),
                "experience": vacancy.get('experience', {}).get('name', 'No experience'),
                "employment": vacancy.get('employment', {}).get('name', 'No employment'),
                "schedule": vacancy.get('schedule', {}).get('name', 'No schedule'),
                "full_description": full_data.get('description', 'No description available'),
                "key_skills": [skill['name'] for skill in full_data.get('key_skills', [])],
                "tags": [role['name'] for role in full_data.get('professional_roles', [])]
            }
            logging.info(f"Обработана вакансия {index + 1}/{total}")
            return processed_vacancy
        return None

    async def save_to_json(self, filename: str):
        """Асинхронное сохранение вакансий в JSON с промежуточным сохранением."""
        vacancies_to_save = []
        total_vacancies = len(self.vacancies)
        skipped_vacancies = 0

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.process_vacancy(session, vacancy, i, total_vacancies)
                for i, vacancy in enumerate(self.vacancies)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    skipped_vacancies += 1
                    logging.error(f"Ошибка обработки вакансии: {result}")
                elif result:
                    vacancies_to_save.append(result)
                    self.temp.append(result)

                # Промежуточное сохранение каждые 50 вакансий
                if len(self.temp) % 50 == 0 or len(self.temp) == total_vacancies - skipped_vacancies:
                    await self.save_temp_to_json("temp_vacancies.json")

        # Финальное сохранение
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vacancies_to_save, f, ensure_ascii=False, indent=4)
        logging.info(f"Данные сохранены в {filename}: {len(vacancies_to_save)} вакансий, {skipped_vacancies} пропущено")

    async def save_temp_to_json(self, filename: str):
        """Асинхронное промежуточное сохранение временных данных."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.temp, f, ensure_ascii=False, indent=4)
        logging.info(f"Временные данные сохранены в {filename} ({len(self.temp)} вакансий)")

    def run(self):
        """Запуск асинхронных операций."""
        asyncio.run(self.collect_all_vacancies())
        asyncio.run(self.save_to_json(f"vacancies_hh/{self.query}_{time.strftime('%Y-%m-%d_%H-%M')}.json"))

# Пример использования
if __name__ == "__main__":
    ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
    hh_data = LaborMarketData(query="системный аналитик", access_token=ACCESS_TOKEN)
    try:
        hh_data.run()
    except Exception as e:
        logging.error(f"Процесс прерван: {e}. Временные данные сохранены в temp_vacancies.json")