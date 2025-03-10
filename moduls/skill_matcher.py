from sentence_transformers import SentenceTransformer, util
import torch
import logging
import gc

BATCH_SIZE = 64

class SkillMatcher:
    def __init__(self, device="cpu", model_path="C:/python-models/tuned_model_mpnet_v1"): #sentence-transformers/paraphrase-multilingual-mpnet-base-v2 #### C:/python-models/tuned_model_mpnet_v1
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

    def match_skills(self, program_skills, job_descriptions, BATCH_SIZE):
        try:
            if not program_skills or not job_descriptions:
                logging.warning("Нет данных для анализа навыков.")
                return {"sentence_transformer": {}}

            self._load_model()
            job_embeddings = self._encode_in_batches(job_descriptions, BATCH_SIZE)
            skill_embeddings = self._encode_in_batches(program_skills, BATCH_SIZE)

            similarity_results = {}
            for i in range(0, len(program_skills), BATCH_SIZE):
                batch_skills = program_skills[i:i + BATCH_SIZE]
                batch_embeddings = skill_embeddings[i:i + BATCH_SIZE]
                similarity_matrix = util.pytorch_cos_sim(batch_embeddings, job_embeddings)
                for j, skill in enumerate(batch_skills):
                    similarity_results[skill.strip()] = similarity_matrix[j].mean().item()

            return {"sentence_transformer": similarity_results}
        except Exception as e:
            logging.error(f"Ошибка вычисления сходства: {e}", exc_info=True)
            raise
        finally:
            self._cleanup_memory()

    def _encode_in_batches(self, texts, BATCH_SIZE):
        try:
            all_embeddings = []
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i:i + BATCH_SIZE]
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