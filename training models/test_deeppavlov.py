import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from torch.nn.functional import cross_entropy

# 1. Проверка наличия GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 2. Загрузка модели и токенизатора
model_path = "C:/python-models/fine_tuned_model_v4"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.to(device)  # Перемещение модели на GPU (если доступно)

# 3. Чтение данных из CSV
csv_file = "training models/test_deeppavlov.csv"  # Укажите имя вашего файла
data = pd.read_csv(csv_file)
sentences = data["sentence"].tolist()  # Исправьте на "sentence", если в файле нет опечатки
true_labels = data["label"].tolist()

# 4. Токенизация данных
inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt", max_length=512)
inputs = {key: val.to(device) for key, val in inputs.items()}  # Перемещение токенизированных данных на GPU

# 5. Предсказания с использованием GPU
model.eval()
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=-1)[:, 1].cpu().tolist()  # Вероятности класса 1, перенос на CPU для метрик
    predictions = torch.argmax(logits, dim=-1).cpu().tolist()  # Бинарные предсказания, перенос на CPU

# 6. Вычисление метрик
# Бинарные метрики
accuracy = accuracy_score(true_labels, predictions)
precision = precision_score(true_labels, predictions)
recall = recall_score(true_labels, predictions)
f1 = f1_score(true_labels, predictions)

# Метрики на основе вероятностей
mse = mean_squared_error(true_labels, probabilities)
mae = mean_absolute_error(true_labels, probabilities)
r2 = r2_score(true_labels, probabilities)

# Функция потерь (кросс-энтропия)
true_labels_tensor = torch.tensor(true_labels).to(device)  # Метки на GPU
loss = cross_entropy(logits, true_labels_tensor).item()  # Потери вычисляются на GPU, затем переносим результат

# 7. Вывод результатов
print(f"Точность (Accuracy): {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall (Полнота): {recall:.4f}")
print(f"F1-Score: {f1:.4f}")
print(f"Среднеквадратичная ошибка (MSE): {mse:.4f}")
print(f"Средняя абсолютная ошибка (MAE): {mae:.4f}")
print(f"Коэффициент детерминации (R²): {r2:.4f}")
print(f"Функция потерь (Cross-Entropy Loss): {loss:.4f}")

# 8. Confusion Matrix (опционально, для наглядности)
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(true_labels, predictions)
print("\nConfusion Matrix:")
print(cm)