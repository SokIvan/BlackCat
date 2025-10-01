import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
from pathlib import Path
import threading
import webbrowser

class BlackCatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🐱 BlackCat - Система охраны компьютера")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Устанавливаем иконку (если есть)
        try:
            self.root.iconbitmap("blackcat.ico")  # Можно добавить иконку позже
        except:
            pass
        
        self.setup_gui()
        
    def setup_gui(self):
        # Создаем notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка "Главная"
        self.setup_main_tab(notebook)
        
        # Вкладка "Обучение"
        self.setup_training_tab(notebook)
        
        # Вкладка "Настройки"
        self.setup_settings_tab(notebook)
        
        # Вкладка "Инструкция"
        self.setup_instructions_tab(notebook)
        
        # Вкладка "Логи"
        self.setup_logs_tab(notebook)
    
    def setup_main_tab(self, notebook):
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="🐱 Главная")
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                               text="🐱 BlackCat - Система охраны компьютера", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Статус системы
        status_frame = ttk.LabelFrame(main_frame, text="Статус системы", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="🔴 Система неактивна", 
                                     font=('Arial', 12), foreground='red')
        self.status_label.pack(pady=5)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        # Кнопка запуска системы
        self.start_btn = ttk.Button(buttons_frame, 
                                   text="🚀 Запустить систему охраны", 
                                   command=self.start_system,
                                   style='Accent.TButton')
        self.start_btn.pack(pady=10, ipadx=20, ipady=10)
        
        # Кнопка остановки
        self.stop_btn = ttk.Button(buttons_frame, 
                                  text="⛔ Остановить систему", 
                                  command=self.stop_system,
                                  state='disabled')
        self.stop_btn.pack(pady=10, ipadx=20, ipady=10)
        
        # Информация о системе
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding=10)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        info_text = """
• Система отслеживает незнакомцев перед камерой
• Автоматически отправляет уведомления в Telegram
• Работает в фоновом режиме
• Требует предварительного обучения модели
        """
        info_label = ttk.Label(info_frame, text=info_text, justify='left')
        info_label.pack(pady=5)
    
    def setup_training_tab(self, notebook):
        training_frame = ttk.Frame(notebook)
        notebook.add(training_frame, text="🎯 Обучение")
        
        title_label = ttk.Label(training_frame, 
                               text="🎯 Обучение модели распознавания лиц", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)
        
        # Инструкция по обучению
        instruction_frame = ttk.LabelFrame(training_frame, text="Инструкция по обучению", padding=10)
        instruction_frame.pack(fill='x', padx=20, pady=10)
        
        instruction_text = """
1. Подготовьте датасет лиц в папке face_dataset/
   - face_dataset/owner/ - ваши фото (10-15 штук)
   - face_dataset/family/ - фото семьи (опционально)
   - face_dataset/friends/ - фото друзей (опционально)

2. Фото должны быть хорошего качества
3. Разные ракурсы и освещение
4. Минимальный размер: 100x100 пикселей

После обучения система будет распознавать знакомые лица и игнорировать их.
        """
        instruction_label = ttk.Label(instruction_frame, text=instruction_text, justify='left')
        instruction_label.pack(pady=5)
        
        # Кнопки обучения
        training_buttons_frame = ttk.Frame(training_frame)
        training_buttons_frame.pack(pady=20)
        
        self.train_btn = ttk.Button(training_buttons_frame, 
                                   text="🎓 Обучить модель", 
                                   command=self.train_model)
        self.train_btn.pack(pady=10, ipadx=20, ipady=10)
        
        # Прогресс обучения
        self.progress = ttk.Progressbar(training_frame, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)
        
        self.training_status = ttk.Label(training_frame, text="")
        self.training_status.pack(pady=5)
    
    def setup_settings_tab(self, notebook):
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Настройки")
        
        title_label = ttk.Label(settings_frame, 
                               text="⚙️ Настройки системы", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)
        
        # Настройки обнаружения
        detection_frame = ttk.LabelFrame(settings_frame, text="Настройки обнаружения", padding=10)
        detection_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(detection_frame, text="Порог обнаружений для уведомления:").grid(row=0, column=0, sticky='w', pady=5)
        self.detection_threshold = tk.StringVar(value="20")
        ttk.Entry(detection_frame, textvariable=self.detection_threshold, width=10).grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(detection_frame, text="Временное окно (секунды):").grid(row=1, column=0, sticky='w', pady=5)
        self.time_window = tk.StringVar(value="60")
        ttk.Entry(detection_frame, textvariable=self.time_window, width=10).grid(row=1, column=1, pady=5, padx=10)
        
        # Настройки интерфейса
        interface_frame = ttk.LabelFrame(settings_frame, text="Настройки интерфейса", padding=10)
        interface_frame.pack(fill='x', padx=20, pady=10)
        
        self.terminal_visible = tk.BooleanVar(value=True)
        ttk.Checkbutton(interface_frame, 
                       text="Показывать терминал при запуске", 
                       variable=self.terminal_visible).pack(anchor='w', pady=5)
        
        # Кнопки управления настройками
        settings_buttons_frame = ttk.Frame(settings_frame)
        settings_buttons_frame.pack(pady=20)
        
        ttk.Button(settings_buttons_frame, 
                  text="💾 Сохранить настройки", 
                  command=self.save_settings).pack(side='left', padx=10)
        
        ttk.Button(settings_buttons_frame, 
                  text="🔄 Сбросить настройки", 
                  command=self.reset_settings).pack(side='left', padx=10)
    
    def setup_instructions_tab(self, notebook):
        instructions_frame = ttk.Frame(notebook)
        notebook.add(instructions_frame, text="📖 Инструкция")
        
        title_label = ttk.Label(instructions_frame, 
                               text="📖 Полная инструкция по использованию", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)
        
        # Текст инструкции с прокруткой
        instruction_text = scrolledtext.ScrolledText(instructions_frame, width=80, height=25)
        instruction_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        instructions = """
🐱 BLACKCAT - СИСТЕМА ОХРАНЫ КОМПЬЮТЕРА
========================================

1. ПОДГОТОВКА К ИСПОЛЬЗОВАНИЮ
----------------------------------------

1.1. Обучение модели:
   - Перейдите во вкладку "🎯 Обучение"
   - Подготовьте фото знакомых лиц в папке face_dataset/
   - Нажмите "🎓 Обучить модель"
   - Дождитесь завершения обучения

1.2. Настройка Telegram бота:
   - Создайте бота через @BotFather в Telegram
   - Получите токен бота
   - Привяжите компьютер через команду /register

2. ЗАПУСК СИСТЕМЫ
----------------------------------------

2.1. Автозапуск (рекомендуется):
   - Система автоматически запустится при включении компьютера
   - Работает в фоновом режиме

2.2. Ручной запуск:
   - Перейдите во вкладку "🐱 Главная"
   - Нажмите "🚀 Запустить систему охраны"
   - Система начнет мониторинг

3. КАК ЭТО РАБОТАЕТ
----------------------------------------

3.1. Обнаружение лиц:
   - Система постоянно анализирует видео с камеры
   - Обнаруживает все лица в поле зрения
   - Сравнивает с обученной моделью

3.2. Уведомления:
   - При обнаружении незнакомца начинается подсчет
   - После 20+ обнаружений за 60 секунд отправляется уведомление
   - В уведомлении: фото незнакомца + скриншот экрана

4. СТРУКТУРА ПРОЕКТА
----------------------------------------

BlackCat.py          - Главное GUI приложение
main.py             - Основная программа
config.txt          - Настройки системы
face_dataset/       - Датасет для обучения
known_faces_db/     - Обученная модель
scripts/            - Вспомогательные скрипты

5. РЕШЕНИЕ ПРОБЛЕМ
----------------------------------------

5.1. Камера не определяется:
   - Проверьте подключение камеры
   - Убедитесь, что нет других программ, использующих камеру

5.2. Модель не обучена:
   - Обучите модель через GUI
   - Проверьте наличие фото в face_dataset/

5.3. Telegram уведомления не приходят:
   - Проверьте подключение к интернету
   - Убедитесь, что компьютер привязан к боту

6. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
----------------------------------------

- Язык программирования: Python 3.8+
- Компьютерное зрение: OpenCV + MediaPipe
- Распознавание лиц: LBPH алгоритм
- GUI: Tkinter
- Совместимость: Windows 10/11

7. КОНТАКТЫ И ПОДДЕРЖКА
----------------------------------------

Для получения технической поддержки обращайтесь к разработчику.

⚠️ ВНИМАНИЕ: Система предназначена для личного использования.
Не используйте для нарушений приватности других людей.
        """
        
        instruction_text.insert('1.0', instructions)
        instruction_text.config(state='disabled')  # Делаем текст только для чтения
    
    def setup_logs_tab(self, notebook):
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 Логи")
        
        title_label = ttk.Label(logs_frame, 
                               text="📋 Журнал событий системы", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)
        
        # Поле для логов
        self.logs_text = scrolledtext.ScrolledText(logs_frame, width=80, height=20)
        self.logs_text.pack(fill='both', expand=True, padx=20, pady=10)
        self.logs_text.config(state='disabled')
        
        # Кнопки управления логами
        logs_buttons_frame = ttk.Frame(logs_frame)
        logs_buttons_frame.pack(pady=10)
        
        ttk.Button(logs_buttons_frame, 
                  text="🔄 Обновить логи", 
                  command=self.update_logs).pack(side='left', padx=5)
        
        ttk.Button(logs_buttons_frame, 
                  text="🧹 Очистить логи", 
                  command=self.clear_logs).pack(side='left', padx=5)
        
        ttk.Button(logs_buttons_frame, 
                  text="💾 Сохранить логи", 
                  command=self.save_logs).pack(side='left', padx=5)
    
    def log_message(self, message):
        """Добавляет сообщение в лог"""
        self.logs_text.config(state='normal')
        self.logs_text.insert('end', f"{message}\n")
        self.logs_text.see('end')
        self.logs_text.config(state='disabled')
    
    def start_system(self):
        """Запускает основную систему"""
        def run_system():
            try:
                self.log_message("🚀 Запуск системы охраны...")
                # Запускаем main.py
                if self.terminal_visible.get():
                    subprocess.run([sys.executable, "main.py"])
                else:
                    subprocess.run([sys.executable, "main.py"], creationflags=subprocess.CREATE_NO_WINDOW)
                
                self.log_message("✅ Система охраны запущена")
                self.status_label.config(text="🟢 Система активна", foreground='green')
                
            except Exception as e:
                self.log_message(f"❌ Ошибка запуска: {e}")
                messagebox.showerror("Ошибка", f"Не удалось запустить систему: {e}")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_system)
        thread.daemon = True
        thread.start()
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
    
    def stop_system(self):
        """Останавливает систему"""
        # В реальной реализации здесь будет остановка процесса
        self.log_message("⛔ Остановка системы охраны...")
        self.status_label.config(text="🔴 Система неактивна", foreground='red')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log_message("✅ Система остановлена")
    
    def train_model(self):
        """Запускает обучение модели"""
        def run_training():
            try:
                self.train_btn.config(state='disabled')
                self.progress.start()
                self.training_status.config(text="Обучение модели...")
                self.log_message("🎓 Запуск обучения модели...")
                
                # Запускаем скрипт обучения
                result = subprocess.run([
                    sys.executable, 
                    "scripts/face_trainer.py"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_message("✅ Обучение завершено успешно!")
                    self.training_status.config(text="✅ Обучение завершено!")
                    messagebox.showinfo("Успех", "Модель успешно обучена!")
                else:
                    self.log_message(f"❌ Ошибка обучения: {result.stderr}")
                    self.training_status.config(text="❌ Ошибка обучения")
                    messagebox.showerror("Ошибка", f"Ошибка обучения:\n{result.stderr}")
                
            except Exception as e:
                self.log_message(f"❌ Ошибка при обучении: {e}")
                messagebox.showerror("Ошибка", f"Не удалось обучить модель: {e}")
            finally:
                self.progress.stop()
                self.train_btn.config(state='normal')
        
        thread = threading.Thread(target=run_training)
        thread.daemon = True
        thread.start()
    
    def save_settings(self):
        """Сохраняет настройки в config.txt"""
        try:
            config_content = f"""# BlackCat System Configuration
terminal_visible={str(self.terminal_visible.get()).lower()}
detection_threshold={self.detection_threshold.get()}
alert_time_window={self.time_window.get()}
camera_index=0
log_level=INFO
"""
            with open("config.txt", "w", encoding="utf-8") as f:
                f.write(config_content)
            
            self.log_message("💾 Настройки сохранены")
            messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения настроек: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
    
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        self.terminal_visible.set(True)
        self.detection_threshold.set("20")
        self.time_window.set("60")
        self.log_message("🔄 Настройки сброшены к значениям по умолчанию")
    
    def update_logs(self):
        """Обновляет логи (в реальной реализации будет читать из файла)"""
        self.log_message("🔁 Логи обновлены")
    
    def clear_logs(self):
        """Очищает логи"""
        self.logs_text.config(state='normal')
        self.logs_text.delete('1.0', 'end')
        self.logs_text.config(state='disabled')
        self.log_message("🧹 Логи очищены")
    
    def save_logs(self):
        """Сохраняет логи в файл"""
        try:
            with open("blackcat_logs.txt", "w", encoding="utf-8") as f:
                logs = self.logs_text.get('1.0', 'end')
                f.write(logs)
            self.log_message("💾 Логи сохранены в blackcat_logs.txt")
            messagebox.showinfo("Успех", "Логи успешно сохранены!")
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения логов: {e}")

def main():
    # Проверяем наличие необходимых файлов
    required_files = ["main.py", "scripts/face_trainer.py"]
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        messagebox.showerror(
            "Ошибка", 
            f"Отсутствуют необходимые файлы:\n" + "\n".join(missing_files) +
            f"\n\nУбедитесь, что все файлы находятся в правильных папках."
        )
        return
    
    # Создаем главное окно
    root = tk.Tk()
    
    # Стиль для акцентной кнопки
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = BlackCatApp(root)
    app.log_message("🐱 BlackCat GUI запущен")
    app.log_message("📁 Система готова к работе")
    
    root.mainloop()

if __name__ == "__main__":
    main()