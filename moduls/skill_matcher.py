from sentence_transformers import SentenceTransformer, util
import torch
import logging
import gc
import numpy as np

class SkillMatcher:
    def __init__(self, device="cpu", model_path="C:/python-models/tuned_model_mpnet_v12"):
        self.device = device
        self.model_path = model_path
        self.model = None
        logging.info(f"SkillMatcher инициализирован для устройства: {self.device}")

    def initialize_model(self):
        self._load_model()

    def _load_model(self):
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_path)
                self.model.to(self.device)
                logging.info(f"Модель из {self.model_path} загружена на {self.device}")
            except Exception as e:
                logging.error(f"Ошибка загрузки модели: {e}", exc_info=True)
                raise

    def match_skills(self, program_skills, job_descriptions, batch_size, threshold=0.5):
        try:
            if not program_skills or not job_descriptions:
                logging.warning("Нет данных для анализа навыков.")
                return {"sentence_transformer": {}, "frequencies": {}}

            self._load_model()
            job_embeddings = self._encode_in_batches(job_descriptions, batch_size)
            skill_embeddings = self._encode_in_batches(program_skills, batch_size)

            similarity_results = {}
            frequency_results = {}
            for i in range(0, len(program_skills), batch_size):
                batch_skills = program_skills[i:i + batch_size]
                batch_embeddings = skill_embeddings[i:i + batch_size]
                similarity_matrix = util.pytorch_cos_sim(batch_embeddings, job_embeddings)
                for j, skill in enumerate(batch_skills):
                    similarities = similarity_matrix[j].cpu().numpy()
                    mean_similarity = similarities.mean().item()
                    frequency = np.sum(similarities >= threshold)  # Используем настраиваемый порог
                    similarity_results[skill.strip()] = mean_similarity
                    frequency_results[skill.strip()] = int(frequency)

            logging.debug(f"Порог для частот: {threshold}")
            return {"sentence_transformer": similarity_results, "frequencies": frequency_results}
        except Exception as e:
            logging.error(f"Ошибка вычисления сходства: {e}", exc_info=True)
            raise
        finally:
            self._cleanup_memory()

    def _encode_in_batches(self, texts, batch_size):
        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                if not batch:
                    continue
                embeddings = self.model.encode(batch, convert_to_tensor=True, device=self.device, show_progress_bar=False)
                all_embeddings.append(embeddings)
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            return torch.cat(all_embeddings, dim=0) if all_embeddings else torch.tensor([], device=self.device)
        except Exception as e:
            logging.error(f"Ошибка кодирования: {e}", exc_info=True)
            raise

    def _cleanup_memory(self):
        if self.device == "cuda":
            logging.info("Очистка кэша GPU в SkillMatcher...")
            gc.collect()
            torch.cuda.empty_cache()