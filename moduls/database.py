import psycopg2
import logging
import json
import os
from psycopg2 import Error

class Database:
    def __init__(self, db_params, data_dir="data"):
        """Инициализация подключения к базе данных PostgreSQL."""
        self.db_params = db_params
        self.data_dir = data_dir  # Директория, где хранятся JSON-файлы
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Установка соединения с базой данных."""
        try:
            self.connection = psycopg2.connect(**self.db_params)
            self.cursor = self.connection.cursor()
            logging.info("Успешно подключено к базе данных PostgreSQL")
        except Error as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def disconnect(self):
        """Закрытие соединения с базой данных."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logging.info("Соединение с базой данных закрыто")
        except Error as e:
            logging.error(f"Ошибка при закрытии соединения: {e}")

    def fetch_educational_programs(self):
        """Получение списка образовательных программ из БД."""
        try:
            query = """
                SELECT educational_program_id, educational_program_name, educational_program_code
                FROM educational_program
                ORDER BY educational_program_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении образовательных программ: {e}")
            return []

    def fetch_vacancies(self):
        """Получение списка вакансий из БД с путями к JSON-файлам."""
        try:
            query = """
                SELECT vacancy_id, vacancy_name, vacancy_file
                FROM vacancy
                ORDER BY vacancy_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении вакансий: {e}")
            return []

    def fetch_program_details(self, program_id):
        """Получение деталей образовательной программы, включая описание и навыки."""
        try:
            query = """
                SELECT ep.educational_program_name, ep.educational_program_code, 
                       u.university_full_name, ep.educational_program_year,
                       cep.competence_id, c.competence_name, tc.type_competence_full_name
                FROM educational_program ep
                LEFT JOIN university u ON ep.university_id = u.university_id
                LEFT JOIN competence_educational_program cep ON ep.educational_program_id = cep.educational_program_id
                LEFT JOIN competence c ON cep.competence_id = c.competence_id AND cep.type_competence_id = c.type_competence_id
                LEFT JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                WHERE ep.educational_program_id = %s;
            """
            self.cursor.execute(query, (program_id,))
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении деталей программы: {e}")
            return []

    def fetch_vacancy_details(self, vacancy_id):
        """Получение деталей вакансии, включая путь к JSON-файлу."""
        try:
            query = """
                SELECT vacancy_name, vacancy_file
                FROM vacancy
                WHERE vacancy_id = %s;
            """
            self.cursor.execute(query, (vacancy_id,))
            return self.cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении деталей вакансии: {e}")
            return None

    def load_vacancy_from_file(self, file_path):
        """Загрузка данных вакансии из JSON-файла по указанному пути."""
        try:
            full_path = os.path.join(self.data_dir, file_path)
            if not os.path.exists(full_path):
                logging.error(f"Файл вакансии не найден: {full_path}")
                return None
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Предполагаем, что JSON — это список вакансий, берём первую (или все, если нужно)
            if isinstance(data, list):
                for vacancy in data:
                    if 'full_description' in vacancy:
                        return vacancy['full_description']
            elif isinstance(data, dict) and 'full_description' in data:
                return data['full_description']
            logging.warning(f"Не найдено поле 'full_description' в файле: {full_path}")
            return ''
        except (json.JSONDecodeError, Exception) as e:
            logging.error(f"Ошибка при загрузке JSON-файла вакансии: {e}")
            return ''

    def save_educational_program(self, name, code, university_id, year, type_program_id, competences):
        """Сохранение новой образовательной программы в БД."""
        try:
            query = """
                INSERT INTO educational_program (educational_program_name, educational_program_code, 
                                                university_id, educational_program_year, type_educational_program_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING educational_program_id;
            """
            self.cursor.execute(query, (name, code, university_id, year, type_program_id))
            program_id = self.cursor.fetchone()[0]
            
            # Сохранение компетенций
            for competence_id, type_competence_id in competences:
                query_competence = """
                    INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                    VALUES (%s, %s, %s);
                """
                self.cursor.execute(query_competence, (competence_id, type_competence_id, program_id))
            
            self.connection.commit()
            return program_id
        except Error as e:
            logging.error(f"Ошибка при сохранении образовательной программы: {e}")
            self.connection.rollback()
            return None

    def save_vacancy(self, name, num, date, file_path):
        """Сохранение новой вакансии в БД с указанием пути к JSON-файлу."""
        try:
            query = """
                INSERT INTO vacancy (vacancy_name, vacancy_num, vacancty_date, vacancy_file)
                VALUES (%s, %s, %s, %s)
                RETURNING vacancy_id;
            """
            self.cursor.execute(query, (name, num, date, file_path))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        except Error as e:
            logging.error(f"Ошибка при сохранении вакансии: {e}")
            self.connection.rollback()
            return None

# Пример использования с твоими параметрами
if __name__ == "__main__":
    db_params = {
        "database": "postgres",
        "user": "postgres",
        "password": "1111",
        "host": "localhost",
        "port": "5432"
    }

    db = Database(db_params, data_dir="data")
    try:
        # Пример получения данных
        programs = db.fetch_educational_programs()
        for program in programs:
            print(program)
        
        vacancies = db.fetch_vacancies()
        for vacancy in vacancies:
            print(vacancy)
            # Пример загрузки данных из JSON
            description = db.load_vacancy_from_file(vacancy[2])  # vacancy_file — путь
            print(f"Описание вакансии: {description}")
    finally:
        db.disconnect()