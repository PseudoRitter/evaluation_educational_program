import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader
import torch
import os
import sentence_transformers
import transformers

print(f"Версия sentence-transformers: {sentence_transformers.__version__}")
print(f"Версия transformers: {transformers.__version__}")

def parse_label(label):
    """Универсальный парсер меток"""
    try:
        label_str = str(label).strip().replace(',', '.')
        cleaned = ''.join(c for c in label_str if c.isdigit() or c in ['.', '-'])
        value = float(cleaned)
        return min(max(abs(value), 0.0), 1.0)
    except ValueError:
        print(f"Некорректный формат метки: '{label}'")
        return None

def load_data(file_path, dataset_type="train"):
    try:
        df = pd.read_csv(file_path, usecols=[0, 1, 2], 
                         names=['sentence1', 'sentence2', 'label'], 
                         header=0, 
                         dtype={'label': str})
    except pd.errors.ParserError as e:
        print(f"Ошибка парсинга {dataset_type} CSV: {e}")
        df = pd.read_csv(file_path, usecols=[0, 1, 2], 
                         names=['sentence1', 'sentence2', 'label'], 
                         header=0, 
                         on_bad_lines='skip', 
                         dtype={'label': str})

    df['sentence1'] = df['sentence1'].fillna('').astype(str)
    df['sentence2'] = df['sentence2'].fillna('').astype(str)

    examples = []
    for _, row in df.iterrows():
        label = parse_label(row['label'])
        
        if label is None:
            print(f"Пропущена некорректная метка в {dataset_type}: {row['label']}")
            continue
            
        if row['sentence1'].strip() and row['sentence2'].strip():
            examples.append(InputExample(
                texts=[row['sentence1'], row['sentence2']], 
                label=label
            ))
        else:
            print(f"Пропущена строка с пустыми предложениями в {dataset_type}")
            
    return examples

def create_similarity_evaluator(examples, name):
    """Создает оценщика для регрессии схожести"""
    sentences1 = []
    sentences2 = []
    scores = []
    for example in examples:
        sentences1.append(example.texts[0])
        sentences2.append(example.texts[1])
        scores.append(example.label)
        
    return evaluation.EmbeddingSimilarityEvaluator(
        sentences1, 
        sentences2, 
        scores,
        name=name,
        show_progress_bar=True,
        batch_size=16
    )

def train_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Используемое устройство: {device}")

    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2').to(device)
    
    # Загрузка данных
    train_data = load_data('training models/обучающая выборка.csv', 'train')
    dev_data = load_data('training models/валидационная выборка.csv', 'validation')
    test_data = load_data('training models/тестовая выборка.csv', 'test')

    print(f"Размеры наборов данных:")
    print(f"  Обучение: {len(train_data)}")
    print(f"  Валидация: {len(dev_data)}")
    print(f"  Тест: {len(test_data)}")

    # Создание DataLoader
    train_dataloader = DataLoader(train_data, shuffle=True, batch_size=16)
    train_loss = losses.CosineSimilarityLoss(model).to(device)
    
    # Создание оценщиков
    dev_evaluator = create_similarity_evaluator(dev_data, 'validation')
    test_evaluator = create_similarity_evaluator(test_data, 'test')

    # Параметры обучения
    output_dir = 'C:/python-models/tuned_model_mpnet_similarity'
    os.makedirs(output_dir, exist_ok=True)
    
    # Начало обучения
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=dev_evaluator,
        epochs=6,
        warmup_steps=100,
        output_path=output_dir,
        save_best_model=True,
        optimizer_params={'lr': 2e-5},
        evaluation_steps=500,
        checkpoint_save_steps=1000,
        checkpoint_save_total_limit=3,
        callback=lambda score, epoch, steps: print(f"[Эпоха {epoch} шаг {steps}] Текущий скор: {score:.4f}")
    )
    
    # Финальная оценка
    test_metrics = test_evaluator(model, output_path=output_dir)
    
    # Вывод всех метрик
    print("\nФинальные результаты на тестовом наборе:")
    for metric, value in test_metrics.items():
        print(f"  {metric.upper()}: {value:.4f}")

if __name__ == '__main__':
    print("Начинаем обучение модели...")
    train_model()
    print("Обучение завершено! Модель сохранена в:", 'C:/python-models/tuned_model_mpnet_similarity')