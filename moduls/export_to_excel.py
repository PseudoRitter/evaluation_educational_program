import pandas as pd
from tkinter import filedialog
from datetime import datetime

class ExcelExporter:
    def __init__(self, results, program_name=None, vacancy_name=None):
        self.results = results
        self.program_name = program_name
        self.vacancy_name = vacancy_name

    def export_to_excel(self):
        if not self.results:
            return "Нет данных для экспорта! Сначала запустите анализ."

        # Создание списка данных в нужном порядке
        data = []

        # Добавляем заголовки: программа, вакансия, дата
        if self.program_name:
            data.append({"Описание компетенции": f"Образовательная программа: {self.program_name}", "Вид компетенции": "", "Оценка": ""})
        if self.vacancy_name:
            data.append({"Описание компетенции": f"Вакансия: {self.vacancy_name}", "Вид компетенции": "", "Оценка": ""})
        creation_date = datetime.now().strftime("%Y-%d-%m %H:%M")
        data.append({"Описание компетенции": f"Дата создания: {creation_date}", "Вид компетенции": "", "Оценка": ""})

        # Добавляем компетенции
        for skill, (score, ctype) in self.results["similarity_results"].items():
            data.append({"Описание компетенции": skill, "Вид компетенции": ctype, "Оценка": score})

        # Добавляем оценки групп и общую оценку, если они есть
        if "group_scores" in self.results and "overall_score" in self.results:
            for ctype, score in self.results["group_scores"].items():
                data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            data.append({"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]})

        # Создание DataFrame из единого списка данных
        df = pd.DataFrame(data)

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