import pandas as pd
from tkinter import filedialog
from datetime import datetime

class ExcelExporter:
    def __init__(self, results, program_name=None, vacancy_name=None, university=None, year=None):
        self.results = results
        self.program_name = program_name
        self.vacancy_name = vacancy_name
        self.university = university  
        self.year = year  

    def export_to_excel(self):
        if not self.results:
            return "Нет данных для экспорта! Сначала запустите анализ."

        data = self._prepare_data()

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
        return "Экспорт отменён."

    def _prepare_data(self):
        data = []

        if self.program_name:
            data.append({"Описание компетенции": f"Образовательная программа: {self.program_name}", "Вид компетенции": "", "Оценка": ""})
        if self.vacancy_name:
            data.append({"Описание компетенции": f"Вакансия: {self.vacancy_name}", "Вид компетенции": "", "Оценка": ""})
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        data.append({"Описание компетенции": f"Дата создания: {creation_date}", "Вид компетенции": "", "Оценка": ""})

        for skill, (score, ctype) in self.results.get("similarity_results", {}).items():
            data.append({"Описание компетенции": skill, "Вид компетенции": ctype, "Оценка": score})

        if "group_scores" in self.results and "overall_score" in self.results:
            for ctype, score in self.results["group_scores"].items():
                data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            data.append({"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]})

        return data

    def export_history_to_excel(self):
        if not self.results:
            return "Нет данных для экспорта!"

        data = self._prepare_history_data()

        df = pd.DataFrame(data)

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить как",
            initialfile=f"history_{self.program_name}_{self.vacancy_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )

        if filepath:
            try:
                df.to_excel(filepath, index=False)
                return f"Данные успешно экспортированы в {filepath}"
            except Exception as e:
                return f"Ошибка при экспорте данных: {str(e)}"
        return "Экспорт отменён."

    def _prepare_history_data(self):
        data = []

        if self.program_name:
            data.append({"Описание компетенции": f"Образовательная программа: {self.program_name}", "Вид компетенции": "", "Оценка": ""})
        if self.university:
            data.append({"Описание компетенции": f"ВУЗ: {self.university}", "Вид компетенции": "", "Оценка": ""})
        if self.year:
            data.append({"Описание компетенции": f"Год программы: {self.year}", "Вид компетенции": "", "Оценка": ""})
        if self.vacancy_name:
            data.append({"Описание компетенции": f"Вакансия: {self.vacancy_name}", "Вид компетенции": "", "Оценка": ""})
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        data.append({"Описание компетенции": f"Дата создания: {creation_date}", "Вид компетенции": "", "Оценка": ""})

        for skill, (score, ctype) in self.results.get("similarity_results", {}).items():
            data.append({"Описание компетенции": skill, "Вид компетенции": ctype, "Оценка": score})

        if "group_scores" in self.results and "overall_score" in self.results:
            for ctype, score in self.results["group_scores"].items():
                data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            data.append({"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]})

        return data