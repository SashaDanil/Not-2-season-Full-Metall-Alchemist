import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta

class ProjectManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления проектами")
        self.root.geometry("1000x700")
        
        self.db_name = 'project_management.db'
        self.init_database()
        self.create_widgets()
        self.refresh_projects_list()
        
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      description TEXT,
                      created_date TEXT,
                      deadline TEXT)''')
        
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
                      FOREIGN KEY (project_id) REFERENCES projects (id))''')
        
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса строк и столбцов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Система управления проектами", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Левая панель - проекты
        left_frame = ttk.LabelFrame(main_frame, text="Проекты", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        # Кнопки управления проектами
        project_buttons_frame = ttk.Frame(left_frame)
        project_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(project_buttons_frame, text="Добавить проект", 
                  command=self.add_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(project_buttons_frame, text="Удалить проект", 
                  command=self.delete_project).pack(side=tk.LEFT)
        
        # Список проектов
        self.projects_listbox = tk.Listbox(left_frame, height=15, width=30)
        self.projects_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.projects_listbox.bind('<<ListboxSelect>>', self.on_project_select)
        
        # Правая панель - задачи
        right_frame = ttk.LabelFrame(main_frame, text="Задачи проекта", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Информация о проекте
        self.project_info_label = ttk.Label(right_frame, text="Выберите проект", 
                                           font=('Arial', 10, 'bold'))
        self.project_info_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Кнопки управления задачами
        task_buttons_frame = ttk.Frame(right_frame)
        task_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(task_buttons_frame, text="Добавить задачу", 
                  command=self.add_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_buttons_frame, text="Изменить статус", 
                  command=self.update_task_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_buttons_frame, text="Удалить задачу", 
                  command=self.delete_task).pack(side=tk.LEFT)
        
        # Таблица задач
        columns = ('ID', 'Задача', 'Исполнитель', 'Статус', 'Приоритет', 'Дедлайн')
        self.tasks_tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=12)
        
        # Настройка колонок
        self.tasks_tree.heading('ID', text='ID')
        self.tasks_tree.heading('Задача', text='Задача')
        self.tasks_tree.heading('Исполнитель', text='Исполнитель')
        self.tasks_tree.heading('Статус', text='Статус')
        self.tasks_tree.heading('Приоритет', text='Приоритет')
        self.tasks_tree.heading('Дедлайн', text='Дедлайн')
        
        self.tasks_tree.column('ID', width=50)
        self.tasks_tree.column('Задача', width=200)
        self.tasks_tree.column('Исполнитель', width=120)
        self.tasks_tree.column('Статус', width=100)
        self.tasks_tree.column('Приоритет', width=80)
        self.tasks_tree.column('Дедлайн', width=120)
        
        self.tasks_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Полоса прокрутки для таблицы
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
        # Статистика
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Всего проектов: 0 | Всего задач: 0")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
    def refresh_projects_list(self):
        """Обновление списка проектов"""
        self.projects_listbox.delete(0, tk.END)
        projects = self.get_projects()
        
        for project in projects:
            self.projects_listbox.insert(tk.END, f"{project[0]}: {project[1]}")
        
        self.update_stats()
    
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
        c.execute('''SELECT id, title, assignee, status, priority, deadline 
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
            c.execute("SELECT name, description, deadline FROM projects WHERE id = ?", (project_id,))
            project_info = c.fetchone()
            conn.close()
            
            # Обновляем информацию о проекте
            self.current_project_id = project_id
            self.project_info_label.config(
                text=f"Проект: {project_info[0]}\nОписание: {project_info[1]}\nДедлайн: {project_info[2]}"
            )
            
            # Обновляем список задач
            self.refresh_tasks_list(project_id)
    
    def refresh_tasks_list(self, project_id):
        """Обновление списка задач"""
        # Очищаем таблицу
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        tasks = self.get_project_tasks(project_id)
        
        for task in tasks:
            self.tasks_tree.insert('', tk.END, values=task)
    
    def add_project(self):
        """Добавление нового проекта"""
        dialog = ProjectDialog(self.root, "Добавление проекта")
        if dialog.result:
            name, description, deadline_days = dialog.result
            
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO projects (name, description, created_date, deadline)
                         VALUES (?, ?, ?, ?)''', (name, description, created_date, deadline))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Проект '{name}' успешно создан!")
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
        project_name = project_text.split(':', 1)[1].strip()
        
        if messagebox.askyesno("Подтверждение", f"Удалить проект '{project_name}' и все его задачи?"):
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
        
        dialog = TaskDialog(self.root, "Добавление задачи")
        if dialog.result:
            title, description, assignee, priority, deadline_days = dialog.result
            
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO tasks (project_id, title, description, status, assignee, priority, created_date, deadline)
                         VALUES (?, ?, ?, 'Новая', ?, ?, ?, ?)''',
                      (self.current_project_id, title, description, assignee, priority, created_date, deadline))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", f"Задача '{title}' добавлена!")
            self.refresh_tasks_list(self.current_project_id)
            self.update_stats()
    
    def update_task_status(self):
        """Изменение статуса задачи"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу для изменения статуса!")
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
            
            messagebox.showinfo("Успех", f"Статус задачи изменен на '{new_status}'")
            self.refresh_tasks_list(self.current_project_id)
    
    def delete_task(self):
        """Удаление задачи"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу для удаления!")
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
            self.update_stats()
    
    def update_stats(self):
        """Обновление статистики"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM projects")
        projects_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM tasks")
        tasks_count = c.fetchone()[0]
        
        conn.close()
        
        self.stats_label.config(text=f"Всего проектов: {projects_count} | Всего задач: {tasks_count}")

class ProjectDialog(simpledialog.Dialog):
    """Диалог для добавления проекта"""
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
        
        return self.name_entry
    
    def apply(self):
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        try:
            days = int(self.days_entry.get())
        except ValueError:
            days = 30
        
        if name:
            self.result = (name, description, days)

class TaskDialog(simpledialog.Dialog):
    """Диалог для добавления задачи"""
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
        
        return self.title_entry
    
    def apply(self):
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        assignee = self.assignee_entry.get().strip()
        priority = self.priority_combo.get()
        
        try:
            days = int(self.days_entry.get())
        except ValueError:
            days = 7
        
        if title:
            self.result = (title, description, assignee, priority, days)

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = ProjectManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()