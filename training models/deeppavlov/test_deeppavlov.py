import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.metrics import (precision_score, recall_score, f1_score, accuracy_score,
                            mean_squared_error, mean_absolute_error, r2_score,
                            confusion_matrix, roc_auc_score)
from scipy.stats import pearsonr, spearmanr, kendalltau
import numpy as np
from torch.nn.functional import cross_entropy
from sklearn.metrics import ndcg_score
import matplotlib.pyplot as plt
import os

# Функция для вычисления NDCG@k
def compute_ndcg_at_k(true_labels, predictions, k):
    order = np.argsort(predictions)[::-1]
    true_labels = np.array(true_labels)[order[:k]]
    return ndcg_score([true_labels], [np.ones(k)], k=k)

# 1. Проверка наличия GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 2. Загрузка модели и токенизатора
model_path = "C:/python-models/tuned_model_deeppavlov_v1"  # Можно заменить на "DeepPavlov/rubert-base-cased-sentence"
#model_path = "DeepPavlov/rubert-base-cased-sentence"

# Проверка, является ли model_path локальным путем или названием модели
if os.path.exists(model_path):
    print(f"Загружаем локальную модель из: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
else:
    print(f"Загружаем модель из Hugging Face: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    # Примечание: если модель изначально не обучена для классификации,
    # может потребоваться настройка выходного слоя
    num_labels = 2  # Предполагаем бинарную классификацию
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=num_labels)

model.to(device)

# 3. Чтение данных из CSV
csv_file = "training models/deeppavlov/deeppavlov_test.csv"
data = pd.read_csv(csv_file)
sentences = data["sentence"].tolist()
true_labels = data["label"].tolist()

# 4. Токенизация данных
inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt", max_length=512)
inputs = {key: val.to(device) for key, val in inputs.items()}

# 5. Предсказания с использованием GPU
model.eval()
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=-1)[:, 1].cpu().tolist()
    predictions = torch.argmax(logits, dim=-1).cpu().tolist()

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
true_labels_tensor = torch.tensor(true_labels).to(device)
loss = cross_entropy(logits, true_labels_tensor).item()

# Дополнительные метрики
pearson_corr, _ = pearsonr(true_labels, probabilities)
spearman_corr, _ = spearmanr(true_labels, probabilities)
rmse = np.sqrt(mse)
kendall_corr, _ = kendalltau(true_labels, probabilities)
true_relevance = np.array(true_labels).reshape(1, -1)
predicted_relevance = np.array(probabilities).reshape(1, -1)
ndcg = ndcg_score(true_relevance, predicted_relevance)
bias = np.mean(np.array(true_labels) - np.array(probabilities))

threshold = 0.5
true_classes = [1 if label > threshold else 0 for label in true_labels]
predicted_classes = [1 if pred > threshold else 0 for pred in probabilities]

roc_auc = roc_auc_score(true_classes, probabilities)
ndcg_5 = compute_ndcg_at_k(true_labels, probabilities, 5)
ndcg_10 = compute_ndcg_at_k(true_labels, probabilities, 10)

# 7. Вывод результатов
print(f"Точность (Accuracy): {accuracy:.6f}")
print(f"Precision: {precision:.6f}")
print(f"Recall (Полнота): {recall:.6f}")
print(f"F1-Score: {f1:.6f}")
print(f"Среднеквадратичная ошибка (MSE): {mse:.6f}")
print(f"Корень из MSE (RMSE): {rmse:.6f}")
print(f"Средняя абсолютная ошибка (MAE): {mae:.6f}")
print(f"Коэффициент детерминации (R²): {r2:.6f}")
print(f"Функция потерь (Cross-Entropy Loss): {loss:.6f}")
print(f"Корреляция Пирсона: {pearson_corr:.6f}")
print(f"Корреляция Спирмена: {spearman_corr:.6f}")
print(f"Корреляция Кендалла: {kendall_corr:.6f}")
print(f"NDCG: {ndcg:.6f}")
print(f"NDCG@5: {ndcg_5:.6f}")
print(f"NDCG@10: {ndcg_10:.6f}")
print(f"Среднее смещение (Bias): {bias:.6f}")
print(f"ROC-AUC: {roc_auc:.6f}")

# 8. Confusion Matrix
cm = confusion_matrix(true_labels, predictions)
print("\nConfusion Matrix:")
print(cm)

# 9. Визуализация
# Гистограмма ошибок
errors = np.array(true_labels) - np.array(probabilities)
plt.hist(errors, bins=20, edgecolor='black')
plt.title("Distribution of Prediction Errors")
plt.xlabel("Error (True - Predicted)")
plt.ylabel("Frequency")
plt.show()

# Анализ перцентилей ошибок
error_percentiles = np.percentile(np.abs(errors), [50, 75, 90, 95])
print(f"\nАнализ распределения ошибок:")
print(f"Медиана абсолютной ошибки: {error_percentiles[0]:.6f}")
print(f"75-й перцентиль абсолютной ошибки: {error_percentiles[1]:.6f}")
print(f"90-й перцентиль абсолютной ошибки: {error_percentiles[2]:.6f}")
print(f"95-й перцентиль абсолютной ошибки: {error_percentiles[3]:.6f}")

# Scatter plot
plt.scatter(true_labels, probabilities, alpha=0.5)
plt.xlabel("Истинные оценки")
plt.ylabel("Предсказанные вероятности")
plt.title("Истинные vs. Предсказанные значения")
plt.plot([0, 1], [0, 1], color='red', linestyle='--')
plt.show()