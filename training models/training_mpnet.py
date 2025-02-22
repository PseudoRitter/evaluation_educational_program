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
    num_epochs = 3
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
    file_path = "training/data_mpnet.csv"  # Укажите путь к вашему CSV файлу
    
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