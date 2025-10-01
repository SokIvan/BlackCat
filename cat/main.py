#!/usr/bin/env python3
"""
Главный файл системы охраны компьютера
"""

import sys
import logging
from pathlib import Path
import os

# Загружаем конфигурацию ДО настройки логирования
try:
    from config_loader import ConfigLoader
    config = ConfigLoader()
    
    # Настройка логирования на основе config.txt
    log_level = getattr(logging, config.get('log_level', 'INFO'))
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
except ImportError:
    # Fallback если модуль конфигурации не доступен
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    config = None

def main():
    """Главная функция"""
    print("🛡️ COMPUTER GUARD SYSTEM")
    print("=" * 50)
    
    # Проверяем конфигурацию
    if config:
        terminal_visible = config.get_bool('terminal_visible', True)
        detection_threshold = config.get_int('detection_threshold', 20)
        alert_time_window = config.get_int('alert_time_window', 60)
        
        print(f"📊 Настройки из config.txt:")
        print(f"   👁️  Terminal visible: {terminal_visible}")
        print(f"   🎯 Detection threshold: {detection_threshold}")
        print(f"   ⏱️  Alert time window: {alert_time_window}")
    else:
        print("⚠️  Конфигурация не загружена, используются настройки по умолчанию")
        terminal_visible = True
    
    # Проверяем, обучена ли модель
    if not Path("known_faces_db/face_model.yml").exists():
        print("❌ Модель не обучена!")
        print("💡 Сначала обучите систему:")
        print("   python scripts/face_trainer.py")
        return
    
    # Запускаем систему охраны
    try:
        from client.computer_guard import ComputerGuard
        
        # Передаем настройки в охранную систему
        guard = ComputerGuard(config=config)
        
        print("\n🚀 Запуск системы охраны...")
        print("💡 Нажмите Ctrl+C для остановки")
        print("=" * 50)
        
        guard.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n⛔ Остановка системы...")
        if 'guard' in locals():
            guard.stop_monitoring()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
    
    # Пауза если терминал видимый
    if terminal_visible:
        input("\n🎯 Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()