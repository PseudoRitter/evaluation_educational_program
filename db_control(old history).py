import sqlite3

conntection = sqlite3.connect('my_database.db')
cursor = conntection.cursor()

cursor.execute(''' 
CREATE TABLE educational_program (
educational_program_id  INTEGER PRIMARY KEY AUTOINCREMENT,
educational_program_name TEXT NOT NULL, 
educational_program_code TEXT NOT NULL,
university_id INTEGER NOT NULL,
educational_program_year TEXT NOT NULL,
type_educational_program_id TEXT NOT NULL
               )   
''')


conntection.commit()
conntection.close()