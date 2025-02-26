import requests
import json
import time
import random

class LaborMarketData:
    def __init__(self, query: str, access_token: str):
        self.base_url = "https://api.hh.ru/vacancies"
        self.query = query
        self.access_token = access_token
        self.vacancies = []
        self.max_vacancies_per_experience = 2000
        self.temp = []

    def fetch_data_by_experience(self, experience: str):
        page = 0
        max_pages = 20
        headers = {'Authorization': f'Bearer {self.access_token}'}
        while page < max_pages:
            params = {
                'text': self.query,
                'area': 113,
                'per_page': 100,
                'page': page,
                'experience': experience
            }
            response = requests.get(self.base_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if not data.get('items'):
                    print(f"No more vacancies available for experience level: {experience}.")
                    break
                self.vacancies.extend(data['items'])
                print(f"Fetched {len(data['items'])} vacancies from page {page} for experience level: {experience}")
                if len(self.vacancies) >= self.max_vacancies_per_experience:
                    print(f"Reached maximum limit of {self.max_vacancies_per_experience} vacancies for experience level: {experience}.")
                    self.vacancies = self.vacancies[:self.max_vacancies_per_experience]
                    break
                if page >= data.get('pages', 0) - 1:
                    print(f"All pages fetched for experience level: {experience}.")
                    break
                page += 1
                #time.sleep(random.uniform(10, 20))
            else:
                print(f"Error fetching data for experience level {experience}: {response.status_code}. Stopping the process.")
                break

    def get_full_vacancy_data(self, vacancy_id: str):
        vacancy_url = f"{self.base_url}/{vacancy_id}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        #time.sleep(random.uniform(1, 5))
        try:
            response = requests.get(vacancy_url, headers=headers, timeout=30) #timeout=30
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Vacancy with ID {vacancy_id} not found. Skipping...")
                return None
            else:
                print(f"Error fetching full vacancy data for ID {vacancy_id}: "
                      f"Status Code = {response.status_code}, "
                      f"Response Type = {response.headers.get('Content-Type', 'Unknown')}, "
                      f"Response Body = {response.text[:200]}...")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed for ID {vacancy_id}: {e}. Skipping this vacancy.")
            return None  # Пропускаем вакансию при ошибке

    def collect_all_vacancies(self):
        experience_levels = ['noExperience', 'between1And3', 'between3And6', 'moreThan6']
        all_vacancies = []
        for experience in experience_levels:
            print(f"Fetching vacancies for experience level: {experience}")
            self.vacancies = []
            self.fetch_data_by_experience(experience)
            all_vacancies.extend(self.vacancies)
        self.vacancies = all_vacancies

    def save_to_json(self, filename: str):
        vacancies_to_save = []
        total_vacancies = len(self.vacancies)
        skipped_vacancies = 0  # Счетчик пропущенных вакансий

        for index, vacancy in enumerate(self.vacancies):
            try:
                full_vacancy_data = self.get_full_vacancy_data(vacancy['id'])
                if full_vacancy_data:
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
                        "full_description": full_vacancy_data.get('description', 'No description available'),
                        "key_skills": [skill['name'] for skill in full_vacancy_data.get('key_skills', [])],
                        "tags": [role['name'] for role in full_vacancy_data.get('professional_roles', [])]
                    }
                    vacancies_to_save.append(processed_vacancy)
                    self.temp.append(processed_vacancy)
                    print(f"Processed {index + 1}/{total_vacancies} vacancies.")
                else:
                    skipped_vacancies += 1
                    print(f"Skipped vacancy {index + 1}/{total_vacancies} due to fetch error.")

                if (index + 1) % 50 == 0 or (index + 1) == total_vacancies:
                    self.save_temp_to_json("temp_vacancies.json")

            except Exception as e:
                skipped_vacancies += 1
                print(f"Error processing vacancy {index + 1}/{total_vacancies}: {e}. Skipping this vacancy.")
                self.save_temp_to_json("temp_vacancies.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vacancies_to_save, f, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {filename} ({len(vacancies_to_save)} vacancies processed, {skipped_vacancies} skipped)")

    def save_temp_to_json(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.temp, f, ensure_ascii=False, indent=4)
        print(f"Temporary data saved to {filename} ({len(self.temp)} vacancies).")

# Пример использования класса
if __name__ == "__main__":
    ACCESS_TOKEN = "APPLRDK45780T0N5LTCCGEC9DU19NPGSORRJP5535R95VETEF4203PHSQI97V49C"
    hh_data = LaborMarketData(query="системный аналитик", access_token=ACCESS_TOKEN)
    try:
        hh_data.collect_all_vacancies()
        hh_data.save_to_json("системный аналитик.json")
    except Exception as e:
        print(f"Process interrupted due to an error: {e}. Temporary data may be saved in temp_vacancies.json.")