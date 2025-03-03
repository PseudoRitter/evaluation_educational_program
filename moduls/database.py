import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import logging
from psycopg2 import Error
import os
import json

class Database:
    def __init__(self, db_params, data_dir="vacancies"):
        """Инициализация подключения к базе данных PostgreSQL."""
        if not isinstance(db_params, dict):
            raise ValueError("db_params должен быть словарем, а не множеством или другим типом")
        self.db_params = db_params
        self.data_dir = data_dir
        self.connection = None
        self.cursor = None
        self.pool = ThreadedConnectionPool(1, 10, **self.db_params)  # Исправлено использование ThreadedConnectionPool
        self.connect()

    def connect(self):
        """Установка соединения с базой данных."""
        try:
            self.connection = self.pool.getconn()
            self.cursor = self.connection.cursor()
            logging.info("Успешно подключено к базе данных PostgreSQL")
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def disconnect(self):
        """Закрытие соединения с базой данных."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.pool.putconn(self.connection)
            logging.info("Соединение с базой данных закрыто")
        except Exception as e:
            logging.error(f"Ошибка при закрытии соединения: {e}")

    def get_connection(self):
        """Получение соединения из пула."""
        return self.pool.getconn()

    def release_connection(self, conn):
        """Возврат соединения в пул."""
        if conn:
            self.pool.putconn(conn)

    def fetch_educational_programs(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT educational_program_id, educational_program_name, educational_program_code
                    FROM educational_program
                    ORDER BY educational_program_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении программ: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_vacancies(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT vacancy_id, vacancy_name, vacancy_num, vacancty_date, vacancy_file
                    FROM vacancy
                    ORDER BY vacancy_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении вакансий: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_program_details(self, program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
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
                """, (program_id,))
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении деталей программы: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_vacancy_details(self, vacancy_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT vacancy_name, vacancy_num, vacancty_date, vacancy_file
                    FROM vacancy
                    WHERE vacancy_id = %s;
                """, (vacancy_id,))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении деталей вакансии: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_educational_program(self, name, code, university_id, year, type_program_id, competences):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO educational_program (educational_program_name, educational_program_code, 
                                                    university_id, educational_program_year, type_educational_program_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING educational_program_id;
                """, (name, code, university_id, year, type_program_id))
                program_id = cursor.fetchone()[0]
                for competence_id, type_competence_id in competences:
                    cursor.execute("""
                        INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                        VALUES (%s, %s, %s);
                    """, (competence_id, type_competence_id, program_id))
            conn.commit()
            return program_id
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_vacancy(self, name, num, date, file_path):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vacancy (vacancy_name, vacancy_num, vacancty_date, vacancy_file)
                    VALUES (%s, %s, %s, %s)
                    RETURNING vacancy_id;
                """, (name, num, date, file_path))
                vacancy_id = cursor.fetchone()[0]
            conn.commit()
            return vacancy_id
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении вакансии: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_educational_programs_with_details(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        ep.educational_program_name,
                        ep.educational_program_code,
                        ep.educational_program_year,
                        u.university_short_name,
                        tep.type_educational_program_name
                    FROM educational_program ep
                    JOIN university u ON ep.university_id = u.university_id
                    JOIN type_educational_program tep ON ep.type_educational_program_id = tep.type_educational_program_id
                    ORDER BY ep.educational_program_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении программ с деталями: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_program_id_by_name_and_code(self, name, code):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT educational_program_id
                    FROM educational_program
                    WHERE educational_program_name = %s AND educational_program_code = %s;
                """, (str(name).strip(), str(code).strip()))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ID программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_universities(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT university_full_name, university_short_name, university_city
                    FROM university
                    ORDER BY university_full_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении ВУЗов: {e}")
            return []
        finally:
            self.release_connection(conn)

    def save_university(self, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO university (university_full_name, university_short_name, university_city)
                    VALUES (%s, %s, %s)
                    RETURNING university_id;
                """, (full_name, short_name, city))
                university_id = cursor.fetchone()[0]
            conn.commit()
            return university_id
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_university_id_by_details(self, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT university_id
                    FROM university
                    WHERE university_full_name = %s AND university_short_name = %s AND university_city = %s;
                """, (full_name, short_name, city))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ID ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_university(self, university_id, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE university
                    SET university_full_name = %s, university_short_name = %s, university_city = %s
                    WHERE university_id = %s;
                """, (full_name, short_name, city, university_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении ВУЗа: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_university(self, university_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM educational_program WHERE university_id = %s;", (university_id,))
                if cursor.fetchone()[0] > 0:
                    logging.error("Нельзя удалить ВУЗ, он связан с программами.")
                    return False
                cursor.execute("DELETE FROM university WHERE university_id = %s;", (university_id,))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении ВУЗа: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_educational_program_types(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT type_educational_program_id, type_educational_program_name
                    FROM type_educational_program
                    ORDER BY type_educational_program_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении типов программ: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_university_by_short_name(self, short_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT university_id, university_full_name, university_short_name, university_city
                    FROM university
                    WHERE university_short_name = %s;
                """, (short_name,))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_educational_program_type_by_name(self, type_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT type_educational_program_id
                    FROM type_educational_program
                    WHERE type_educational_program_name = %s;
                """, (type_name,))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении ID типа программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_educational_program(self, program_id, name, code, university_id, year, type_program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE educational_program
                    SET educational_program_name = %s, educational_program_code = %s, 
                        university_id = %s, educational_program_year = %s, 
                        type_educational_program_id = %s
                    WHERE educational_program_id = %s;
                """, (name, code, university_id, year, type_program_id, program_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_educational_program(self, program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM competence_educational_program WHERE educational_program_id = %s;", (program_id,))
                cursor.execute("DELETE FROM educational_program WHERE educational_program_id = %s;", (program_id,))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_competence_types(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT type_competence_id, type_competence_full_name
                    FROM type_competence
                    ORDER BY type_competence_full_name;
                """)
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении типов компетенций: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_competence_by_name(self, competence_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT competence_id, competence_name, type_competence_id
                    FROM competence
                    WHERE competence_name = %s;
                """, (competence_name,))
                return cursor.fetchone()
        except Error as e:
            logging.error(f"Ошибка при получении компетенции: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_competence(self, competence_name, type_competence_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO competence (competence_name, type_competence_id)
                    VALUES (%s, %s)
                    RETURNING competence_id;
                """, (competence_name, type_competence_id))
                competence_id = cursor.fetchone()[0]
            conn.commit()
            return competence_id
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении компетенции: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_competence(self, competence_id, competence_name, type_competence_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE competence
                    SET competence_name = %s, type_competence_id = %s
                    WHERE competence_id = %s;
                """, (competence_name, type_competence_id, competence_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении компетенции: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_competence(self, competence_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM competence_educational_program WHERE competence_id = %s;", (competence_id,))
                if cursor.fetchone()[0] > 0:
                    logging.error("Нельзя удалить компетенцию, она связана с программами.")
                    return False
                cursor.execute("DELETE FROM competence WHERE competence_id = %s;", (competence_id,))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении компетенции: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_competences_for_program(self, program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT c.competence_name, tc.type_competence_full_name
                    FROM competence_educational_program cep
                    JOIN competence c ON cep.competence_id = c.competence_id
                    JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                    WHERE cep.educational_program_id = %s;
                """, (program_id,))
                return cursor.fetchall()
        except Error as e:
            logging.error(f"Ошибка при получении компетенций программы: {e}")
            return []
        finally:
            self.release_connection(conn)

    def save_competence_for_program(self, competence_id, type_competence_id, program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                    VALUES (%s, %s, %s);
                """, (competence_id, type_competence_id, program_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def update_competence_for_program(self, old_competence_id, old_type_competence_id, program_id, new_competence_id, new_type_competence_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM competence_educational_program 
                    WHERE competence_id = %s AND type_competence_id = %s AND educational_program_id = %s;
                """, (old_competence_id, old_type_competence_id, program_id))
                cursor.execute("""
                    INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                    VALUES (%s, %s, %s);
                """, (new_competence_id, new_type_competence_id, program_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_competence_for_program(self, competence_id, type_competence_id, program_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM competence_educational_program 
                    WHERE competence_id = %s AND type_competence_id = %s AND educational_program_id = %s;
                """, (competence_id, type_competence_id, program_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def update_vacancy(self, vacancy_id, name, num, date, file_path):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE vacancy
                    SET vacancy_name = %s, vacancy_num = %s, vacancty_date = %s, vacancy_file = %s
                    WHERE vacancy_id = %s;
                """, (name, num, date, file_path, vacancy_id))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении вакансии: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_vacancy(self, vacancy_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM vacancy WHERE vacancy_id = %s;", (vacancy_id,))
            conn.commit()
            return True
        except Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении вакансии: {e}")
            return False
        finally:
            self.release_connection(conn)