import pandas as pd
from tkinter import filedialog

class ExcelExporter:
    def __init__(self, results):
        self.results = results

    def export_to_excel(self):
        # Проверка, есть ли данные для экспорта
        if not self.results:
            return "Нет данных для экспорта! Сначала запустите анализ."

        # Создание DataFrame для экспорта
        data = {
            "Описание компетенции": list(self.results.keys()),
            "Оценка": list(self.results.values())
        }
        df = pd.DataFrame(data)

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