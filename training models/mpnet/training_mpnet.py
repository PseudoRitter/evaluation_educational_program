# import pandas as pd
# from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
# from torch.utils.data import DataLoader
# import torch
# import os
# import sentence_transformers
# import transformers

# print(f"Версия sentence-transformers: {sentence_transformers.__version__}")
# print(f"Версия transformers: {transformers.__version__}")

# def parse_label(label):
#     """Универсальный парсер меток"""
#     try:
#         label_str = str(label).strip().replace(',', '.')
#         cleaned = ''.join(c for c in label_str if c.isdigit() or c in ['.', '-'])
#         value = float(cleaned)
#         return min(max(abs(value), 0.0), 1.0)
#     except ValueError:
#         print(f"Некорректный формат метки: '{label}'")
#         return None

# def load_data(file_path, dataset_type="train"):
#     try:
#         df = pd.read_csv(file_path, usecols=[0, 1, 2], 
#                          names=['sentence1', 'sentence2', 'label'], 
#                          header=0, 
#                          dtype={'label': str})
#     except pd.errors.ParserError as e:
#         print(f"Ошибка парсинга {dataset_type} CSV: {e}")
#         df = pd.read_csv(file_path, usecols=[0, 1, 2], 
#                          names=['sentence1', 'sentence2', 'label'], 
#                          header=0, 
#                          on_bad_lines='skip', 
#                          dtype={'label': str})

#     df['sentence1'] = df['sentence1'].fillna('').astype(str)
#     df['sentence2'] = df['sentence2'].fillna('').astype(str)

#     examples = []
#     for _, row in df.iterrows():
#         label = parse_label(row['label'])
        
#         if label is None:
#             print(f"Пропущена некорректная метка в {dataset_type}: {row['label']}")
#             continue
            
#         if row['sentence1'].strip() and row['sentence2'].strip():
#             examples.append(InputExample(
#                 texts=[row['sentence1'], row['sentence2']], 
#                 label=label
#             ))
#         else:
#             print(f"Пропущена строка с пустыми предложениями в {dataset_type}")
            
#     return examples

# def create_similarity_evaluator(examples, name):
#     """Создает оценщика для регрессии схожести"""
#     sentences1 = []
#     sentences2 = []
#     scores = []
#     for example in examples:
#         sentences1.append(example.texts[0])
#         sentences2.append(example.texts[1])
#         scores.append(example.label)
        
#     return evaluation.EmbeddingSimilarityEvaluator(
#         sentences1, 
#         sentences2, 
#         scores,
#         name=name,
#         show_progress_bar=True,
#         batch_size=16
#     )

# def train_model():
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#     print(f"Используемое устройство: {device}")

#     model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2').to(device)
    
#     # Загрузка данных
#     train_data = load_data('training models/mpnet/mpnet_train.csv', 'train')
#     dev_data = load_data('training models/mpnet/mpnet_valid.csv', 'validation')
#     test_data = load_data('training models/mpnet/mpnet_test.csv', 'test')

#     print(f"Размеры наборов данных:")
#     print(f"  Обучение: {len(train_data)}")
#     print(f"  Валидация: {len(dev_data)}")
#     print(f"  Тест: {len(test_data)}")

#     # Создание DataLoader
#     train_dataloader = DataLoader(train_data, shuffle=True, batch_size=1)
#     train_loss = losses.CosineSimilarityLoss(model).to(device)
    
#     # Создание оценщиков
#     dev_evaluator = create_similarity_evaluator(dev_data, 'validation')
#     test_evaluator = create_similarity_evaluator(test_data, 'test')

#     # Параметры обучения
#     output_dir = 'C:/python-models/tuned_model_mpnet_v3'
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Начало обучения
#     model.fit(
#         train_objectives=[(train_dataloader, train_loss)],
#         evaluator=dev_evaluator,
#         epochs=8,
#         warmup_steps=100,
#         output_path=output_dir,
#         save_best_model=True,
#         optimizer_params={'lr': 2e-4},
#         evaluation_steps=500,
#         checkpoint_save_steps=1000,
#         checkpoint_save_total_limit=3,
#         callback=lambda score, epoch, steps: print(f"[Эпоха {epoch} шаг {steps}] Текущий скор: {score:.6f}")
#     )
    
#     # Финальная оценка
#     test_metrics = test_evaluator(model, output_path=output_dir)
    
#     # Вывод всех метрик
#     print("\nФинальные результаты на тестовом наборе:")
#     for metric, value in test_metrics.items():
#         print(f"  {metric.upper()}: {value:.6f}")

# if __name__ == '__main__':
#     print("Начинаем обучение модели...")
#     train_model()
#     print("Обучение завершено!")


import os
import torch
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from datasets import Dataset

# 1. Загрузка данных через pandas
def load_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found. Please check the path.")
    
    # Чтение CSV файла
    df = pd.read_csv(file_path, header=None, names=["sentence1", "sentence2", "score"], quoting=1)
    
    # Проверка наличия необходимых столбцов
    required_columns = {"sentence1", "sentence2", "score"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_columns}. Ensure your CSV file has these columns.")
    
    # Разделение на тренировочную и тестовую выборки
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)
    
    return train_df, eval_df

# 2. Создание InputExamples для SentenceTransformers
def create_input_examples(df):
    examples = []
    for _, row in df.iterrows():
        sentence1 = row["sentence1"]
        sentence2 = row["sentence2"]
        score = float(row["score"])
        examples.append(InputExample(texts=[sentence1, sentence2], label=score))
    return examples

# 3. Дообучение модели с поддержкой GPU
def fine_tune_model(train_df, eval_df, output_dir="C:/python-models/tuned_model_mpnet"):
    # Проверка наличия GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Загрузка предобученной модели
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2", device=device)
    
    # Создание InputExamples для обучения и валидации
    train_examples = create_input_examples(train_df)
    eval_examples = create_input_examples(eval_df)
    
    # Преобразование данных в DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    
    # Выбор функции потерь (CosineSimilarityLoss для задачи схожести предложений)
    train_loss = losses.CosineSimilarityLoss(model=model)
    
    # Создание evaluator для оценки качества на валидационной выборке
    evaluator = EmbeddingSimilarityEvaluator(
        sentences1=[example.texts[0] for example in eval_examples],
        sentences2=[example.texts[1] for example in eval_examples],
        scores=[example.label for example in eval_examples]
    )
    
    # Настройка параметров обучения
    num_epochs = 5
    warmup_steps = int(len(train_dataloader) * num_epochs * 0.1)  # 10% шагов для разогрева
    
    # Обучение модели
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=num_epochs,
        evaluation_steps=1000,
        warmup_steps=warmup_steps,
        output_path=output_dir,
        save_best_model=True
    )
    
    print(f"Модель успешно дообучена и сохранена в {output_dir}")
    return model

# Основной скрипт
if __name__ == "__main__":
    # Путь к файлу с данными
    file_path = "training models/mpnet/mpnet_train.csv"  # Укажите путь к вашему CSV файлу
    
    # Проверка существования файла
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found. Please check the path.")
    else:
        print(f"File '{file_path}' found. Proceeding...")
        
        # Шаг 1: Загрузка данных
        train_df, eval_df = load_data(file_path)
        
        # Шаг 2: Дообучение модели
        output_dir = "C:/python-models/fine_tuned_sentence_transformer"
        model = fine_tune_model(train_df, eval_df, output_dir)