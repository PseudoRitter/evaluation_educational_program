import os
import torch
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# 1. Загрузка данных из CSV файлов
def load_data_from_files(train_path, val_path, test_path):
    datasets = [(train_path, "train"), (val_path, "validation"), (test_path, "test")]
    for path, name in datasets:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' not found. Please check the path.")
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    for df, (path, name) in zip([train_df, val_df, test_df], datasets):
        if "label" not in df.columns:
            raise ValueError(f"Column 'label' is missing in the {name} dataset ({path}).")
        for idx, label in df["label"].items():
            try:
                int(label)
            except (ValueError, TypeError):
                print(f"Error in {name} dataset ({path}):")
                print(f"Row {idx}: Unable to convert '{label}' to integer")
                print(f"Full row content: {df.iloc[idx].to_dict()}")
                raise ValueError(f"Invalid label found in {name} dataset ({path}). All labels must be numeric.")
    
    return train_df, val_df, test_df

# 2. Токенизация данных
def tokenize_function(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["sentence"], 
        padding="max_length", 
        truncation=True, 
        max_length=128
    )
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

# 4. Дообучение модели с сохранением только последней модели
def fine_tune_model(train_df, val_df, test_df, output_dir="C:/python-models/fine_tuned_model_v5"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased-sentence")
    model = AutoModelForSequenceClassification.from_pretrained("DeepPavlov/rubert-base-cased", num_labels=2)
    model.to(device)
    
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    test_dataset = Dataset.from_pandas(test_df)
    
    tokenized_train_dataset = train_dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    tokenized_val_dataset = val_dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    tokenized_test_dataset = test_dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    
    tokenized_train_dataset = tokenized_train_dataset.remove_columns(["sentence", "label"])
    tokenized_val_dataset = tokenized_val_dataset.remove_columns(["sentence", "label"])
    tokenized_test_dataset = tokenized_test_dataset.remove_columns(["sentence", "label"])
    tokenized_train_dataset.set_format("torch")
    tokenized_val_dataset.set_format("torch")
    tokenized_test_dataset.set_format("torch")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",  # Оцениваем на валидационной выборке после каждой эпохи
        per_device_train_batch_size=64,
        per_device_eval_batch_size=64,
        num_train_epochs=25,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        save_strategy="no",  # Отключаем сохранение чекпоинтов во время обучения
        fp16=True if device == "cuda" else False,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train_dataset,
        eval_dataset=tokenized_val_dataset,
        compute_metrics=compute_metrics
    )
    
    trainer.train()
    
    test_results = trainer.evaluate(tokenized_test_dataset)
    print("Test set results:", test_results)
    
    # Сохранение только последней модели
    model.save_pretrained(output_dir, safe_serialization=False)
    tokenizer.save_pretrained(output_dir)
    
    return model, tokenizer

# Основной скрипт
if __name__ == "__main__":
    train_path = "training models/deeppavlov/deeppavlov_train.csv"
    val_path = "training models/deeppavlov/deeppavlov_valid.csv"
    test_path = "training models/deeppavlov/deeppavlov_test.csv"
    
    missing_files = [path for path in [train_path, val_path, test_path] if not os.path.exists(path)]
    if missing_files:
        print(f"Error: The following files were not found: {', '.join(missing_files)}. Please check the paths.")
    else:
        print(f"All files found. Proceeding...")
        
        train_df, val_df, test_df = load_data_from_files(train_path, val_path, test_path)
        output_dir = "/content/drive/MyDrive/train_model/fine_tuned_model_v5"
        model, tokenizer = fine_tune_model(train_df, val_df, test_df, output_dir)