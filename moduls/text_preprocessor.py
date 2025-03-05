import re
from razdel import sentenize
import torch
import numpy as np
import gc
import logging
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class TextPreprocessor:
    def __init__(self, model_path="C:/python-models/fine_tuned_model_v4"):
        self.model_path = os.path.normpath(model_path)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Директория {self.model_path} не существует.")
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"TextPreprocessor инициализирован для устройства: {self.device}")

    def initialize_model(self):
        """Публичный метод для явной инициализации модели и токенизатора."""
        self._load_model()

    def _load_model(self):
        """Ленивая загрузка модели и токенизатора."""
        if self.tokenizer is None or self.model is None:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                self.model.to(self.device)
                logging.info(f"Модель загружена на устройство: {self.device}")
            except Exception as e:
                logging.error(f"Ошибка загрузки модели: {e}", exc_info=True)
                raise ValueError(f"Не удалось загрузить модель из {self.model_path}")

    def remove_html_tags(self, text):
        banned_words = ['"', "</strong>", "<strong>", "</p>", "<p>", "</em>", "<em>", "</ol>", "<ol>",
                        "</div>", "<div>", "</h1>", "<h1>", "</h2>", "<h2>", "</ul>", "<ul>", "<b>", "</b>", "✅",
                        "</h3>", "<h3>", "<li>"]
        clean_text = text
        for word in banned_words:
            clean_text = clean_text.replace(word, ' ')
        return clean_text.strip()

    def remove_list_tags(self, text):
        try:
            return text.replace('</li>', '\n').replace('<br />', '\n')
        except Exception as e:
            logging.error(f"Ошибка удаления тегов: {e}", exc_info=True)
            return text

    def normalize_spaces(self, text):
        try:
            if not isinstance(text, str):
                logging.warning(f"Неверный тип данных: {type(text)}")
                return ""
            return ' '.join(text.split())
        except Exception as e:
            logging.error(f"Ошибка нормализации: {e}", exc_info=True)
            return ""

    def segment_text(self, text):
        try:
            return [s.text.strip() for s in sentenize(text) if s.text.strip()]
        except Exception as e:
            logging.error(f"Ошибка сегментации: {e}", exc_info=True)
            return []

    def filter_short_sentences(self, sentences, min_words=3):
        try:
            return [s for s in sentences if s.strip() and len(s.split()) >= min_words]
        except Exception as e:
            logging.error(f"Ошибка фильтрации: {e}", exc_info=True)
            return []

    def filter_sentences(self, sentences):
        return [s[:512] for s in sentences]

    def classify_sentences(self, sentences, batch_size=64, exclude_category_label=1):
        try:
            if not sentences:
                return [], []

            self._load_model()  # Убедимся, что модель загружена
            results = []
            filtered_sentences = []
            for i in range(0, len(sentences), batch_size):
                batch = sentences[i:i + batch_size]
                embeddings = self._encode_batch(batch)
                for embedding, sentence in zip(embeddings, batch):
                    label = np.argmax(embedding)
                    if label != exclude_category_label:
                        results.append((sentence, label))
                        filtered_sentences.append(sentence)
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            return results, filtered_sentences
        except Exception as e:
            logging.error(f"Ошибка классификации: {e}", exc_info=True)
            return [], []
        finally:
            # Очистка кэша GPU после классификации
            if self.device == "cuda":
                logging.info("Очистка кэша GPU после классификации...")
                self.model.to("cpu")  # Перемещаем модель на CPU
                del self.model       # Удаляем модель из памяти
                gc.collect()         # Вызываем сборщик мусора
                torch.cuda.empty_cache()  # Очищаем кэш GPU

    def _encode_batch(self, batch):
        try:
            inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=128).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            return outputs.logits.cpu().numpy()
        except Exception as e:
            logging.error(f"Ошибка кодирования пакета: {e}", exc_info=True)
            return np.array([])

