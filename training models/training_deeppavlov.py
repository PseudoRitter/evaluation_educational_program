import os
import torch
import pandas as pd
import numpy as np  # Добавлено для работы с NumPy
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# 1. Загрузка данных через pandas
def load_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found. Please check the path.")
    
    # Чтение CSV файла
    df = pd.read_csv(file_path)
    
    # Проверка наличия столбца 'label'
    if "label" not in df.columns:
        raise ValueError("Column 'label' is missing in the dataset. Please ensure your CSV file has a 'label' column.")
    
    # Разделение на тренировочную и тестовую выборки
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)
    
    return train_df, eval_df

# 2. Токенизация данных
def tokenize_function(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["sentence"], 
        padding="max_length", 
        truncation=True, 
        max_length=128
    )
    # Преобразуем метки в список целых чисел
    if isinstance(examples["label"], list):
        tokenized_inputs["labels"] = [int(label) for label in examples["label"]]
    elif isinstance(examples["label"], (np.ndarray, pd.Series)):
        tokenized_inputs["labels"] = examples["label"].astype(int).tolist()
    else:
        raise ValueError(f"Unsupported type for labels: {type(examples['label'])}")
    return tokenized_inputs

# 3. Вычисление метрик
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": acc,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

# 4. Дообучение модели с поддержкой GPU
def fine_tune_model(train_df, eval_df, output_dir="C:/python-models/fine_tuned_model_v4"):
     # Проверка наличия GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Загрузка предобученной модели и токенизатора
    tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased-sentence")
    model = AutoModelForSequenceClassification.from_pretrained("DeepPavlov/rubert-base-cased", num_labels=2)
    model.to(device)  # Перемещение модели на GPU (если доступно)
    
    # Преобразование DataFrame в Dataset
    train_dataset = Dataset.from_pandas(train_df)
    eval_dataset = Dataset.from_pandas(eval_df)
    
    # Токенизация датасетов
    tokenized_train_dataset = train_dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    tokenized_eval_dataset = eval_dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    
    # Удаление лишних столбцов и форматирование данных
    tokenized_train_dataset = tokenized_train_dataset.remove_columns(["sentence", "label"])
    tokenized_eval_dataset = tokenized_eval_dataset.remove_columns(["sentence", "label"])
    tokenized_train_dataset.set_format("torch")
    tokenized_eval_dataset.set_format("torch")
    
    # Настройка параметров обучения
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        save_strategy="epoch",
        fp16=True if device == "cuda" else False,  
    )
    
    # Создание объекта Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train_dataset,
        eval_dataset=tokenized_eval_dataset,
        compute_metrics=compute_metrics
    )
    
    # Обучение модели
    trainer.train()
    
    # Сохранение модели
    model.save_pretrained(output_dir, safe_serialization=False)
    tokenizer.save_pretrained(output_dir)
    
    return model, tokenizer

# Основной скрипт
if __name__ == "__main__":
    # Путь к файлу с данными
    file_path = "training models/data_deeppavlov.csv" # Укажите путь к вашему CSV файлу
    
    # Проверка существования файла
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found. Please check the path.")
    else:
        print(f"File '{file_path}' found. Proceeding...")
        
        # Шаг 1: Загрузка данных
        train_df, eval_df = load_data(file_path)
        
        # Шаг 2: Дообучение модели
        output_dir = "C:/python-models/fine_tuned_model_v4"
        model, tokenizer = fine_tune_model(train_df, eval_df, output_dir)