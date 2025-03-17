import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics.pairwise import cosine_similarity
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, ndcg_score
from scipy.stats import pearsonr, spearmanr, kendalltau
import matplotlib.pyplot as plt


model_path = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # или укажите локальный путь
#model_path = "C:/python-models/tuned_model_mpnet_v1"


# Загрузка модели
try:
    if os.path.exists(model_path):
        model = SentenceTransformer(model_path)
        print(f"Модель успешно загружена из локальной директории: {model_path}")
    else:
        print(f"Локальная директория {model_path} не найдена. Пытаемся загрузить модель из интернета...")
        model = SentenceTransformer(model_path)
        print(f"Модель успешно загружена из интернета: {model_path}")
except Exception as e:
    print(f"Ошибка при загрузке модели: {e}")
    exit(1)

# Функция для вычисления косинусного сходства между двумя эмбеддингами
def compute_cosine_similarity(embeddings1, embeddings2):
    similarities = []
    for emb1, emb2 in zip(embeddings1, embeddings2):
        sim = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]
        similarities.append(sim)
    return np.array(similarities)

# Загрузка данных
data_path = "training models/mpnet_test.csv"
try:
    data = pd.read_csv(data_path)
    print(f"Данные успешно загружены из {data_path}")
except FileNotFoundError:
    print(f"Ошибка: Файл {data_path} не найден.")
    exit(1)

sentences1 = data['sentence1'].tolist()
sentences2 = data['sentence2'].tolist()
labels = data['label'].tolist()

# Получение эмбеддингов для всех предложений
print("\nГенерация эмбеддингов для первого набора предложений...")
embeddings1 = model.encode(sentences1, convert_to_numpy=True, show_progress_bar=True)
print("Генерация эмбеддингов для второго набора предложений...")
embeddings2 = model.encode(sentences2, convert_to_numpy=True, show_progress_bar=True)

# Вычисление косинусного сходства между эмбеддингами
print("\nВычисление косинусного сходства...")
predicted_similarities = compute_cosine_similarity(embeddings1, embeddings2)

# Убедимся, что предсказанные значения находятся в диапазоне [0, 1]
predicted_similarities = np.clip(predicted_similarities, 0, 1)

# Вычисление метрик
# 1. Корреляция Пирсона
pearson_corr, _ = pearsonr(labels, predicted_similarities)
# 2. Корреляция Спирмена
spearman_corr, _ = spearmanr(labels, predicted_similarities)
# 3. Mean Squared Error
mse = mean_squared_error(labels, predicted_similarities)
# 4. Root Mean Squared Error
rmse = np.sqrt(mse)
# 5. Mean Absolute Error
mae = mean_absolute_error(labels, predicted_similarities)
# 6. Kendall Tau
kendall_corr, _ = kendalltau(labels, predicted_similarities)
# 7. NDCG
true_relevance = np.array(labels).reshape(1, -1)
predicted_relevance = np.array(predicted_similarities).reshape(1, -1)
ndcg = ndcg_score(true_relevance, predicted_relevance)
# 8. Mean Bias
bias = np.mean(np.array(labels) - np.array(predicted_similarities))
# 9. Метрики классификации (с порогом 0.5)
threshold = 0.5
true_classes = [1 if label > threshold else 0 for label in labels]
predicted_classes = [1 if pred > threshold else 0 for pred in predicted_similarities]
accuracy = accuracy_score(true_classes, predicted_classes)
precision = precision_score(true_classes, predicted_classes)
recall = recall_score(true_classes, predicted_classes)
f1 = f1_score(true_classes, predicted_classes)
roc_auc = roc_auc_score(true_classes, predicted_similarities)

# Вывод результатов
print("\nРезультаты оценки качества модели:")
print("\nМетрики, основанные на ошибках:")
print(f"Корреляция Пирсона: {pearson_corr:.6f}")
print(f"Корреляция Спирмена: {spearman_corr:.6f}")
print(f"Mean Squared Error (MSE): {mse:.6f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.6f}")
print(f"Mean Absolute Error (MAE): {mae:.6f}")
print(f"Mean Bias: {bias:.6f}")

print("\nМетрики, основанные на ранжировании:")
print(f"Kendall Tau: {kendall_corr:.6f}")
print(f"Normalized Discounted Cumulative Gain (NDCG): {ndcg:.6f}")

print(f"\nМетрики классификации (порог={threshold}):")
print(f"Accuracy: {accuracy:.6f}")
print(f"Precision: {precision:.6f}")
print(f"Recall: {recall:.6f}")
print(f"F1-Score: {f1:.6f}")
print(f"ROC-AUC: {roc_auc:.6f}")

# Анализ распределения ошибок
errors = np.array(labels) - np.array(predicted_similarities)
plt.hist(errors, bins=20, edgecolor='black')
plt.title("Distribution of Prediction Errors")
plt.xlabel("Error (True - Predicted)")
plt.ylabel("Frequency")
plt.show()
error_percentiles = np.percentile(np.abs(errors), [50, 75, 90, 95])
print(f"\nАнализ распределения ошибок:")
print(f"Median Absolute Error: {error_percentiles[0]:.6f}")
print(f"75th Percentile of Absolute Error: {error_percentiles[1]:.6f}")
print(f"90th Percentile of Absolute Error: {error_percentiles[2]:.6f}")
print(f"95th Percentile of Absolute Error: {error_percentiles[3]:.6f}")