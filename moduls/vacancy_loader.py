import json

class VacancyLoader:
    def __init__(self, filename):
        self.filename = filename

    def load_vacancy_descriptions_field(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            vacancies = json.load(file)
            return [vacancy.get('full_description', '') for vacancy in vacancies]
