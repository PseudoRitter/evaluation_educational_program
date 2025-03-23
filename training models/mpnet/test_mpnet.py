import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, ndcg_score, r2_score
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.metrics.pairwise import cosine_similarity
import os
import matplotlib.pyplot as plt
import logging
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, r2_score, roc_curve, precision_recall_curve, auc
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.metrics import ndcg_score

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mpnet_test.log"),  # Логи в файл
        logging.StreamHandler()                 # Логи в консоль
    ]
)
logger = logging.getLogger(__name__)

# Путь к модели
#model_path = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # или укажите локальный путь
model_path = "C:/python-models/tuned_model_mpnet_v1"

# Загрузка модели
try:
    if os.path.exists(model_path):
        model = SentenceTransformer(model_path)
        logger.info(f"Модель успешно загружена из локальной директории: {model_path}")
    else:
        logger.warning(f"Локальная директория {model_path} не найдена. Пытаемся загрузить модель из интернета...")
        model = SentenceTransformer(model_path)
        logger.info(f"Модель успешно загружена из интернета: {model_path}")
except Exception as e:
    logger.error(f"Ошибка при загрузке модели: {e}")
    exit(1)

# Функция для вычисления косинусного сходства между двумя эмбеддингами
def compute_cosine_similarity(embeddings1, embeddings2):
    similarities = []
    for emb1, emb2 in zip(embeddings1, embeddings2):
        sim = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]
        similarities.append(sim)
    return np.array(similarities)

# Функция для вычисления NDCG@k
def compute_ndcg_at_k(true_labels, predicted_scores, k):
    sorted_indices = np.argsort(predicted_scores)[::-1]
    true_labels_sorted = np.array(true_labels)[sorted_indices][:k]
    dcg = sum(true_labels_sorted[i] / np.log2(i + 2) for i in range(k))
    ideal_sorted_labels = np.sort(true_labels)[::-1][:k]
    idcg = sum(ideal_sorted_labels[i] / np.log2(i + 2) for i in range(k))
    if idcg == 0:
        return 0
    return dcg / idcg

# Загрузка данных
data_path = "training models/mpnet/mpnet_train.csv"
try:
    data = pd.read_csv(data_path)
    logger.info(f"Данные успешно загружены из {data_path}")
    logger.info(f"Первые 5 строк данных:\n{data.head().to_string()}")
except FileNotFoundError:
    logger.error(f"Файл {data_path} не найден.")
    exit(1)

# Преобразование данных и проверка на ошибки
sentences1 = data['sentence1'].tolist()
sentences2 = data['sentence2'].tolist()
labels = []

# Проверяем каждую строку столбца 'label' на корректность
for idx, value in enumerate(data['label']):
    try:
        label = float(value)  # Преобразуем в float
        labels.append(label)
    except (ValueError, TypeError):
        logger.error(f"Ошибка в строке {idx + 2} файла {data_path}: значение '{value}' не является числом.")
        logger.info(f"Sentence1: {sentences1[idx]}, Sentence2: {sentences2[idx]}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка в строке {idx + 2}: {e}")

# Проверка на NaN и некорректные значения
if not labels:  # Если labels пустой из-за ошибок
    logger.error("Все значения в столбце 'label' некорректны. Завершение программы.")
    exit(1)

labels = np.array(labels)
valid_indices = ~np.isnan(labels)
if not np.all(valid_indices):
    logger.warning(f"Обнаружены NaN значения в столбце 'label'. Удаляем строки с NaN (количество: {len(labels) - sum(valid_indices)})")
    sentences1 = [sentences1[i] for i in range(len(sentences1)) if valid_indices[i]]
    sentences2 = [sentences2[i] for i in range(len(sentences2)) if valid_indices[i]]
    labels = labels[valid_indices].tolist()

logger.info(f"Количество валидных строк после обработки: {len(labels)}")

# Генерация эмбеддингов
logger.info("Генерация эмбеддингов для первого набора предложений...")
embeddings1 = model.encode(sentences1, convert_to_numpy=True, show_progress_bar=True)
logger.info("Генерация эмбеддингов для второго набора предложений...")
embeddings2 = model.encode(sentences2, convert_to_numpy=True, show_progress_bar=True)

logger.info("Вычисление косинусного сходства...")
predicted_similarities = compute_cosine_similarity(embeddings1, embeddings2)
predicted_similarities = np.clip(predicted_similarities, 0, 1)

def compute_ndcg_at_k(true_labels, predicted_scores, k):
    sorted_indices = np.argsort(predicted_scores)[::-1]
    true_labels_sorted = np.array(true_labels)[sorted_indices][:k]
    dcg = sum(true_labels_sorted[i] / np.log2(i + 2) for i in range(k))
    ideal_sorted_labels = np.sort(true_labels)[::-1][:k]
    idcg = sum(ideal_sorted_labels[i] / np.log2(i + 2) for i in range(k))
    return dcg / idcg if idcg > 0 else 0

