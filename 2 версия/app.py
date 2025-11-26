# project_management_v2_gui.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv
import time
from datetime import datetime, timedelta

class AdvancedProjectManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Расширенная система управления проектами")
        self.root.geometry("1200x800")
        
        self.db_name = 'project_management_advanced.db'
        self.init_database()
        self.create_widgets()
        self.refresh_projects_list()
        
    def init_database(self):
        """Инициализация базы данных с индексами"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      description TEXT,
                      created_date TEXT,
                      deadline TEXT,
                      budget REAL DEFAULT 0,
                      status TEXT DEFAULT 'Активный')''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      project_id INTEGER,
                      title TEXT NOT NULL,
                      description TEXT,
                      status TEXT DEFAULT 'Новая',
                      assignee TEXT,
                      priority TEXT DEFAULT 'Средний',
                      created_date TEXT,
                      deadline TEXT,
                      estimated_hours INTEGER DEFAULT 0,
                      actual_hours INTEGER DEFAULT 0,
                      FOREIGN KEY (project_id) REFERENCES projects (id))''')
        
        # Создание индексов
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)")
        
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Расширенная система управления проектами", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Левая панель - проекты
        left_frame = ttk.LabelFrame(main_frame, text="Проекты", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Кнопки управления проектами
        project_buttons_frame = ttk.Frame(left_frame)
        project_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(project_buttons_frame, text="Добавить проект", 
                  command=self.add_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(project_buttons_frame, text="Удалить проект", 
                  command=self.delete_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(project_buttons_frame, text="Статистика", 
                  command=self.show_project_stats).pack(side=tk.LEFT)
        
        # Список проектов
        self.projects_listbox = tk.Listbox(left_frame, height=15, width=35)
        self.projects_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.projects_listbox.bind('<<ListboxSelect>>', self.on_project_select)
        
        # Правая панель - задачи и аналитика
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Верхняя часть - информация о проекте
        info_frame = ttk.LabelFrame(right_frame, text="Информация о проекте", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        self.project_info_text = tk.Text(info_frame, height=4, width=60, font=('Arial', 9))
        self.project_info_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Кнопки экспорта и теста производительности
        export_frame = ttk.Frame(info_frame)
        export_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(export_frame, text="Экспорт отчета", 
                  command=self.export_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Тест производительности", 
                  command=self.run_performance_test).pack(side=tk.LEFT)
        
        # Средняя часть - задачи
        tasks_frame = ttk.LabelFrame(right_frame, text="Задачи проекта", padding="10")
        tasks_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tasks_frame.columnconfigure(0, weight=1)
        tasks_frame.rowconfigure(1, weight=1)
        
        # Кнопки управления задачами
        task_buttons_frame = ttk.Frame(tasks_frame)
        task_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(task_buttons_frame, text="Добавить задачу", 
                  command=self.add_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_buttons_frame, text="Изменить статус", 
                  command=self.update_task_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_buttons_frame, text="Обновить часы", 
                  command=self.update_task_hours).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_buttons_frame, text="Удалить задачу", 
                  command=self.delete_task).pack(side=tk.LEFT)
        
        # Таблица задач
        columns = ('ID', 'Задача', 'Исполнитель', 'Статус', 'Приоритет', 'План ч.', 'Факт ч.', 'Дедлайн')
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=columns, show='headings', height=10)
        
        # Настройка колонок
        for col in columns:
            self.tasks_tree.heading(col, text=col)
        
        self.tasks_tree.column('ID', width=50)
        self.tasks_tree.column('Задача', width=200)
        self.tasks_tree.column('Исполнитель', width=120)
        self.tasks_tree.column('Статус', width=100)
        self.tasks_tree.column('Приоритет', width=80)
        self.tasks_tree.column('План ч.', width=60)
        self.tasks_tree.column('Факт ч.', width=60)
        self.tasks_tree.column('Дедлайн', width=120)
        
        self.tasks_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(tasks_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Нижняя часть - аналитика
        analytics_frame = ttk.LabelFrame(right_frame, text="Аналитика", padding="10")
        analytics_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.analytics_text = tk.Text(analytics_frame, height=6, width=80, font=('Arial', 9))
        self.analytics_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
    def refresh_projects_list(self):
        """Обновление списка проектов"""
        self.projects_listbox.delete(0, tk.END)
        projects = self.get_projects()
        
        for project in projects:
            budget_text = f" (Бюджет: {project[5]} руб.)" if project[5] else ""
            self.projects_listbox.insert(tk.END, f"{project[0]}: {project[1]}{budget_text}")
    
    def get_projects(self):
        """Получение списка проектов"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM projects ORDER BY id")
        projects = c.fetchall()
        conn.close()
        return projects
    
    def get_project_tasks(self, project_id):
        """Получение задач проекта"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''SELECT id, title, assignee, status, priority, estimated_hours, actual_hours, deadline 
                     FROM tasks WHERE project_id = ? ORDER BY id''', (project_id,))
        tasks = c.fetchall()
        conn.close()
        return tasks
    
    def on_project_select(self, event):
        """Обработка выбора проекта"""
        selection = self.projects_listbox.curselection()
        if selection:
            index = selection[0]
            project_text = self.projects_listbox.get(index)
            project_id = int(project_text.split(':')[0])
            
            # Получаем информацию о проекте
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT name, description, deadline, budget, status FROM projects WHERE id = ?", (project_id,))
            project_info = c.fetchone()
            conn.close()
            
            # Обновляем информацию о проекте
            self.current_project_id = project_id
            info_text = f"Проект: {project_info[0]}\n"
            info_text += f"Описание: {project_info[1]}\n"
            info_text += f"Статус: {project_info[4]} | Дедлайн: {project_info[2]}\n"
            info_text += f"Бюджет: {project_info[3]} руб."
            
            self.project_info_text.delete(1.0, tk.END)
            self.project_info_text.insert(1.0, info_text)
            
            # Обновляем список задач
            self.refresh_tasks_list(project_id)
            # Обновляем аналитику
            self.update_analytics(project_id)
    
    def refresh_tasks_list(self, project_id):
        """Обновление списка задач"""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        tasks = self.get_project_tasks(project_id)
        
        for task in tasks:
            self.tasks_tree.insert('', tk.END, values=task)
    
    def update_analytics(self, project_id):
        """Обновление аналитики"""
        stats = self.calculate_project_statistics(project_id)
        deadlines = self.calculate_deadlines(project_id)
        
        analytics_text = "=== СТАТИСТИКА ПРОЕКТА ===\n"
        analytics_text += f"Завершено: {stats['completed_tasks']}/{stats['total_tasks']} задач ({stats['completion_rate']}%)\n"
        analytics_text += f"Часы: плановые {stats['total_estimated_hours']}ч, фактические {stats['total_actual_hours']}ч\n"
        analytics_text += f"Эффективность: {stats['time_efficiency']}%\n"
        analytics_text += f"Средняя оценка: {stats['avg_estimated_hours']}ч на задачу\n\n"
        
        analytics_text += "=== ЗАГРУЗКА ИСПОЛНИТЕЛЕЙ ===\n"
        for assignee in stats['assignee_load']:
            analytics_text += f"{assignee[0]}: {assignee[1]} задач, {assignee[2]}ч\n"
        
        analytics_text += f"\n=== ДЕДЛАЙНЫ ===\n"
        analytics_text += f"Просрочено: {len(deadlines['overdue_tasks'])} задач\n"
        analytics_text += f"Ближайшие: {len(deadlines['upcoming_deadlines'])} задач\n"
        
        self.analytics_text.delete(1.0, tk.END)
        self.analytics_text.insert(1.0, analytics_text)
    
    def calculate_project_statistics(self, project_id):
        """Расчет статистики по проекту"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''SELECT 
                     COUNT(*) as total_tasks,
                     SUM(CASE WHEN status = 'Завершена' THEN 1 ELSE 0 END) as completed_tasks,
                     SUM(estimated_hours) as total_estimated_hours,
                     SUM(actual_hours) as total_actual_hours,
                     AVG(estimated_hours) as avg_estimated_hours
                     FROM tasks WHERE project_id = ?''', (project_id,))
        
        stats = c.fetchone()
        total_tasks, completed_tasks, total_estimated, total_actual, avg_estimated = stats
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        time_efficiency = (total_estimated / total_actual * 100) if total_actual > 0 else 0
        
        c.execute('''SELECT assignee, COUNT(*) as task_count, 
                     SUM(estimated_hours) as total_hours
                     FROM tasks WHERE project_id = ? AND assignee != ''
                     GROUP BY assignee''', (project_id,))
        
        assignee_load = c.fetchall()
        conn.close()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 2),
            'total_estimated_hours': total_estimated or 0,
            'total_actual_hours': total_actual or 0,
            'time_efficiency': round(time_efficiency, 2),
            'avg_estimated_hours': round(avg_estimated or 0, 2),
            'assignee_load': assignee_load
        }
    
    def calculate_deadlines(self, project_id):
        """Расчет дедлайнов"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Просроченные задачи
        c.execute('''SELECT id, title, deadline, assignee 
                     FROM tasks 
                     WHERE project_id = ? AND deadline < ? AND status != 'Завершена'
                     ORDER BY deadline''', 
                  (project_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        overdue_tasks = c.fetchall()
        
        # Ближайшие дедлайны
        three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''SELECT id, title, deadline, assignee 
                     FROM tasks 
                     WHERE project_id = ? AND deadline BETWEEN ? AND ? AND status != 'Завершена'
                     ORDER BY deadline''', 
                  (project_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), three_days_later))
        upcoming_deadlines = c.fetchall()
        
        conn.close()
        
        return {
            'overdue_tasks': overdue_tasks,
            'upcoming_deadlines': upcoming_deadlines
        }
    
    def add_project(self):
        """Добавление нового проекта"""
        dialog = AdvancedProjectDialog(self.root, "Добавление проекта")
        if dialog.result:
            name, description, deadline_days, budget = dialog.result
            
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO projects (name, description, created_date, deadline, budget)
                         VALUES (?, ?, ?, ?, ?)''', 
                      (name, description, created_date, deadline, budget))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Проект '{name}' создан!\nБюджет: {budget} руб.")
            self.refresh_projects_list()
    
    def delete_project(self):
        """Удаление проекта"""
        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите проект для удаления!")
            return
        
        index = selection[0]
        project_text = self.projects_listbox.get(index)
        project_id = int(project_text.split(':')[0])
        
        if messagebox.askyesno("Подтверждение", "Удалить проект и все его задачи?"):
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", "Проект удален!")
            self.refresh_projects_list()
            self.project_info_label.config(text="Выберите проект")
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
    
    def add_task(self):
        """Добавление новой задачи"""
        if not hasattr(self, 'current_project_id'):
            messagebox.showwarning("Предупреждение", "Сначала выберите проект!")
            return
        
        dialog = AdvancedTaskDialog(self.root, "Добавление задачи")
        if dialog.result:
            title, description, assignee, priority, deadline_days, estimated_hours = dialog.result
            
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO tasks (project_id, title, description, status, assignee, priority, created_date, deadline, estimated_hours)
                         VALUES (?, ?, ?, 'Новая', ?, ?, ?, ?, ?)''',
                      (self.current_project_id, title, description, assignee, priority, created_date, deadline, estimated_hours))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Задача '{title}' добавлена!\nОценка: {estimated_hours}ч")
            self.refresh_tasks_list(self.current_project_id)
            self.update_analytics(self.current_project_id)
    
    def update_task_status(self):
        """Изменение статуса задачи"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу!")
            return
        
        item = selection[0]
        task_id = self.tasks_tree.item(item)['values'][0]
        
        statuses = ['Новая', 'В работе', 'На проверке', 'Завершена', 'Отложена']
        new_status = simpledialog.askstring("Изменение статуса", 
                                           "Выберите новый статус:\n" + "\n".join(statuses),
                                           initialvalue='В работе')
        
        if new_status and new_status in statuses:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Статус изменен на '{new_status}'")
            self.refresh_tasks_list(self.current_project_id)
            self.update_analytics(self.current_project_id)
    
    def update_task_hours(self):
        """Обновление фактических часов"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу!")
            return
        
        item = selection[0]
        task_id = self.tasks_tree.item(item)['values'][0]
        task_title = self.tasks_tree.item(item)['values'][1]
        
        actual_hours = simpledialog.askinteger("Обновление часов", 
                                              f"Фактические часы для задачи '{task_title}':",
                                              minvalue=0)
        
        if actual_hours is not None:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("UPDATE tasks SET actual_hours = ? WHERE id = ?", (actual_hours, task_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Установлено {actual_hours} фактических часов")
            self.refresh_tasks_list(self.current_project_id)
            self.update_analytics(self.current_project_id)
    
    def delete_task(self):
        """Удаление задачи"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу!")
            return
        
        item = selection[0]
        task_id = self.tasks_tree.item(item)['values'][0]
        task_title = self.tasks_tree.item(item)['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task_title}'?"):
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", "Задача удалена!")
            self.refresh_tasks_list(self.current_project_id)
            self.update_analytics(self.current_project_id)
    
    def export_report(self):
        """Экспорт отчета"""
        if not hasattr(self, 'current_project_id'):
            messagebox.showwarning("Предупреждение", "Сначала выберите проект!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Сохранить отчет как"
        )
        
        if filename:
            self.export_project_report(self.current_project_id, filename)
            messagebox.showinfo("Успех", f"Отчет сохранен в:\n{filename}")
    
    def export_project_report(self, project_id, filename):
        """Экспорт отчета в CSV"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute("SELECT name, description, deadline, budget FROM projects WHERE id = ?", (project_id,))
        project_info = c.fetchone()
        
        c.execute('''SELECT title, description, status, assignee, priority, 
                     deadline, estimated_hours, actual_hours
                     FROM tasks WHERE project_id = ?''', (project_id,))
        tasks = c.fetchall()
        conn.close()
        
        stats = self.calculate_project_statistics(project_id)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow([f"Отчет по проекту: {project_info[0]}"])
            writer.writerow([f"Описание: {project_info[1]}"])
            writer.writerow([f"Дедлайн: {project_info[2]}"])
            writer.writerow([f"Бюджет: {project_info[3]} руб."])
            writer.writerow([])
            
            writer.writerow(["СТАТИСТИКА ПРОЕКТА"])
            writer.writerow(["Всего задач", stats['total_tasks']])
            writer.writerow(["Завершено задач", stats['completed_tasks']])
            writer.writerow(["Процент завершения", f"{stats['completion_rate']}%"])
            writer.writerow(["Всего плановых часов", stats['total_estimated_hours']])
            writer.writerow(["Всего фактических часов", stats['total_actual_hours']])
            writer.writerow(["Эффективность по времени", f"{stats['time_efficiency']}%"])
            writer.writerow([])
            
            writer.writerow(["СПИСОК ЗАДАЧ"])
            writer.writerow(["Задача", "Описание", "Статус", "Исполнитель", "Приоритет",
                           "Дедлайн", "Плановые часы", "Фактические часы"])
            
            for task in tasks:
                writer.writerow(task)
    
    def show_project_stats(self):
        """Показать статистику проекта"""
        if not hasattr(self, 'current_project_id'):
            messagebox.showwarning("Предупреждение", "Сначала выберите проект!")
            return
        
        stats = self.calculate_project_statistics(self.current_project_id)
        
        stats_text = f"=== ДЕТАЛЬНАЯ СТАТИСТИКА ===\n"
        stats_text += f"Всего задач: {stats['total_tasks']}\n"
        stats_text += f"Завершено: {stats['completed_tasks']} ({stats['completion_rate']}%)\n"
        stats_text += f"Плановые часы: {stats['total_estimated_hours']}\n"
        stats_text += f"Фактические часы: {stats['total_actual_hours']}\n"
        stats_text += f"Эффективность: {stats['time_efficiency']}%\n"
        stats_text += f"Средняя оценка: {stats['avg_estimated_hours']}ч\n"
        
        messagebox.showinfo("Статистика проекта", stats_text)
    
    def run_performance_test(self):
        """Запуск теста производительности"""
        result = self.performance_test(500)
        
        result_text = f"=== РЕЗУЛЬТАТЫ ТЕСТА ПРОИЗВОДИТЕЛЬНОСТИ ===\n"
        result_text += f"Обработано задач: {result['tasks_processed']}\n"
        result_text += f"Время вставки: {result['insert_time']:.4f} сек.\n"
        result_text += f"Время поиска: {result['search_time']:.4f} сек.\n"
        result_text += f"Время агрегации: {result['aggregation_time']:.4f} сек.\n"
        
        messagebox.showinfo("Тест производительности", result_text)
    
    def performance_test(self, num_tasks=500):
        """Тест производительности"""
        # Создание тестового проекта
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, created_date) VALUES (?, ?)",
                  ("Тестовый проект", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        test_project_id = c.lastrowid
        conn.commit()
        conn.close()

        # Тест вставки
        start_time = time.time()
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        for i in range(num_tasks):
            c.execute('''INSERT INTO tasks (project_id, title, status, assignee, created_date)
                         VALUES (?, ?, ?, ?, ?)''',
                      (test_project_id, f"Тестовая задача {i}", "Новая", f"Исполнитель {i % 5}",
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        insert_time = time.time() - start_time

        # Тест поиска
        start_time = time.time()
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tasks WHERE project_id = ? AND status = 'Новая'", (test_project_id,))
        search_result = c.fetchone()[0]
        conn.close()
        search_time = time.time() - start_time

        # Тест агрегации
        start_time = time.time()
        stats = self.calculate_project_statistics(test_project_id)
        aggregation_time = time.time() - start_time

        # Очистка
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE project_id = ?", (test_project_id,))
        c.execute("DELETE FROM projects WHERE id = ?", (test_project_id,))
        conn.commit()
        conn.close()

        return {
            'insert_time': insert_time,
            'search_time': search_time,
            'aggregation_time': aggregation_time,
            'tasks_processed': num_tasks
        }

class AdvancedProjectDialog(simpledialog.Dialog):
    def __init__(self, parent, title):
        self.result = None
        super().__init__(parent, title)
    
    def body(self, frame):
        ttk.Label(frame, text="Название проекта:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Описание:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(frame, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Срок (дней):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.days_entry = ttk.Entry(frame, width=30)
        self.days_entry.insert(0, "30")
        self.days_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Бюджет (руб.):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.budget_entry = ttk.Entry(frame, width=30)
        self.budget_entry.insert(0, "0")
        self.budget_entry.grid(row=3, column=1, padx=5, pady=5)
        
        return self.name_entry
    
    def apply(self):
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        try:
            days = int(self.days_entry.get())
            budget = float(self.budget_entry.get())
        except ValueError:
            days = 30
            budget = 0
        
        if name:
            self.result = (name, description, days, budget)

class AdvancedTaskDialog(simpledialog.Dialog):
    def __init__(self, parent, title):
        self.result = None
        super().__init__(parent, title)
    
    def body(self, frame):
        ttk.Label(frame, text="Название задачи:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Описание:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(frame, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Исполнитель:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.assignee_entry = ttk.Entry(frame, width=30)
        self.assignee_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Приоритет:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.priority_combo = ttk.Combobox(frame, values=['Низкий', 'Средний', 'Высокий'], state='readonly')
        self.priority_combo.set('Средний')
        self.priority_combo.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Срок (дней):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.days_entry = ttk.Entry(frame, width=30)
        self.days_entry.insert(0, "7")
        self.days_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Плановые часы:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.hours_entry = ttk.Entry(frame, width=30)
        self.hours_entry.insert(0, "0")
        self.hours_entry.grid(row=5, column=1, padx=5, pady=5)
        
        return self.title_entry
    
    def apply(self):
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        assignee = self.assignee_entry.get().strip()
        priority = self.priority_combo.get()
        
        try:
            days = int(self.days_entry.get())
            hours = int(self.hours_entry.get())
        except ValueError:
            days = 7
            hours = 0
        
        if title:
            self.result = (title, description, assignee, priority, days, hours)

def main():
    root = tk.Tk()
    app = AdvancedProjectManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()