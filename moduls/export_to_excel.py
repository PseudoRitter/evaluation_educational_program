import pandas as pd
from tkinter import filedialog

class ExcelExporter:
    def __init__(self, results):
        self.results = results

    def export_to_excel(self):
        # Проверка, есть ли данные для экспорта
        if not self.results:
            return "Нет данных для экспорта! Сначала запустите анализ."

        # Извлечение данных о компетенциях, типах и оценках
        competences = []
        competence_types = []
        scores = []

        for skill, (score, ctype) in self.results["similarity_results"].items():
            competences.append(skill)
            competence_types.append(ctype)
            scores.append(score)

        # Создание DataFrame для компетенций
        data = {
            "Описание компетенции": competences,
            "Вид компетенции": competence_types,
            "Оценка": scores
        }
        df_competences = pd.DataFrame(data)

        # Добавление общих результатов (оценки групп компетенций и общей оценки)
        if "group_scores" in self.results and "overall_score" in self.results:
            group_scores_data = []
            for ctype, score in self.results["group_scores"].items():
                group_scores_data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            overall_score_data = {"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]}
            group_scores_df = pd.DataFrame(group_scores_data)
            overall_score_df = pd.DataFrame([overall_score_data])
            df = pd.concat([df_competences, group_scores_df, overall_score_df], ignore_index=True)
        else:
            df = df_competences

        # Открытие диалогового окна для выбора пути сохранения
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить как"
        )

        if filepath:
            try:
                # Сохранение DataFrame в Excel
                df.to_excel(filepath, index=False)
                return f"Данные успешно экспортированы в {filepath}"
            except Exception as e:
                return f"Ошибка при экспорте данных: {str(e)}"
        return "Экспорт отменен."