# Предполагается, что labels и predicted_similarities уже определены
# Вычисление метрик
pearson_corr, _ = pearsonr(labels, predicted_similarities)
spearman_corr, _ = spearmanr(labels, predicted_similarities)
mse = mean_squared_error(labels, predicted_similarities)
rmse = np.sqrt(mse)
mae = mean_absolute_error(labels, predicted_similarities)
kendall_corr, _ = kendalltau(labels, predicted_similarities)
true_relevance = np.array(labels).reshape(1, -1)
predicted_relevance = np.array(predicted_similarities).reshape(1, -1)
ndcg = ndcg_score(true_relevance, predicted_relevance)
bias = np.mean(np.array(labels) - np.array(predicted_similarities))
r2 = r2_score(labels, predicted_similarities)
ndcg_5 = compute_ndcg_at_k(labels, predicted_similarities, 5)
ndcg_10 = compute_ndcg_at_k(labels, predicted_similarities, 10)

# Дополнительные метрики для косинусного сходства
error_margin = 0.1
cosin_accuracy = np.mean(np.abs(np.array(labels) - np.array(predicted_similarities)) < error_margin)
mape = np.mean(np.abs((np.array(labels) - np.array(predicted_similarities)) / np.array(labels))) * 100

# Метрики классификации для разных порогов
thresholds = [0.3, 0.5, 0.7]
for threshold in thresholds:
    true_classes = [1 if label > threshold else 0 for label in labels]
    predicted_classes = [1 if pred > threshold else 0 for pred in predicted_similarities]
    accuracy = accuracy_score(true_classes, predicted_classes)
    precision = precision_score(true_classes, predicted_classes, zero_division=0)
    recall = recall_score(true_classes, predicted_classes, zero_division=0)
    f1 = f1_score(true_classes, predicted_classes, zero_division=0)
    roc_auc = roc_auc_score(true_classes, predicted_similarities)
    
    logger.info(f"\nМетрики классификации (порог={threshold}):")
    logger.info(f"Accuracy: {accuracy:.6f}")
    logger.info(f"Precision: {precision:.6f}")
    logger.info(f"Recall: {recall:.6f}")
    logger.info(f"F1-Score: {f1:.6f}")
    logger.info(f"ROC-AUC: {roc_auc:.6f}")

# Вывод результатов в логи
logger.info("\nРезультаты оценки качества модели:")
logger.info("\nМетрики, основанные на ошибках:")
logger.info(f"Корреляция Пирсона: {pearson_corr:.6f}")
logger.info(f"Корреляция Спирмена: {spearman_corr:.6f}")
logger.info(f"Mean Squared Error (MSE): {mse:.6f}")
logger.info(f"Root Mean Squared Error (RMSE): {rmse:.6f}")
logger.info(f"Mean Absolute Error (MAE): {mae:.6f}")
logger.info(f"R-squared: {r2:.6f}")
logger.info(f"Mean Bias: {bias:.6f}")
logger.info(f"Cosin Accuracy (error < {error_margin}): {cosin_accuracy:.6f}")
logger.info(f"Mean Absolute Percentage Error (MAPE): {mape:.6f}%")

logger.info("\nМетрики, основанные на ранжировании:")
logger.info(f"Kendall Tau: {kendall_corr:.6f}")
logger.info(f"Normalized Discounted Cumulative Gain (NDCG): {ndcg:.6f}")
logger.info(f"NDCG@5: {ndcg_5:.6f}")
logger.info(f"NDCG@10: {ndcg_10:.6f}")

# Визуализация ROC-кривой (для порога 0.5 как примера)
true_classes = [1 if label > 0.5 else 0 for label in labels]
fpr, tpr, _ = roc_curve(true_classes, predicted_similarities)
roc_auc = auc(fpr, tpr)
plt.plot(fpr, tpr, label=f"ROC-AUC = {roc_auc:.3f}")
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend()
plt.show()

# Precision-Recall кривая
precision, recall, _ = precision_recall_curve(true_classes, predicted_similarities)
pr_auc = auc(recall, precision)
plt.plot(recall, precision, label=f"PR-AUC = {pr_auc:.3f}")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve")
plt.legend()
plt.show()

# Визуализация ошибок
errors = np.array(labels) - np.array(predicted_similarities)
plt.hist(errors, bins=20, edgecolor='black')
plt.title("Distribution of Prediction Errors")
plt.xlabel("Error (True - Predicted)")
plt.ylabel("Frequency")
plt.show()

error_percentiles = np.percentile(np.abs(errors), [50, 75, 90, 95])
logger.info(f"\nАнализ распределения ошибок:")
logger.info(f"Median Absolute Error: {error_percentiles[0]:.6f}")
logger.info(f"75th Percentile of Absolute Error: {error_percentiles[1]:.6f}")
logger.info(f"90th Percentile of Absolute Error: {error_percentiles[2]:.6f}")
logger.info(f"95th Percentile of Absolute Error: {error_percentiles[3]:.6f}")

# Scatter plot
plt.scatter(labels, predicted_similarities, alpha=0.5)
plt.xlabel("Истинные оценки")
plt.ylabel("Предсказанные сходства")
plt.title("Истинные vs. Предсказанные сходства")
plt.plot([0, 1], [0, 1], color='red', linestyle='--')
plt.show()

# Bland-Altman plot
mean_values = (np.array(labels) + np.array(predicted_similarities)) / 2
diff_values = np.array(labels) - np.array(predicted_similarities)
plt.scatter(mean_values, diff_values, alpha=0.5)
plt.axhline(0, color='red', linestyle='--')
plt.xlabel("Среднее значение (True + Predicted) / 2")
plt.ylabel("Разница (True - Predicted)")
plt.title("Bland-Altman Plot")
plt.show()