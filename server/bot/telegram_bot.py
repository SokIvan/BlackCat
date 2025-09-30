import logging
from typing import Optional
from pathlib import Path
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
import asyncio

class TelegramBot:
    def __init__(self, token: str = None, config_path: str = "bot_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path, token)
        
        if self.config['telegram_token'] == "YOUR_BOT_TOKEN_HERE":
            self.logger.error("❌ Не установлен Telegram токен!")
            raise ValueError("Установите TELEGRAM_TOKEN в bot_config.json")
        
        self.bot = Bot(
            token=self.config['telegram_token'],
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        
        self._register_handlers()
        self.logger.info("✅ Telegram бот (aiogram) инициализирован")
    
    def _load_config(self, config_path: str, token: str = None):
        """Загружает конфигурацию бота"""
        config_file = Path(config_path)
        default_config = {
            "telegram_token": token or "YOUR_BOT_TOKEN_HERE",
            "admin_chat_id": None
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфигурации бота: {e}")
        
        # Сохраняем конфиг
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def _register_handlers(self):
        """Регистрирует обработчики команд aiogram"""
        self.dp.message(Command("start"))(self._start_command)
        self.dp.message(Command("register"))(self._register_command)
        self.dp.message(Command("help"))(self._help_command)
    
    async def _start_command(self, message: Message):
        """Обработчик команды /start"""
        await message.answer(
            "🛡️ <b>Computer Guard Bot</b>\n\n"
            "Я буду отправлять вам уведомления когда кто-то посторонний "
            "сядет за ваш компьютер.\n\n"
            "Для привязки компьютера используйте:\n"
            "<code>/register YOUR_COMPUTER_ID</code>\n\n"
            "Для справки: /help"
        )
    
    async def _register_command(self, message: Message):
        """Обработчик команды /register"""
        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.answer(
                    "❌ Неправильный формат команды.\n"
                    "Используйте: <code>/register COMPUTER_ID</code>\n\n"
                    "Пример: <code>/register A1B2C3D4</code>"
                )
                return
            
            computer_id = parts[1].strip().upper()
            
            # Загружаем существующие регистрации
            registrations = {}
            reg_file = Path("user_registrations.json")
            if reg_file.exists():
                with open(reg_file, 'r', encoding='utf-8') as f:
                    registrations = json.load(f)
            
            # Сохраняем привязку пользователь -> компьютер
            registrations[str(message.from_user.id)] = {
                "computer_id": computer_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "registered_at": message.date.isoformat()
            }
            
            # Сохраняем в файл
            with open(reg_file, 'w', encoding='utf-8') as f:
                json.dump(registrations, f, indent=2, ensure_ascii=False)
            
            await message.answer(
                f"✅ Компьютер <code>{computer_id}</code> успешно привязан!\n\n"
                "Теперь вы будете получать уведомления когда система обнаружит незнакомца за вашим компьютером."
            )
            self.logger.info(f"📝 Пользователь {message.from_user.id} привязал компьютер {computer_id}")
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации: {e}")
            await message.answer("❌ Ошибка привязки компьютера")
    
    async def _help_command(self, message: Message):
        """Обработчик команды /help"""
        await message.answer(
            "🛡️ <b>Computer Guard Bot - Помощь</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - начать работу\n"
            "/register COMPUTER_ID - привязать компьютер\n"
            "/help - эта справка\n\n"
            "<b>Как использовать:</b>\n"
            "1. Установите программу на компьютер\n"
            "2. Запустите её и получите ID компьютера\n"
            "3. Привяжите ID через /register\n"
            "4. Получайте уведомления о незнакомцах!\n\n"
            "💡 <i>Программа работает в фоновом режиме и отслеживает появление неизвестных лиц перед камерой.</i>"
        )
    
    async def send_alert_to_user(
        self, 
        computer_id: str,
        message: str,
        detection_count: int,
        timestamp: str,
        stranger_photo_path: Optional[str] = None,
        screenshot_path: Optional[str] = None
    ):
        """Отправляет уведомление пользователю через aiogram"""
        try:
            # Находим пользователя по computer_id
            user_chat_id = await self._find_user_by_computer_id(computer_id)
            
            if not user_chat_id:
                self.logger.error(f"❌ Не найден пользователь для компьютера {computer_id}")
                return False
            
            # Формируем сообщение
            alert_message = (
                f"🚨 <b>ОБНАРУЖЕН НЕЗНАКОМЕЦ!</b>\n\n"
                f"💻 Компьютер: <code>{computer_id}</code>\n"
                f"📊 Количество обнаружений: {detection_count}\n"
                f"🕐 Время: {timestamp}\n"
                f"📝 {message}"
            )
            
            # Отправляем текстовое сообщение
            await self.bot.send_message(chat_id=user_chat_id, text=alert_message)
            
            # Отправляем фото если есть
            if stranger_photo_path and Path(stranger_photo_path).exists():
                photo = FSInputFile(stranger_photo_path)
                await self.bot.send_photo(
                    chat_id=user_chat_id,
                    photo=photo,
                    caption="📸 Обнаруженное лицо"
                )
            
            # Отправляем скриншот если есть
            if screenshot_path and Path(screenshot_path).exists():
                screenshot = FSInputFile(screenshot_path)
                await self.bot.send_photo(
                    chat_id=user_chat_id,
                    photo=screenshot,
                    caption="🖥️ Скриншот рабочего стола"
                )
            
            self.logger.info(f"✅ Уведомление отправлено пользователю {user_chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки уведомления: {e}")
            return False
    
    async def _find_user_by_computer_id(self, computer_id: str) -> Optional[int]:
        """Находит chat_id пользователя по computer_id"""
        try:
            reg_file = Path("user_registrations.json")
            if reg_file.exists():
                with open(reg_file, 'r', encoding='utf-8') as f:
                    registrations = json.load(f)
                
                for chat_id_str, user_data in registrations.items():
                    if user_data.get('computer_id') == computer_id:
                        return int(chat_id_str)
            
            self.logger.warning(f"⚠️ Компьютер {computer_id} не привязан к пользователю")
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска пользователя: {e}")
            return None
    
    async def start_polling(self):
        """Запускает бота (для отдельного запуска)"""
        self.logger.info("🚀 Запуск Telegram бота...")
        await self.dp.start_polling(self.bot)