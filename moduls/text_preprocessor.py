from razdel import sentenize
import torch
import numpy as np
import gc
import logging
import os
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class TextPreprocessor:
    def __init__(self, model_path="C:/python-models/tuned_model_deeppavlov_v1"):
    #def __init__(self, model_path="python-models/tuned_model_deeppavlov_v1"):

        self.model_path = os.path.normpath(model_path)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Директория {self.model_path} не существует.")
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"TextPreprocessor инициализирован для устройства: {self.device}")

    def initialize_model(self):
        self._load_model()

    def _load_model(self):
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
        banned_words = ["<strong>", "</strong>", "<em>", "</em>", "/<em>",
                        "<span>", "</span>", "<i>", "</i>", "</ol>", "<ol>",
                        "<div>", "</div>", "<ul>", "</ul>", "<b>", "</b>",
                        "<s>", "</s>", "&quot;", "<p></p>", "<p> </p>"]
        clean_text = text
        for word in banned_words:
            clean_text = clean_text.replace(word, "")
        return clean_text.strip()
    
    def remove_header(self, text):
        pattern = r'<h[1-6][^>]*>.*?(</h[1-6]>|/>|$)'
        cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
        return cleaned_text

    def remove_list_tags(self, text):
        try:
            def add_punctuation(text_segment):
                stripped = text_segment.strip()
                if stripped and not stripped.endswith(('.', ';')):
                    return stripped + '.'
                return stripped

            li_pattern = r'<li>(.*?)</li>'
            li_matches = re.finditer(li_pattern, text, re.DOTALL)
            
            for match in li_matches:
                content = match.group(1).strip()
                if content:
                    cleaned_content = add_punctuation(content)
                    text = text.replace(match.group(0), cleaned_content + ' ')

            text = text.replace('<li>', '').replace('</li>', '')

            parts = text.split('<br />')
            cleaned_parts = []
            for part in parts:
                cleaned_part = add_punctuation(part)
                cleaned_parts.append(cleaned_part)
            text = ' '.join(cleaned_parts)

            p_pattern = r'<p>(.*?)</p>'
            p_matches = re.finditer(p_pattern, text, re.DOTALL)
            
            for match in p_matches:
                content = match.group(1).strip()
                if content:
                    cleaned_content = add_punctuation(content)
                    text = text.replace(match.group(0), cleaned_content + ' ')

            text = text.replace('<p>', '').replace('</p>', '')
            text = self.normalize_spaces(text)
            return text
        except Exception as e:
            logging.error(f"Ошибка удаления тегов: {e}", exc_info=True)
            return text

    def normalize_spaces(self, text):
        try:
            if not isinstance(text, str):
                logging.warning(f"Неверный тип данных: {type(text)}")
                return ""
            return " ".join(text.split())
        except Exception as e:
            logging.error(f"Ошибка нормализации: {e}", exc_info=True)
            return ""

    def segment_text(self, text):
        try:
            return [s.text.strip() for s in sentenize(text) if s.text.strip()]
        except Exception as e:
            logging.error(f"Ошибка сегментации: {e}", exc_info=True)
            return []

    def filter_short_sentences(self, sentences, min_words=0, max_words=10):
        try:
            result = []
            for sentence in sentences:
                cleaned_sentence = sentence.strip()
                if not cleaned_sentence:
                    continue
                
                words = cleaned_sentence.split()
                word_count = len(words)
                
                if word_count < min_words:
                    continue
                
                if word_count <= max_words:
                    result.append(cleaned_sentence)
                else:
                    num_parts = (word_count + max_words - 1) // max_words
                    part_size = word_count // num_parts
                    start_idx = 0
                    for i in range(num_parts):
                        end_idx = start_idx + part_size
                        if i == num_parts - 1:
                            end_idx = word_count
                        
                        part_words = words[start_idx:end_idx]
                        part_text = " ".join(part_words)
                        
                        if i < num_parts - 1 and not part_text.endswith(('.', ';')):
                            part_text += ';'

                        result.append(part_text)
                        start_idx = end_idx
            
            return result
        except Exception as e:
            logging.error(f"Ошибка фильтрации и разделения: {e}", exc_info=True)
            return []

    def filter_sentences(self, sentences):
        return [s[:1024] for s in sentences]

    def classify_sentences(self, sentences, batch_size, exclude_category_label=1, stop_flag=False):
        try:
            if not sentences:
                return [], []

            self._load_model()
            if stop_flag:
                logging.info("Анализ принудительно остановлен перед классификацией предложений.")
                return [], []

            results = []
            filtered_sentences = []
            for i in range(0, len(sentences), batch_size):
                if stop_flag:
                    logging.info("Анализ принудительно остановлен во время классификации батча.")
                    return results, filtered_sentences
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
            if self.device == "cuda":
                logging.info("Очистка кэша GPU после классификации...")
                self.model.to("cpu")
                del self.model
                self.model = None
                gc.collect()
                torch.cuda.empty_cache()

    def _encode_batch(self, batch):
        try:
            inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=128).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            return outputs.logits.cpu().numpy()
        except Exception as e:
            logging.error(f"Ошибка кодирования пакета: {e}", exc_info=True)
            return np.array([])