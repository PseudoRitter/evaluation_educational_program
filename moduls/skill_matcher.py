from sentence_transformers import SentenceTransformer, util
import torch
import logging
import gc
import numpy as np

class SkillMatcher:
    def __init__(self, device="cpu", model_path="C:/python-models/tuned_model_mpnet_v21", reduce_factor=0.15, boost_factor=0.2):
        self.device = device
        self.model_path = model_path
        self.model = None
        self.boost_factor = boost_factor
        self.reduce_factor = reduce_factor
        self.paraphrase_model = None
        self.similarity_job = None
        logging.info(f"SkillMatcher инициализирован для устройства: {self.device}, boost_factor: {self.boost_factor}, reduce_factor: {self.reduce_factor}")

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

    def _load_paraphrase_model(self):
        if self.paraphrase_model is None:
            try:
                self.paraphrase_model = SentenceTransformer('C:/python-models/tuned_model_mpnet_v21')
                self.paraphrase_model.to(self.device)
                logging.info(f"Модель paraphrase-multilingual-mpnet-base-v2 загружена на {self.device}")
            except Exception as e:
                logging.error(f"Ошибка загрузки модели paraphrase-multilingual-mpnet-base-v2: {e}", exc_info=True)
                raise

    def _split_skill_into_chunks(self, skill, max_words_per_chunk):
        """Разделяет компетенцию на подпредложения по max_words_per_chunk слов."""
        words = skill.split()
        if len(words) <= max_words_per_chunk:
            return [skill]
        
        chunks = []
        for i in range(0, len(words), max_words_per_chunk):
            chunk = " ".join(words[i:i + max_words_per_chunk])
            chunks.append(chunk)
        logging.debug(f"Компетенция '{skill}' разделена на {len(chunks)} частей")
        return chunks

    def match_skills(self, program_skills, job_descriptions, batch_size, threshold=75, stop_flag=False, max_words_per_chunk=10, competence_types=None):
        try:
            if not program_skills or not job_descriptions:
                logging.warning("Нет данных для анализа навыков.")
                return {"sentence_transformer": {}, "frequencies": {}}

            self._load_model()
            if stop_flag:
                logging.info("Анализ принудительно остановлен перед кодированием навыков.")
                return {"sentence_transformer": {}, "frequencies": {}}

            job_embeddings = self._encode_in_batches(job_descriptions, batch_size, stop_flag)
            if stop_flag:
                logging.info("Анализ принудительно остановлен после кодирования описаний вакансий.")
                return {"sentence_transformer": {}, "frequencies": {}}

            # Разделяем длинные компетенции на части
            all_chunks = []
            skill_to_chunks = {}
            chunk_to_skill_index = []
            for skill_idx, skill in enumerate(program_skills):
                chunks = self._split_skill_into_chunks(skill, max_words_per_chunk)
                skill_to_chunks[skill] = chunks
                all_chunks.extend(chunks)
                chunk_to_skill_index.extend([skill_idx] * len(chunks))

            # Кодируем все части компетенций
            if all_chunks:
                chunk_embeddings = self._encode_in_batches(all_chunks, batch_size, stop_flag)
            else:
                chunk_embeddings = torch.tensor([], device=self.device)
            if stop_flag:
                logging.info("Анализ принудительно остановлен после кодирования навыков программы.")
                return {"sentence_transformer": {}, "frequencies": {}}

            similarity_results = {}
            frequency_results = {}
            chunk_index = 0

            for skill_idx, skill in enumerate(program_skills):
                if stop_flag:
                    logging.info("Показ принудительно остановлен во время вычисления сходства.")
                    return {"sentence_transformer": {}, "frequencies": {}}
                
                chunks = skill_to_chunks[skill]
                chunk_count = len(chunks)
                
                if chunk_count == 0:
                    continue
                
                # Собираем сходства и частоты для всех частей компетенции
                chunk_similarities = []
                chunk_frequencies = []
                
                for _ in range(chunk_count):
                    if chunk_index >= len(chunk_embeddings):
                        break
                    similarities = util.pytorch_cos_sim(chunk_embeddings[chunk_index:chunk_index+1], job_embeddings)[0].cpu().numpy()
                    mean_similarity = similarities.mean().item()
                    frequency = np.sum(similarities >= threshold/100)

                    # Проверяем тип компетенции и similarity_job для модификации
                    if competence_types and chunk_to_skill_index[chunk_index] < len(competence_types):
                        ctype = competence_types[chunk_to_skill_index[chunk_index]]
                        if self.similarity_job is not None:
                            if self.similarity_job < 0.5 and mean_similarity < 0.5:
                                # Не уменьшаем оценку для универсальных компетенций
                                if ctype != "Универсальная компетенция":
                                    mean_similarity = max(0.0, mean_similarity - self.reduce_factor)
                                elif ctype == "Универсальная компетенция":
                                    mean_similarity = max(0.0, mean_similarity - self.reduce_factor + 0.12)
                            elif self.similarity_job > 0.6 and mean_similarity >= 0.6:
                                # Применяем boost_factor для всех типов компетенций
                                mean_similarity = min(1.0, mean_similarity + self.boost_factor)
                    
                    chunk_similarities.append(mean_similarity)
                    #chunk_frequencies.append(frequency)
                    chunk_index += 1
                
                    frequency_results[skill.strip()] = int(frequency)

                # Вычисляем средние значения для исходной компетенции
                if chunk_similarities:
                    mean_similarity = np.mean(chunk_similarities) * 200 #200 + 10
                    mean_frequency = np.mean(chunk_frequencies) * 200
                    similarity_results[skill.strip()] = mean_similarity
                    #frequency_results[skill.strip()] = int(mean_similarity)
                    #logging.debug(f"Компетенция '{skill}': среднее сходство={mean_similarity:.4f}, средняя частота={mean_frequency:.2f}")

            logging.debug(f"Порог для частот: {threshold}")
            return {"sentence_transformer": similarity_results, "frequencies": frequency_results}
        except Exception as e:
            logging.error(f"Ошибка вычисления сходства: {e}", exc_info=True)
            raise
        finally:
            self._cleanup_memory()

    def compare_program_vacancy_names(self, program_name, vacancy_name):
        try:
            if not program_name or not vacancy_name:
                logging.warning("Название программы или вакансии пустое.")
                return 0.0

            self._load_paraphrase_model()
            program_embedding = self.paraphrase_model.encode(program_name, convert_to_tensor=True, device=self.device)
            vacancy_embedding = self.paraphrase_model.encode(vacancy_name, convert_to_tensor=True, device=self.device)
            similarity = util.pytorch_cos_sim(program_embedding, vacancy_embedding).cpu().numpy()[0][0]
            
            logging.info(f"Косинусное сходство между '{program_name}' и '{vacancy_name}': {similarity:.4f}")
            self.similarity_job = similarity
            return similarity
        except Exception as e:
            logging.error(f"Ошибка при сравнении названий программы и вакансии: {e}", exc_info=True)
            return 0.0
        finally:
            self._cleanup_memory()

    def _encode_in_batches(self, texts, batch_size, stop_flag=False):
        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                if stop_flag:
                    logging.info("Анализ принудительно остановлен во время кодирования батча.")
                    return torch.tensor([], device=self.device)
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
            if self.model is not None:
                self.model.to("cpu")
                del self.model
                self.model = None
                logging.info("Модель tuned_model_mpnet_v21 удалена")
            if self.paraphrase_model is not None:
                self.paraphrase_model.to("cpu")
                del self.paraphrase_model
                self.paraphrase_model = None
                logging.info("Модель paraphrase-multilingual-mpnet-base-v2 удалена")
            gc.collect()
            torch.cuda.empty_cache()