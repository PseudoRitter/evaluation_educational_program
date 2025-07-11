import sqlite3
import logging
import numpy as np
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="assessment_database.db", data_dir="vacancies"):
        self.db_path = os.path.abspath(db_path)
        if not os.path.exists(self.db_path):
            raise ValueError(f"Файл базы данных {self.db_path} не найден")
        self.data_dir = data_dir
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path, timeout=10)
            self.connection.execute("PRAGMA journal_mode=WAL;")
            self.cursor = self.connection.cursor()
            logging.info("Успешно подключено к базе данных SQLite")
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logging.info("Соединение с базой данных закрыто")
        except Exception as e:
            logging.error(f"Ошибка при закрытии соединения: {e}")

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL;")
            return conn
        except Exception as e:
            logging.error(f"Ошибка при создании нового соединения: {e}")
            raise

    def release_connection(self, conn):
        if conn:
            conn.close()

    def fetch_educational_programs(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT educational_program_id, educational_program_name, educational_program_code
                    FROM educational_program
                    ORDER BY educational_program_name;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении программ: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_vacancies(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT vacancy_id, vacancy_name, vacancy_num, vacancy_date, vacancy_file
                    FROM vacancy
                    ORDER BY vacancy_name;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении вакансий: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_program_details(self, program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
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
                    WHERE ep.educational_program_id = ?;
                """, (program_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении деталей программы: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_vacancy_details(self, vacancy_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT vacancy_name, vacancy_num, vacancy_date, vacancy_file
                    FROM vacancy
                    WHERE vacancy_id = ?;
                """, (vacancy_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении деталей вакансии: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_educational_program(self, name, code, university_id, year, type_program_id, competences):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO educational_program (educational_program_name, educational_program_code, 
                                                    university_id, educational_program_year, type_educational_program_id)
                    VALUES (?, ?, ?, ?, ?);
                """, (name, code, university_id, year, type_program_id))
                program_id = cursor.lastrowid
                for competence_id, type_competence_id in competences:
                    cursor.execute("""
                        INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                        VALUES (?, ?, ?);
                    """, (competence_id, type_competence_id, program_id))
                conn.commit()
                return program_id
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_vacancy(self, name, num, date, file_path):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vacancy (vacancy_name, vacancy_num, vacancy_date, vacancy_file)
                    VALUES (?, ?, ?, ?);
                """, (name, num, date, file_path))
                vacancy_id = cursor.lastrowid
                conn.commit()
                return vacancy_id
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении вакансии: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_educational_programs_with_details(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
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
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении программ с деталями: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_program_id_by_name_and_code(self, name, code, year, university_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT educational_program_id
                    FROM educational_program
                    WHERE educational_program_name = ? 
                    AND educational_program_code = ? 
                    AND educational_program_year = ? 
                    AND university_id = ?;
                """, (str(name).strip(), str(code).strip(), str(year).strip(), university_id))
                result = cursor.fetchone()
                return result if result else None
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении ID программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_universities(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT university_full_name, university_short_name, university_city
                    FROM university
                    ORDER BY university_full_name;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении ВУЗов: {e}")
            return []
        finally:
            self.release_connection(conn)

    def save_university(self, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO university (university_full_name, university_short_name, university_city)
                    VALUES (?, ?, ?);
                """, (full_name, short_name, city))
                university_id = cursor.lastrowid
                conn.commit()
                return university_id
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_university_id_by_details(self, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT university_id
                    FROM university
                    WHERE university_full_name = ? AND university_short_name = ? AND university_city = ?;
                """, (full_name, short_name, city))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении ID ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_university(self, university_id, full_name, short_name, city):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE university
                    SET university_full_name = ?, university_short_name = ?, university_city = ?
                    WHERE university_id = ?;
                """, (full_name, short_name, city, university_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении ВУЗа: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_university(self, university_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM educational_program WHERE university_id = ?;", (university_id,))
                if cursor.fetchone()[0] > 0:
                    logging.error("Нельзя удалить ВУЗ, он связан с программами.")
                    return False
                cursor.execute("DELETE FROM university WHERE university_id = ?;", (university_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении ВУЗа: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_educational_program_types(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT type_educational_program_id, type_educational_program_name
                    FROM type_educational_program
                    ORDER BY type_educational_program_name;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении типов программ: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_university_by_short_name(self, short_name):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT university_id, university_full_name, university_short_name, university_city
                    FROM university
                    WHERE university_short_name = ?;
                """, (short_name,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении ВУЗа: {e}")
            return None
        finally:
            self.release_connection(conn)

    def fetch_educational_program_type_by_name(self, type_name):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT type_educational_program_id
                    FROM type_educational_program
                    WHERE type_educational_program_name = ?;
                """, (type_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении ID типа программы: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_educational_program(self, program_id, name, code, university_id, year, type_program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE educational_program
                    SET educational_program_name = ?, educational_program_code = ?, 
                        university_id = ?, educational_program_year = ?, 
                        type_educational_program_id = ?
                    WHERE educational_program_id = ?;
                """, (name, code, university_id, year, type_program_id, program_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_educational_program(self, program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM competence_educational_program WHERE educational_program_id = ?;", (program_id,))
                cursor.execute("DELETE FROM educational_program WHERE educational_program_id = ?;", (program_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_competence_types(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT type_competence_id, type_competence_full_name
                    FROM type_competence
                    ORDER BY type_competence_full_name;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении типов компетенций: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_competence_by_name(self, competence_name):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT competence_id, competence_name, type_competence_id
                    FROM competence
                    WHERE competence_name = ?;
                """, (competence_name,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении компетенции: {e}")
            return None
        finally:
            self.release_connection(conn)

    def save_competence(self, competence_name, type_competence_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO competence (competence_name, type_competence_id)
                    VALUES (?, ?);
                """, (competence_name, type_competence_id))
                competence_id = cursor.lastrowid
                conn.commit()
                return competence_id
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении компетенции: {e}")
            return None
        finally:
            self.release_connection(conn)

    def update_competence(self, competence_id, competence_name, type_competence_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE competence
                    SET competence_name = ?, type_competence_id = ?
                    WHERE competence_id = ?;
                """, (competence_name, type_competence_id, competence_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении компетенции: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_competence(self, competence_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM competence_educational_program WHERE competence_id = ?;", (competence_id,))
                if cursor.fetchone()[0] > 0:
                    logging.error("Нельзя удалить компетенцию, она связана с программами.")
                    return False
                cursor.execute("DELETE FROM competence WHERE competence_id = ?;", (competence_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении компетенции: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_competences_for_program(self, program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.competence_name, tc.type_competence_full_name
                    FROM competence_educational_program cep
                    JOIN competence c ON cep.competence_id = c.competence_id
                    JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                    WHERE cep.educational_program_id = ?;
                """, (program_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении компетенций программы: {e}")
            return []
        finally:
            self.release_connection(conn)

    def save_competence_for_program(self, competence_id, type_competence_id, program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                    VALUES (?, ?, ?);
                """, (competence_id, type_competence_id, program_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при сохранении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def update_competence_for_program(self, old_competence_id, old_type_competence_id, program_id, new_competence_id, new_type_competence_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM competence_educational_program 
                    WHERE competence_id = ? AND type_competence_id = ? AND educational_program_id = ?;
                """, (old_competence_id, old_type_competence_id, program_id))
                cursor.execute("""
                    INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                    VALUES (?, ?, ?);
                """, (new_competence_id, new_type_competence_id, program_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_competence_for_program(self, competence_id, type_competence_id, program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM competence_educational_program 
                    WHERE competence_id = ? AND type_competence_id = ? AND educational_program_id = ?;
                """, (competence_id, type_competence_id, program_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении компетенции для программы: {e}")
            return False
        finally:
            self.release_connection(conn)

    def update_vacancy(self, vacancy_id, name, num, date, file_path):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE vacancy
                    SET vacancy_name = ?, vacancy_num = ?, vacancy_date = ?, vacancy_file = ?
                    WHERE vacancy_id = ?;
                """, (name, num, date, file_path, vacancy_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при обновлении вакансии: {e}")
            return False
        finally:
            self.release_connection(conn)

    def delete_vacancy(self, vacancy_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM vacancy WHERE vacancy_id = ?;", (vacancy_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при удалении вакансии: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_program_vacancy_history(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT 
                        ep.educational_program_name, 
                        u.university_short_name,
                        ep.educational_program_year,
                        v.vacancy_name, 
                        a.assessment_date
                    FROM assessment a
                    JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                    JOIN university u ON ep.university_id = u.university_id
                    JOIN vacancy v ON a.vacancy_id = v.vacancy_id
                    ORDER BY ep.educational_program_name, v.vacancy_name, a.assessment_date;
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении истории программ и вакансий: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_competence_history(self, educational_program_name, vacancy_name, assessment_date):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.competence_name, tc.type_competence_full_name, a.value
                    FROM assessment a
                    JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                    JOIN vacancy v ON a.vacancy_id = v.vacancy_id
                    JOIN competence c ON a.competence_id = c.competence_id
                    JOIN type_competence tc ON a.type_competence_id = tc.type_competence_id
                    WHERE ep.educational_program_name = ? AND v.vacancy_name = ? AND a.assessment_date = ?
                    ORDER BY c.competence_name;
                """, (educational_program_name, vacancy_name, assessment_date))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении истории компетенций: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_assessment_results(self, educational_program_name, vacancy_name, assessment_date):
        results = {"similarity_results": {}, "group_scores": {}, "overall_score": 0.0}
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.competence_name, tc.type_competence_full_name, a.value
                    FROM assessment a
                    JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                    JOIN vacancy v ON a.vacancy_id = v.vacancy_id
                    JOIN competence c ON a.competence_id = c.competence_id
                    JOIN type_competence tc ON a.type_competence_id = tc.type_competence_id
                    WHERE ep.educational_program_name = ? AND v.vacancy_name = ? AND a.assessment_date = ?
                    ORDER BY c.competence_name;
                """, (educational_program_name, vacancy_name, assessment_date))
                competences = cursor.fetchall()

                for competence_name, type_competence, score in competences:
                    results["similarity_results"][competence_name] = (float(score), type_competence)

                group_scores = {}
                for _, type_competence, score in competences:
                    group_scores.setdefault(type_competence, []).append(float(score))
                
                results["group_scores"] = {ctype: np.mean(scores) for ctype, scores in group_scores.items()}
                results["overall_score"] = np.mean([score for scores in group_scores.values() for score in scores])

            return results
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении результатов оценки: {e}")
            raise
        finally:
            self.release_connection(conn)

    def save_assessment_results(self, program_id, vacancy_id, similarity_results):
        if not similarity_results:
            logging.error("Нет данных для сохранения!")
            return False

        try:
            assessment_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn = self.get_connection()
            with conn:
                cursor = conn.cursor()
                for competence, (score, type_competence) in similarity_results.items():
                    competence_data = self.fetch_competence_by_name(competence)
                    if not competence_data:
                        logging.error(f"Компетенция '{competence}' не найдена!")
                        continue
                    competence_id, _, type_competence_id = competence_data

                    if not self.ensure_competence_program_link(competence_id, type_competence_id, program_id):
                        logging.error(f"Не удалось создать связь для '{competence}'")
                        continue

                    cursor.execute("""
                        INSERT INTO assessment (
                            competence_id, type_competence_id, educational_program_id, vacancy_id,
                            assessment_date, value
                        ) VALUES (?, ?, ?, ?, ?, ?);
                    """, (competence_id, type_competence_id, program_id, vacancy_id, assessment_date, float(score)))
                    logging.info(f"Сохранена оценка для '{competence}' со значением {score:.10f}")
                conn.commit()
            logging.info("Результаты успешно сохранены в таблице assessment.")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка сохранения результатов: {e}", exc_info=True)
            return False
        finally:
            self.release_connection(conn)

    def delete_assessment(self, educational_program_name, vacancy_name, assessment_date):
        conn = self.get_connection()
        try:
            assessment_date_truncated = assessment_date[:16]  
            logging.info(f"Обрезанная дата для удаления: {assessment_date_truncated}")

            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT assessment_id, assessment_date, ep.educational_program_name, v.vacancy_name
                    FROM assessment a
                    JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                    JOIN vacancy v ON a.vacancy_id = v.vacancy_id
                    WHERE ep.educational_program_name = ?
                    AND v.vacancy_name = ?
                    AND a.assessment_date = ?;
                """, (educational_program_name, vacancy_name, assessment_date_truncated))
                matching_records = cursor.fetchall()
                if not matching_records:
                    logging.warning(f"Запись не найдена: {educational_program_name}, {vacancy_name}, {assessment_date}")
                    cursor.execute("""
                        SELECT a.assessment_date FROM assessment a
                        JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                        JOIN vacancy v ON a.vacancy_id = v.vacancy_id
                        WHERE ep.educational_program_name = ?
                        AND v.vacancy_name = ?;
                    """, (educational_program_name, vacancy_name))
                    existing_dates = cursor.fetchall()
                    logging.warning(f"Существующие даты: {existing_dates}")
                    return False
                else:
                    logging.info(f"Найдено {len(matching_records)} записей для удаления: {matching_records}")

                cursor.execute("""
                    DELETE FROM assessment
                    WHERE educational_program_id IN (
                        SELECT ep.educational_program_id FROM educational_program ep
                        WHERE ep.educational_program_name = ?
                    ) AND vacancy_id IN (
                        SELECT v.vacancy_id FROM vacancy v WHERE v.vacancy_name = ?
                    ) AND assessment_date = ?;
                """, (educational_program_name, vacancy_name, assessment_date_truncated))
                deleted_rows = cursor.rowcount
                conn.commit()

                if deleted_rows > 0:
                    logging.info(f"Удалено {deleted_rows} строк: {educational_program_name}, {vacancy_name}, {assessment_date}")
                    return True
                else:
                    logging.warning(f"Запись не удалена: {educational_program_name}, {vacancy_name}, {assessment_date}")
                    return False
        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка удаления из assessment: {e}", exc_info=True)
            return False
        finally:
            self.release_connection(conn)

    def ensure_competence_program_link(self, competence_id, type_competence_id, educational_program_id):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM competence_educational_program
                    WHERE competence_id = ? AND type_competence_id = ? AND educational_program_id = ?;
                """, (competence_id, type_competence_id, educational_program_id))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO competence_educational_program (competence_id, type_competence_id, educational_program_id)
                        VALUES (?, ?, ?);
                    """, (competence_id, type_competence_id, educational_program_id))
                    logging.info(f"Добавлена связь: competence_id={competence_id}, type_competence_id={type_competence_id}, educational_program_id={educational_program_id}")
                conn.commit()
                return True
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Ошибка при добавлении связи: {e}")
            return False
        finally:
            self.release_connection(conn)

    def fetch_unique_programs_for_graphs(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT ep.educational_program_name, ep.educational_program_code,
                        ep.educational_program_year, u.university_short_name
                    FROM assessment a
                    JOIN educational_program ep ON a.educational_program_id = ep.educational_program_id
                    JOIN university u ON ep.university_id = u.university_id
                    ORDER BY ep.educational_program_name;
                """)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка при получении программ для графиков: {e}")
            return []
        finally:
            self.release_connection(conn)

    def fetch_program_code(self, program_name, year, univ_short_name):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT educational_program_code
                    FROM educational_program
                    WHERE educational_program_name = ? AND educational_program_year = ?
                    AND university_id = (SELECT university_id FROM university WHERE university_short_name = ?);
                """, (program_name, year, univ_short_name))
                result = cursor.fetchone()
                return result[0] if result else "Неизвестно"
        except Exception as e:
            logging.error(f"Ошибка при получении кода программы: {e}")
            return "Неизвестно"
        finally:
            self.release_connection(conn)

    def get_competence_types(self, competence_ids):
        try:
            if not competence_ids:
                return []
            conn = self.get_connection()
            with conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(competence_ids))
                cursor.execute(f"""
                    SELECT c.competence_id, tc.type_competence_full_name
                    FROM competence c
                    JOIN type_competence tc ON c.type_competence_id = tc.type_competence_id
                    WHERE c.competence_id IN ({placeholders});
                """, tuple(competence_ids))
                types = dict(cursor.fetchall())
            self.release_connection(conn)
            return [types.get(cid, "Неизвестно") for cid in competence_ids]
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения типов компетенций: {e}")
            return ["Неизвестно"] * len(competence_ids)