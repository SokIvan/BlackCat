import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

class DataManager:
    """Управление данными в файлах для работы на Render"""
    
    def __init__(self, data_dir: str = "data"):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Файлы для хранения данных
        self.users_file = self.data_dir / "users.json"
        self.computers_file = self.data_dir / "computers.json"
        self.alerts_file = self.data_dir / "alerts.json"
        
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализирует файлы данных если их нет"""
        files_to_create = {
            self.users_file: {},
            self.computers_file: {},
            self.alerts_file: []
        }
        
        for file_path, default_data in files_to_create.items():
            if not file_path.exists():
                self._save_data(file_path, default_data)
                self.logger.info(f"📁 Создан файл данных: {file_path.name}")
    
    def _load_data(self, file_path: Path):
        """Загружает данные из файла"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки {file_path}: {e}")
            return None
    
    def _save_data(self, file_path: Path, data):
        """Сохраняет данные в файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения {file_path}: {e}")
            return False
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ===
    
    def register_user(self, user_id: int, computer_id: str, username: str = None, first_name: str = None):
        """Регистрирует пользователя и привязывает компьютер"""
        users = self._load_data(self.users_file) or {}
        computers = self._load_data(self.computers_file) or {}
        
        # Сохраняем пользователя
        users[str(user_id)] = {
            "computer_id": computer_id,
            "username": username,
            "first_name": first_name,
            "registered_at": self._get_timestamp()
        }
        
        # Сохраняем привязку компьютер -> пользователь
        computers[computer_id] = {
            "user_id": user_id,
            "username": username,
            "registered_at": self._get_timestamp()
        }
        
        # Сохраняем оба файла
        success1 = self._save_data(self.users_file, users)
        success2 = self._save_data(self.computers_file, computers)
        
        if success1 and success2:
            self.logger.info(f"✅ Пользователь {user_id} привязал компьютер {computer_id}")
            return True
        else:
            self.logger.error("❌ Ошибка сохранения данных регистрации")
            return False
    
    def get_user_by_computer_id(self, computer_id: str) -> Optional[int]:
        """Находит user_id по computer_id"""
        computers = self._load_data(self.computers_file) or {}
        computer_data = computers.get(computer_id)
        return computer_data.get('user_id') if computer_data else None
    
    def get_computer_by_user_id(self, user_id: int) -> Optional[str]:
        """Находит computer_id по user_id"""
        users = self._load_data(self.users_file) or {}
        user_data = users.get(str(user_id))
        return user_data.get('computer_id') if user_data else None
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        users = self._load_data(self.users_file) or {}
        return users.get(str(user_id))
    
    def get_all_users(self) -> Dict:
        """Получает всех пользователей"""
        return self._load_data(self.users_file) or {}
    
    def get_all_computers(self) -> Dict:
        """Получает все компьютеры"""
        return self._load_data(self.computers_file) or {}
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С УВЕДОМЛЕНИЯМИ ===
    
    def save_alert(self, computer_id: str, detection_count: int, timestamp: str):
        """Сохраняет информацию об уведомлении"""
        alerts = self._load_data(self.alerts_file) or []
        
        alert_data = {
            "computer_id": computer_id,
            "detection_count": detection_count,
            "timestamp": timestamp,
            "alert_id": len(alerts) + 1
        }
        
        alerts.append(alert_data)
        
        if self._save_data(self.alerts_file, alerts):
            self.logger.info(f"📊 Сохранено уведомление для {computer_id}")
            return True
        return False
    
    def get_alerts_by_computer(self, computer_id: str) -> List[Dict]:
        """Получает уведомления для компьютера"""
        alerts = self._load_data(self.alerts_file) or []
        return [alert for alert in alerts if alert.get('computer_id') == computer_id]
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Получает последние уведомления"""
        alerts = self._load_data(self.alerts_file) or []
        return alerts[-limit:] if alerts else []
    
    def _get_timestamp(self):
        """Возвращает текущую timestamp строку"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_stats(self) -> Dict:
        """Получает статистику системы"""
        users = self.get_all_users()
        computers = self.get_all_computers()
        alerts = self._load_data(self.alerts_file) or []
        
        return {
            "total_users": len(users),
            "total_computers": len(computers),
            "total_alerts": len(alerts),
            "last_updated": self._get_timestamp()
        }