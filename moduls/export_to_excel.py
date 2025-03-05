import pandas as pd
from tkinter import filedialog
from datetime import datetime

class ExcelExporter:
    """Класс для экспорта результатов анализа в Excel-файл."""

    def __init__(self, results, program_name=None, vacancy_name=None):
        """Инициализация экспортера с результатами анализа."""
        self.results = results
        self.program_name = program_name
        self.vacancy_name = vacancy_name

    def export_to_excel(self):
        """Экспорт данных в Excel-файл с выбором пути пользователем."""
        if not self.results:
            return "Нет данных для экспорта! Сначала запустите анализ."

        # Подготовка данных для экспорта
        data = self._prepare_data()

        # Создание DataFrame
        df = pd.DataFrame(data)

        # Запрос пути для сохранения файла
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
        """Подготовка данных для экспорта в требуемом порядке."""
        data = []

        # Добавление заголовков
        if self.program_name:
            data.append({"Описание компетенции": f"Образовательная программа: {self.program_name}", "Вид компетенции": "", "Оценка": ""})
        if self.vacancy_name:
            data.append({"Описание компетенции": f"Вакансия: {self.vacancy_name}", "Вид компетенции": "", "Оценка": ""})
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        data.append({"Описание компетенции": f"Дата создания: {creation_date}", "Вид компетенции": "", "Оценка": ""})

        # Добавление компетенций
        for skill, (score, ctype) in self.results.get("similarity_results", {}).items():
            data.append({"Описание компетенции": skill, "Вид компетенции": ctype, "Оценка": score})

        # Добавление оценок групп и общей оценки
        if "group_scores" in self.results and "overall_score" in self.results:
            for ctype, score in self.results["group_scores"].items():
                data.append({"Описание компетенции": f"Оценка группы: {ctype}", "Вид компетенции": "", "Оценка": score})
            data.append({"Описание компетенции": "Общая оценка программы", "Вид компетенции": "", "Оценка": self.results["overall_score"]})

        return data