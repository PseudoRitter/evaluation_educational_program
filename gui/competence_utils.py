import logging
import tkinter as tk
from tkinter import ttk

def update_competence_table(app_instance, program_id, table_name="competence_table"):
    """Обновление таблицы компетенций для выбранной программы.
    Args:
        app_instance: Экземпляр приложения (App или контекст).
        program_id: ID образовательной программы.
        table_name (str): Имя атрибута таблицы (по умолчанию 'competence_table', для 'add_program_window' можно 'competence_table_add').
    """
    # Проверяем доступность таблицы по указанному имени
    table_attr = getattr(app_instance, table_name, None)
    frame_attr = getattr(app_instance, f"{table_name}_frame", None)
    
    if not table_attr or not table_attr.winfo_exists():
        logging.warning(f"Таблица {table_name} недоступна. Выполняется переинициализация.")
        if frame_attr and frame_attr.winfo_exists():
            frame_attr.destroy()
        setattr(app_instance, f"{table_name}_frame", ttk.LabelFrame(app_instance.education_tab if hasattr(app_instance, 'education_tab') else app_instance, text="Компетенции программы"))
        getattr(app_instance, f"{table_name}_frame").pack(pady=5, padx=5, fill="both", expand=True)
        setattr(app_instance, table_name, ttk.Treeview(getattr(app_instance, f"{table_name}_frame"), columns=("competence", "competence_type"), show="headings", height=10))
        table_attr = getattr(app_instance, table_name)
        table_attr.heading("competence", text="Компетенция")
        table_attr.heading("competence_type", text="Вид компетенции")
        table_attr.column("competence", width=400)
        table_attr.column("competence_type", width=300)
        table_attr.pack(pady=5, fill="both", expand=True)
    # Обновляем данные в таблице
    table_attr.delete(*table_attr.get_children())
    competences = app_instance.logic.db.fetch_program_details(program_id)
    for competence in competences:
        competence_name, competence_type = competence[5], competence[6]  # competence_name, type_competence_full_name
        if competence_name:
            table_attr.insert("", tk.END, values=(competence_name, competence_type or "Неизвестно"))