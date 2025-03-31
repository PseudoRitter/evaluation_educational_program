# import random

# with open('training models/mpnet/resv2.csv', 'r', encoding='utf-8') as f:
#     all_lines = f.readlines()

# # Перемешиваем строки случайным образом
# random.shuffle(all_lines)

# # Вычисляем размеры выборок
# total_lines = len(all_lines)
# train_size = int(total_lines * 0.66) 
# valid_size = int(total_lines * 0.17)  
# test_size = total_lines - train_size - valid_size 

# # Разделяем данные на выборки
# train_data = all_lines[:train_size]
# valid_data = all_lines[train_size:train_size + valid_size]
# test_data = all_lines[train_size + valid_size:]

# # Функция для записи данных в файл
# def write_to_file(data, filename):
#     with open(filename, 'w', encoding='utf-8') as f:
#         f.writelines(data)  # Записываем строки как есть

# # Записываем данные в файлы
# write_to_file(train_data, 'train.txt')
# write_to_file(valid_data, 'valid.txt')
# write_to_file(test_data, 'test.txt')

# # Выводим статистику для проверки
# print(f"Всего строк: {total_lines}")
# print(f"Тренировочная выборка: {len(train_data)} строк")
# print(f"Валидационная выборка: {len(valid_data)} строк")
# print(f"Тестовая выборка: {len(test_data)} строк")



import pandas as pd

# Читаем CSV-файл
df = pd.read_csv('training models/mpnet/resv2.csv')

# Удаляем дубликаты по всем столбцам
df = df.drop_duplicates(subset=['sentence1', 'sentence2', 'label'], keep='first')

# Функция для получения первых трех слов из предложения
def get_first_two_words(sentence):
    words = sentence.split()
    return ' '.join(words[:3])

# Проходим по каждой строке и ищем совпадения
for index, row in df.iterrows():
    search_phrase = get_first_two_words(row['sentence1'])
    
    # Фильтруем строки, где первые три слова в sentence1 совпадают с search_phrase
    filtered_df = df[df['sentence1'].apply(lambda x: get_first_two_words(x) == search_phrase)]
    
    # Проверяем, что количество совпадений >= 4
    if len(filtered_df) >= 3:
        print(f"\nПоиск по фразе: '{search_phrase}' (найдено {len(filtered_df)} совпадений)")
        print(filtered_df.to_string(index=False))