from sentence_transformers import SentenceTransformer, util
import torch
import logging
import gc

class SkillMatcher:
    def __init__(self, device="cpu"):
        try:
            self.device = device
            model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            #model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            self.model = SentenceTransformer(model_name)
            self.model.to(self.device)
            logging.info(f"SkillMatcher модель загружена на устройство: {self.device}")
        except Exception as e:
            logging.error(f"Ошибка при инициализации SkillMatcher: {e}", exc_info=True)
            raise

    def match_skills(self, program_skills, job_descriptions, batch_size=64):
        try:
            if not program_skills or not job_descriptions:
                logging.warning("Нет данных для анализа схожести навыков.")
                return {"sentence_transformer": {}}

            job_embeddings = self._encode_in_batches(job_descriptions, batch_size).to(self.device)
            skill_embeddings = self._encode_in_batches(program_skills, batch_size).to(self.device)
            similarity_matrix = util.pytorch_cos_sim(skill_embeddings, job_embeddings)

            results = {}
            for i, skill in enumerate(program_skills):
                avg_similarity = similarity_matrix[i].mean().item()
                results[skill.strip()] = avg_similarity

            return {"sentence_transformer": results}
        except Exception as e:
            logging.error(f"Ошибка при вычислении схожести навыков: {e}", exc_info=True)
            raise
        finally:
            # Очистка кэша GPU после классификации
            if self.device == "cuda":
                logging.info("Очистка кэша GPU после классификации...")
                self.model.to("cpu")  # Перемещаем модель на CPU
                del self.model       # Удаляем модель из памяти
                gc.collect()         # Вызываем сборщик мусора
                torch.cuda.empty_cache()  # Очищаем кэш GPU

    def _encode_in_batches(self, texts, batch_size):
        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                if not batch:
                    continue
                embeddings = self.model.encode(batch, convert_to_tensor=True)
                all_embeddings.append(embeddings)
            return torch.cat(all_embeddings, dim=0) if all_embeddings else torch.tensor([])
        except Exception as e:
            logging.error(f"Ошибка при кодировании текстов в SkillMatcher: {e}", exc_info=True)
            raise