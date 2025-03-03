import pandas as pd
from tkinter import filedialog
from datetime import datetime

class ExcelExporter:
    def __init__(self, results, program_name=None, vacancy_name=None):
        self.results = results
        self.program_name = program_name  # Название выбранной программы
        self.vacancy_name = vacancy_name  # Название выбранной вакансии

    def export_to_excel(self):
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

        data = {
            "Описание компетенции": competences,
            "Вид компетенции": competence_types,
            "Оценка": scores
        }
        df_competences = pd.DataFrame(data)

        # Добавление информации о программе, вакансии, дате и общих результатов
        if "group_scores" in self.results and "overall_score" in self.results:
            group_scores_data = []
            # Добавляем строки с программой, вакансией и датой
            if self.program_name:
                group_scores_data.append({"Описание компетенции": f"Образовательная программа: {self.program_name}", "Вид компетенции": "", "Оценка": ""})
            if self.vacancy_name:
                group_scores_data.append({"Описание компетенции": f"Вакансия: {self.vacancy_name}", "Вид компетенции": "", "Оценка": ""})
            creation_date = datetime.now().strftime("%Y-%d-%m %H:%M")
            group_scores_data.append({"Описание компетенции": f"Дата создания: {creation_date}", "Вид компетенции": "", "Оценка": ""})

            # Добавляем оценки групп компетенций
            for ctype, score in self.results["group_scores"].items():
                group_scores_data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            overall_score_data = {"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]}
            group_scores_df = pd.DataFrame(group_scores_data)
            overall_score_df = pd.DataFrame([overall_score_data])
            df = pd.concat([df_competences, group_scores_df, overall_score_df], ignore_index=True)
        else:
            df = df_competences

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить как"
        )

        if filepath:
            try:
                df.to_excel(filepath, index=False)
                return f"Данные успешно экспортированы в {filepath}"
            except Exception as e:
                return f"Ошибка при экспорте данных: {str(e)}"
        return "Экспорт отменен."
    