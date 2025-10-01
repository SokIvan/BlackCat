import cv2
import time
import json
from datetime import datetime
from pathlib import Path
import logging
import requests
import pyautogui

from .face_detector import FaceDetector
from .face_recognizer import FaceRecognizer

class ComputerGuard:
    """Главный класс системы охраны"""
    
    def __init__(self, computer_id: str = None, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Загружаем настройки из конфига или используем по умолчанию
        if config:
            self.detection_threshold = config.get_int('detection_threshold', 30)
            self.alert_threshold = config.get_int('alert_threshold', 20)
            self.alert_time_window = config.get_int('alert_time_window', 60)
        else:
            self.detection_threshold = 30
            self.alert_threshold = 20
            self.alert_time_window = 60
        
        self.computer_id = computer_id or self._get_or_create_computer_id()
        self.last_detection_time = None
        self.is_running = False
        
        # Счетчик обнаружений за временное окно
        self.detection_counter = 0
        self.detection_timestamps = []
        
        # Флаг отправки уведомления
        self.alert_sent = False
        
        # Конфигурация API
        self.api_config = self._load_api_config()
        
        # Инициализация компонентов
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        
        self.logger.info(f"🖥️ Идентификатор компьютера: {self.computer_id}")
        self.logger.info(f"📊 Настройки: threshold={self.alert_threshold}, window={self.alert_time_window}s")
        self.logger.info("🚀 Система охраны инициализирована")
    
    def _load_api_config(self):
        """Загружает конфигурацию API"""
        config_path = Path("api_config.json")
        default_config = {
            "server_url": "http://localhost:8000",
            "endpoint": "/api/alert",
            "timeout": 10
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфигурации API: {e}")
        
        # Сохраняем конфиг (создаем если не существует)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _get_or_create_computer_id(self) -> str:
        """Получение или создание ID компьютера"""
        config_path = Path("computer_config.json")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                computer_id = config.get('computer_id')
                if computer_id:
                    self.logger.info(f"📁 Загружен существующий ID: {computer_id}")
                    return computer_id
        
        # Генерация нового ID
        import uuid
        computer_id = str(uuid.uuid4())[:8].upper()
        
        config = {
            'computer_id': computer_id,
            'created_at': str(datetime.now().isoformat())
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"🆕 Сгенерирован новый ID: {computer_id}")
        print(f"\n🔑 ВАШ ID КОМПЬЮТЕРА: {computer_id}")
        print("✍️ Используйте этот ID в Telegram боте для привязки\n")
        
        return computer_id
    
    def _update_detection_counter(self):
        """Обновляет счетчик обнаружений за временное окно"""
        current_time = time.time()
        
        # Удаляем старые обнаружения (старше alert_time_window)
        self.detection_timestamps = [
            ts for ts in self.detection_timestamps 
            if current_time - ts <= self.alert_time_window
        ]
        
        # Добавляем текущее обнаружение
        self.detection_timestamps.append(current_time)
        self.detection_counter = len(self.detection_timestamps)
        
        self.logger.debug(f"📊 Счетчик обнаружений: {self.detection_counter}/{self.alert_threshold}")
        
        # СБРАСЫВАЕМ ФЛАГ если счетчик упал ниже порога
        if self.detection_counter < self.alert_threshold:
            self.alert_sent = False
            self.logger.debug("🔄 Флаг уведомления сброшен (счетчик ниже порога)")
    
    def capture_stranger_photo(self, frame) -> Path:
        """Сохранение фото незнакомца с камеры"""
        try:
            strangers_dir = Path("strangers_photos")
            strangers_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = strangers_dir / f"stranger_{self.computer_id}_{timestamp}.jpg"
            
            cv2.imwrite(str(filename), frame)
            self.logger.info(f"📸 Сохранено фото незнакомца: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения фото незнакомца: {e}")
            return None
    
    def take_screenshot(self) -> Path:
        """Создание скриншота экрана"""
        try:
            screenshot_dir = Path("screenshots")
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = screenshot_dir / f"screenshot_{self.computer_id}_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            self.logger.info(f"🖥️ Сохранен скриншот: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Ошибка создания скриншота: {e}")
            return None
    
    def send_api_alert(self, stranger_photo: Path, screenshot: Path):
        """Отправка уведомления на сервер через API"""
        try:
            # Подготавливаем данные для отправки
            alert_data = {
                "computer_id": self.computer_id,
                "command": "stranger_alert",
                "timestamp": datetime.now().isoformat(),
                "detection_count": self.detection_counter,
                "message": f"Обнаружено незнакомое лицо {self.detection_counter} раз за последнюю минуту"
            }
            
            # Подготавливаем файлы для отправки
            files = {}
            
            if stranger_photo and stranger_photo.exists():
                files['stranger_photo'] = open(stranger_photo, 'rb')
            
            if screenshot and screenshot.exists():
                files['screenshot'] = open(str(screenshot), 'rb')
            
            # URL для отправки
            api_url = f"{self.api_config['server_url']}{self.api_config['endpoint']}"
            
            self.logger.info(f"📤 Отправка API запроса на: {api_url}")
            
            # Отправляем POST запрос
            response = requests.post(
                api_url,
                data=alert_data,
                files=files,
                timeout=self.api_config['timeout']
            )
            
            # Закрываем файлы
            for file in files.values():
                file.close()
            
            if response.status_code == 200:
                self.logger.info("✅ Уведомление успешно отправлено на сервер")
                return True
            else:
                self.logger.error(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки API запроса: {e}")
            return False
    
    def process_frame(self, frame):
        """
        Обрабатывает один кадр с камеры
        Возвращает True если обнаружен незнакомец
        """
        # 1. ДЕТЕКЦИЯ: Находим ВСЕ лица на кадре
        faces = self.face_detector.detect_faces(frame)
        
        if len(faces) == 0:
            return False  # Лиц нет
        
        self.logger.debug(f"📹 Обнаружено лиц: {len(faces)}")
        
        # 2. ПРОВЕРКА: Для каждого лица проверяем, незнакомец ли он
        stranger_found = False
        for (x, y, w, h) in faces:
            # Вырезаем область лица
            face_roi = frame[y:y+h, x:x+w]
            
            # 3. РАСПОЗНАВАНИЕ: Сравниваем с известными лицами
            if self.face_recognizer.is_stranger(face_roi):
                stranger_found = True
                break  # Достаточно одного незнакомца
        
        if stranger_found:
            # Обновляем счетчик обнаружений
            self._update_detection_counter()
            
            # ПРОСТАЯ ПРОВЕРКА: если счетчик >= порога И еще не отправляли
            if self.detection_counter >= self.alert_threshold and not self.alert_sent:
                self.logger.info("🚨 Критическое количество обнаружений! Отправка уведомления...")
                print(f"🚨 Обнаружено {self.detection_counter} раз за минуту! Отправка уведомления...")
                
                # Сохраняем фото незнакомца
                stranger_photo = self.capture_stranger_photo(frame)
                
                # Делаем скриншот
                screenshot = self.take_screenshot()
                
                # Отправляем уведомление через API
                success = self.send_api_alert(stranger_photo, screenshot)
                
                if success:
                    # СТАВИМ ФЛАГ что отправили
                    self.alert_sent = True
                    self.logger.info("✅ Уведомление отправлено. Флаг установлен.")
                else:
                    self.logger.error("❌ Не удалось отправить уведомление. Флаг НЕ установлен.")
        
        return stranger_found
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        # Проверяем загружена ли модель распознавания
        if not self.face_recognizer.known_face_names:
            self.logger.error("❌ Не могу запустить мониторинг: модель распознавания не загружена!")
            print("❌ Модель распознавания не загружена!")
            print("💡 Проверьте файлы в known_faces_db/")
            return
        
        self.is_running = True
        self.logger.info("🚀 Запуск мониторинга...")
        
        try:
            # Пробуем открыть камеру
            cap = cv2.VideoCapture(0)
            
            # Проверяем, открылась ли камера
            if not cap.isOpened():
                self.logger.error("❌ Не удалось открыть веб-камеру!")
                print("❌ Веб-камера не найдена или недоступна!")
                return
                    
            self.logger.info("✅ Камера успешно подключена")
            
            # Устанавливаем разрешение
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации камеры: {e}")
            print(f"❌ Ошибка камеры: {e}")
            return
        
        print("\n🎥 Мониторинг запущен! Система охраны активна.")
        print(f"📊 Настройки обнаружения: {self.alert_threshold} раз за {self.alert_time_window} сек")
        print("💡 Уведомление отправляется ОДИН РАЗ при достижении порога")
        print("👤 Подойдите к камере для тестирования")
        print("⏹️  Нажмите Ctrl+C для остановки\n")
        
        while self.is_running:
            try:
                ret, frame = cap.read()
                if not ret:
                    self.logger.warning("⚠️ Не удалось получить кадр с камеры")
                    continue
                
                # Обрабатываем кадр
                stranger_detected = self.process_frame(frame)
                
                if stranger_detected:
                    if self.last_detection_time is None:
                        self.last_detection_time = time.time()
                        self.logger.info("👤 Обнаружен незнакомец...")
                    
                    # Показываем текущий счетчик каждые 5 обнаружений
                    if self.detection_counter % 5 == 0 and not self.alert_sent:
                        print(f"📊 Текущий счетчик: {self.detection_counter}/{self.alert_threshold}")
                        
                else:
                    # Сброс таймера если незнакомцев нет
                    self.last_detection_time = None
                
                # Задержка для снижения нагрузки
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(1)
        
        if 'cap' in locals():
            cap.release()
        self.logger.info("⛔ Мониторинг остановлен")
        print("⛔ Мониторинг остановлен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_running = False
        self.logger.info("🛑 Остановка системы охраны...")
        print("🛑 Остановка системы охраны...")