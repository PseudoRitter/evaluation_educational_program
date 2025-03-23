import random

with open('training models/mpnet/mpnet_train.csv', 'r', encoding='utf-8') as f:
    all_lines = f.readlines()

# Перемешиваем строки случайным образом
random.shuffle(all_lines)

# Вычисляем размеры выборок
total_lines = len(all_lines)
train_size = int(total_lines * 0.66) 
valid_size = int(total_lines * 0.17)  
test_size = total_lines - train_size - valid_size 

# Разделяем данные на выборки
train_data = all_lines[:train_size]
valid_data = all_lines[train_size:train_size + valid_size]
test_data = all_lines[train_size + valid_size:]

# Функция для записи данных в файл
def write_to_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(data)  # Записываем строки как есть

# Записываем данные в файлы
write_to_file(train_data, 'train.txt')
write_to_file(valid_data, 'valid.txt')
write_to_file(test_data, 'test.txt')

# Выводим статистику для проверки
print(f"Всего строк: {total_lines}")
print(f"Тренировочная выборка: {len(train_data)} строк")
print(f"Валидационная выборка: {len(valid_data)} строк")
print(f"Тестовая выборка: {len(test_data)} строк")




