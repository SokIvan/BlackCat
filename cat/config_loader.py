import os
import logging
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_path="config.txt"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.settings = self._load_config()
    
    def _load_config(self):
        """Загружает настройки из config.txt"""
        default_config = {
            'terminal_visible': 'true',
            'detection_threshold': '20',
            'alert_time_window': '60', 
            'camera_index': '0',
            'log_level': 'INFO'
        }
        
        if not self.config_path.exists():
            self._create_default_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            default_config[key] = value
            
            self.logger.info("✅ Конфигурация загружена из config.txt")
            return default_config
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            return default_config
    
    def _create_default_config(self, config):
        """Создает файл конфигурации по умолчанию"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("# Computer Guard System Configuration\n")
                f.write("# This file contains settings for the application\n\n")
                
                for key, value in config.items():
                    if key == 'terminal_visible':
                        f.write(f"# terminal_visible options:\n")
                        f.write(f"# - true: Show terminal window (for debugging)\n")
                        f.write(f"# - false: Hide terminal window (for silent operation)\n")
                    f.write(f"{key}={value}\n\n")
            
            self.logger.info("📁 Создан файл конфигурации config.txt")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания конфигурации: {e}")
    
    def get(self, key, default=None):
        """Получает значение настройки"""
        return self.settings.get(key, default)
    
    def get_bool(self, key, default=False):
        """Получает булево значение"""
        value = self.settings.get(key, str(default)).lower()
        return value in ('true', 'yes', '1', 'on')
    
    def get_int(self, key, default=0):
        """Получает целочисленное значение"""
        try:
            return int(self.settings.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def update_setting(self, key, value):
        """Обновляет настройку в файле"""
        try:
            # Читаем текущий файл
            lines = []
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Обновляем или добавляем настройку
            key_found = False
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and '=' in line:
                    current_key = line.split('=')[0].strip()
                    if current_key == key:
                        lines[i] = f"{key}={value}\n"
                        key_found = True
                        break
            
            if not key_found:
                lines.append(f"{key}={value}\n")
            
            # Записываем обратно
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Обновляем в памяти
            self.settings[key] = value
            
            self.logger.info(f"✅ Настройка {key} обновлена на {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления настройки: {e}")
            return False