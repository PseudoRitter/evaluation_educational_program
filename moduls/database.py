import psycopg2
import logging
import json
import os
from psycopg2 import Error

class Database:
    def __init__(self, db_params, data_dir="vacancies"):
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
                SELECT 
                    ep.educational_program_name, 
                    ep.educational_program_code, 
                    u.university_full_name, 
                    ep.educational_program_year,
                    cep.competence_id, 
                    c.competence_name, 
                    tc.type_competence_full_name
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
                vacancy_data = json.load(f)
            # Предполагаем, что JSON — это список вакансий, берём первую (или все, если нужно)
            if isinstance(vacancy_data, list):
                for vacancy in vacancy_data:
                    if 'full_description' in vacancy:
                        return vacancy['full_description']
            elif isinstance(vacancy_data, dict) and 'full_description' in vacancy_data:
                return vacancy_data['full_description']
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

    def fetch_educational_programs_with_details(self):
        """Получение данных образовательных программ с расширенной информацией для таблицы."""
        try:
            query = """
                SELECT 
                    ep.educational_program_name,
                    ep.educational_program_code,
                    ep.educational_program_year,  -- Теперь как текст
                    u.university_short_name,
                    tep.type_educational_program_name
                FROM educational_program ep
                JOIN university u ON ep.university_id = u.university_id
                JOIN type_educational_program tep ON ep.type_educational_program_id = tep.type_educational_program_id
                ORDER BY ep.educational_program_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении данных образовательных программ: {e}")
            return []

    def fetch_program_id_by_name_and_code(self, name, code):
        """Получение program_id по имени и коду образовательной программы."""
        try:
            # Убедимся, что name и code — это строки, и уберём лишние пробелы
            name = str(name).strip() if name is not None else ""
            code = str(code).strip() if code is not None else ""
            logging.debug(f"Fetching program_id with name: '{name}', code: '{code}'")

            query = """
                SELECT educational_program_id
                FROM educational_program
                WHERE educational_program_name = %s AND educational_program_code = %s;
            """
            self.cursor.execute(query, (name, code))
            result = self.cursor.fetchone()
            logging.debug(f"Query result for name={name}, code={code}: {result}")
            return result
        except Error as e:
            logging.error(f"Ошибка при получении ID программы: {e}")
            return None

    def fetch_universities(self):
        """Получение списка ВУЗов из БД."""
        try:
            query = """
                SELECT university_full_name, university_short_name, university_city
                FROM university
                ORDER BY university_full_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении ВУЗов: {e}")
            return []

    def save_university(self, full_name, short_name, city):
        """Сохранение нового ВУЗа в БД."""
        try:
            query = """
                INSERT INTO university (university_full_name, university_short_name, university_city)
                VALUES (%s, %s, %s)
                RETURNING university_id;
            """
            self.cursor.execute(query, (full_name, short_name, city))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        except Error as e:
            logging.error(f"Ошибка при сохранении ВУЗа: {e}")
            self.connection.rollback()
            return None

    def fetch_university_id_by_details(self, full_name, short_name, city):
        """Получение university_id по данным ВУЗа."""
        try:
            query = """
                SELECT university_id
                FROM university
                WHERE university_full_name = %s AND university_short_name = %s AND university_city = %s;
            """
            self.cursor.execute(query, (full_name, short_name, city))
            return self.cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ID ВУЗа: {e}")
            return None

    def update_university(self, university_id, full_name, short_name, city):
        """Обновление данных ВУZa в БД."""
        try:
            query = """
                UPDATE university
                SET university_full_name = %s, university_short_name = %s, university_city = %s
                WHERE university_id = %s;
            """
            self.cursor.execute(query, (full_name, short_name, city, university_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при обновлении ВУZa: {e}")
            self.connection.rollback()
            return False

    def delete_university(self, university_id):
        """Удаление ВУZa из БД."""
        try:
            # Сначала проверяем, нет ли связей с образовательными программами
            check_query = """
                SELECT COUNT(*) FROM educational_program WHERE university_id = %s;
            """
            self.cursor.execute(check_query, (university_id,))
            if self.cursor.fetchone()[0] > 0:
                logging.error("Нельзя удалить ВУЗ, так как он связан с образовательными программами.")
                return False

            # Удаляем ВУЗ
            delete_query = """
                DELETE FROM university WHERE university_id = %s;
            """
            self.cursor.execute(delete_query, (university_id,))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при удалении ВУЗа: {e}")
            self.connection.rollback()
            return False

    def fetch_educational_program_types(self):
        """Получение списка типов образовательных программ из БД."""
        try:
            query = """
                SELECT type_educational_program_id, type_educational_program_name
                FROM type_educational_program
                ORDER BY type_educational_program_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении типов образовательных программ: {e}")
            return []

    def fetch_university_by_short_name(self, short_name):
        """Получение данных ВУЗа по краткому наименованию."""
        try:
            query = """
                SELECT university_id, university_full_name, university_short_name, university_city
                FROM university
                WHERE university_short_name = %s;
            """
            self.cursor.execute(query, (short_name,))
            return self.cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ВУЗа по краткому наименованию: {e}")
            return None

    def fetch_educational_program_type_by_name(self, type_name):
        """Получение type_educational_program_id по названию типа программы."""
        try:
            query = """
                SELECT type_educational_program_id
                FROM type_educational_program
                WHERE type_educational_program_name = %s;
            """
            self.cursor.execute(query, (type_name,))
            return self.cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ID типа программы: {e}")
            return None

    def update_educational_program(self, program_id, name, code, university_id, year, type_program_id):
        """Обновление данных образовательной программы в БД."""
        try:
            query = """
                UPDATE educational_program
                SET educational_program_name = %s, educational_program_code = %s, 
                    university_id = %s, educational_program_year = %s, 
                    type_educational_program_id = %s
                WHERE educational_program_id = %s;
            """
            self.cursor.execute(query, (name, code, university_id, year, type_program_id, program_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при обновлении образовательной программы: {e}")
            self.connection.rollback()
            return False

    def delete_educational_program(self, program_id):
        """Удаление образовательной программы из БД."""
        try:
            # Удаляем связанные записи в competence_educational_program
            delete_competence_query = """
                DELETE FROM competence_educational_program 
                WHERE educational_program_id = %s;
            """
            self.cursor.execute(delete_competence_query, (program_id,))

            # Удаляем образовательную программу
            delete_program_query = """
                DELETE FROM educational_program 
                WHERE educational_program_id = %s;
            """
            self.cursor.execute(delete_program_query, (program_id,))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при удалении образовательной программы: {e}")
            self.connection.rollback()
            return False

    def fetch_competence_types(self):
        """Получение списка типов компетенций из БД."""
        try:
            query = """
                SELECT type_competence_id, type_competence_full_name
                FROM type_competence
                ORDER BY type_competence_full_name;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении типов компетенций: {e}")
            return []

    def fetch_competence_by_name(self, competence_name):
        """Получение данных компетенции по её названию."""
        try:
            query = """
                SELECT competence_id, competence_name, type_competence_id
                FROM competence
                WHERE competence_name = %s;
            """
            self.cursor.execute(query, (competence_name,))
            return self.cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении компетенции по названию: {e}")
            return None

    def save_competence(self, competence_name, type_competence_id):
        """Сохранение новой компетенции в БД."""
        try:
            query = """
                INSERT INTO competence (competence_name, type_competence_id)
                VALUES (%s, %s)
                RETURNING competence_id;
            """
            self.cursor.execute(query, (competence_name, type_competence_id))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        except Error as e:
            logging.error(f"Ошибка при сохранении компетенции: {e}")
            self.connection.rollback()
            return None

    def update_competence(self, competence_id, competence_name, type_competence_id):
        """Обновление данных компетенции в БД."""
        try:
            query = """
                UPDATE competence
                SET competence_name = %s, type_competence_id = %s
                WHERE competence_id = %s;
            """
            self.cursor.execute(query, (competence_name, type_competence_id, competence_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при обновлении компетенции: {e}")
            self.connection.rollback()
            return False

    def delete_competence(self, competence_id):
        """Удаление компетенции из БД."""
        try:
            # Сначала проверяем, нет ли связей с образовательными программами
            check_query = """
                SELECT COUNT(*) FROM competence_educational_program WHERE competence_id = %s;
            """
            self.cursor.execute(check_query, (competence_id,))
            if self.cursor.fetchone()[0] > 0:
                logging.error("Нельзя удалить компетенцию, так как она связана с образовательными программами.")
                return False

            # Удаляем компетенцию
            delete_query = """
                DELETE FROM competence WHERE competence_id = %s;
            """
            self.cursor.execute(delete_query, (competence_id,))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при удалении компетенции: {e}")
            self.connection.rollback()
            return False

    def fetch_competences_for_program(self, program_id):
        """Получение списка компетенций для образовательной программы из БД."""
        try:
            query = """
                SELECT c.competence_name, tc.type_competence_full_name
                FROM competence_educational_program cep
                JOIN competence c ON cep.competence_id = c.competence_id
                JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                WHERE cep.educational_program_id = %s;
            """
            self.cursor.execute(query, (program_id,))
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении компетенций программы: {e}")
            return []

    def save_competence_for_program(self, competence_id, type_competence_id, program_id):
        """Сохранение связи компетенции с образовательной программой в БД."""
        try:
            query = """
                INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                VALUES (%s, %s, %s);
            """
            self.cursor.execute(query, (competence_id, type_competence_id, program_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при сохранении связи компетенции с программой: {e}")
            self.connection.rollback()
            return False

    def update_competence_for_program(self, old_competence_id, old_type_competence_id, program_id, new_competence_id, new_type_competence_id):
        """Обновление связи компетенции с образовательной программой в БД."""
        try:
            # Удаляем старую связь
            delete_query = """
                DELETE FROM competence_educational_program 
                WHERE competence_id = %s AND type_competence_id = %s AND educational_program_id = %s;
            """
            self.cursor.execute(delete_query, (old_competence_id, old_type_competence_id, program_id))

            # Добавляем новую связь
            insert_query = """
                INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                VALUES (%s, %s, %s);
            """
            self.cursor.execute(insert_query, (new_competence_id, new_type_competence_id, program_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при обновлении связи компетенции с программой: {e}")
            self.connection.rollback()
            return False

    def delete_competence_for_program(self, competence_id, type_competence_id, program_id):
        """Удаление связи компетенции с образовательной программой из БД."""
        try:
            query = """
                DELETE FROM competence_educational_program 
                WHERE competence_id = %s AND type_competence_id = %s AND educational_program_id = %s;
            """
            self.cursor.execute(query, (competence_id, type_competence_id, program_id))
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"Ошибка при удалении связи компетенции с программой: {e}")
            self.connection.rollback()
            return False

# Пример использования с твоими параметрами
if __name__ == "__main__":
    db_params = {
        "database": "postgres",
        "user": "postgres",
        "password": "1111",
        "host": "localhost",
        "port": "5432"
    }

    db = Database(db_params, data_dir="vacancies")
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

        universities = db.fetch_universities()
        for university in universities:
            print(university)

        program_types = db.fetch_educational_program_types()
        for program_type in program_types:
            print(program_type)

        competence_types = db.fetch_competence_types()
        for competence_type in competence_types:
            print(competence_type)
    finally:
        db.disconnect()