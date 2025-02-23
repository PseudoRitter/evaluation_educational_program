import re
from razdel import sentenize
import torch
import numpy as np
import gc
import logging
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Функция для вычисления косинусного сходства
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class TextPreprocessor:
    def __init__(self, model_path="C:/python-models/fine_tuned_model_v4"):
        try:
            model_path = os.path.normpath(model_path)
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Директория {model_path} не существует.")

            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logging.info(f"Модель загружена на устройство: {self.device}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке модели: {e}", exc_info=True)
            raise ValueError(f"Не удалось загрузить модель из {model_path}. Проверьте путь.")

    def remove_html_tags(self, text):
        banned_words = ['&quot', "</strong>", "<strong>", "</p>", "<p>", "</em>", "<em>", "</ol>", "<ol>",
                        "</div>", "<div>", "</h1>", "<h1>", "</h2>", "<h2>", "</ul>", "<ul>", "<b>", "</b>", "✅",
                        "</h3>", "<h3>", "<li>"]
        clean_text = text
        for word in banned_words:
            clean_text = re.sub(re.escape(word), ' ', clean_text)
        return clean_text.strip()

    def remove_list_tags(self, text):  # Исправлено название метода
        try:
            text = re.sub(r'</li>', '\n', text)
            text = re.sub(r'<br />', '\n', text)
            return text  
        except Exception as e:
            logging.error(f"Ошибка при удалении тегов списков: {e}", exc_info=True)
            return text  # Возвращаем исходный текст в случае ошибки

    def normalize_spaces(self, text):
        try:
            if not isinstance(text, str):
                logging.warning(f"Получен неверный тип данных: {type(text)}. Возвращаем пустую строку.")
                return ""
            normalized_text = re.sub(r'\s+', ' ', text).strip()
            return normalized_text
        except Exception as e:
            logging.error(f"Ошибка при нормализации пробелов: {e}", exc_info=True)
            return ""

    def segment_text(self, text):
        try:
            sentences = [s.text.strip() for s in sentenize(text) if s.text.strip()]
            return sentences
        except Exception as e:
            logging.error(f"Ошибка при сегментации текста: {e}", exc_info=True)
            return []  

    def filter_short_sentences(self, sentences, min_words=3):
        """Фильтрует предложения, удаляя короткие (менее min_words слов) и пустые"""
        try:
            filtered_sentences = [
                sentence for sentence in sentences
                if sentence.strip() and len(sentence.split()) >= min_words
            ]
            return filtered_sentences
        except Exception as e:
            logging.error(f"Ошибка при фильтрации предложений: {e}", exc_info=True)
            return []  

    def filter_sentences(self, sentences):
        """Ограничивает длину каждого предложения до 512 символов."""
        return [sentence[:512] for sentence in sentences]

    def classify_sentences(self, sentences, batch_size=32, exclude_category_label=1):
        try:
            results = []
            filtered_sentences = []
            sentence_embeddings = self._encode_in_batches(sentences, batch_size)
            for sentence_embedding, sentence in zip(sentence_embeddings, sentences):
                label = np.argmax(sentence_embedding)
                if label == exclude_category_label: #выбор какую категорию исключать != о компании/условия работы; == нунжное
                    results.append((sentence, label))
                    filtered_sentences.append(sentence)
            return results, filtered_sentences
        except Exception as e:
            logging.error(f"Ошибка при классификации предложений: {e}", exc_info=True)
            return [], []  
        finally:
            if self.device == "cuda":
                logging.info("Очистка кэша GPU после классификации...")
                self.model.to("cpu")
                del self.model
                gc.collect()
                torch.cuda.empty_cache()

    def _encode_in_batches(self, texts, batch_size):
        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                if not batch:
                    continue
                inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=128).to(self.device)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                embeddings = outputs.logits.cpu().numpy()
                all_embeddings.extend(embeddings)
            return np.array(all_embeddings)
        except Exception as e:
            logging.error(f"Ошибка при кодировании текстов: {e}", exc_info=True)
            return np.array([])  # Возвращаем пустой массив в случае ошибки