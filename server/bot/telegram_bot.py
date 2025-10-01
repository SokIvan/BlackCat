import logging
from typing import Optional
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import asyncio

from supabase_storage import SupabaseStorage

class TelegramBot:
    def __init__(self, token: str = None):
        self.logger = logging.getLogger(__name__)
        
        if not token:
            self.logger.error("❌ Не предоставлен Telegram токен!")
            raise ValueError("Требуется Telegram токен")
        
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.data_manager = SupabaseStorage()
        
        self._register_handlers()
        self.logger.info("✅ Telegram бот (aiogram) инициализирован с Webhook")
    
    def _register_handlers(self):
        """Регистрирует обработчики команд aiogram"""
        self.dp.message(Command("start"))(self._start_command)
        self.dp.message(Command("register"))(self._register_command)
        self.dp.message(Command("help"))(self._help_command)
        self.dp.message(Command("status"))(self._status_command)
        self.dp.message(Command("stats"))(self._stats_command)
        self.dp.message(Command("alerts"))(self._alerts_command)
        self.dp.message(Command("wakeup"))(self._wakeup_command)  # Новая команда для "пробуждения"
    
    async def _wakeup_command(self, message: Message):
        """Команда для принудительного пробуждения сервера"""
        await message.answer(
            "🔔 <b>Сервер пробужден!</b>\n\n"
            "Теперь вы можете использовать все команды:\n"
            "/start - начать работу\n"
            "/register - привязать компьютер\n"
            "/status - статус системы\n"
            "/stats - статистика\n"
            "/alerts - история уведомлений\n"
            "/help - справка"
        )
        self.logger.info(f"🔔 Сервер пробужден пользователем {message.from_user.id}")
    
    async def _start_command(self, message: Message):
        """Обработчик команды /start"""
        await message.answer(
            "🛡️ <b>BlackCat</b>\n\n"
            "Я буду отправлять вам уведомления когда кто-то посторонний "
            "сядет за ваш компьютер.\n\n"
            "<b>Доступные команды:</b>\n"
            "/register - привязать компьютер\n"
            "/status - статус системы\n" 
            "/alerts - история уведомлений\n"
            "/stats - статистика\n"
            "/help - справка\n\n"
            "💡 <i>Сервер может \"засыпать\" после 15 минут неактивности. "
            "Если команды не работают, отправьте /wakeup</i>"
        )
        self.logger.info(f"👤 Пользователь {message.from_user.id} запустил бота")
    
    async def _register_command(self, message: Message):
        """Обработчик команды /register"""
        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.answer(
                    "❌ Неправильный формат команды.\n"
                    "Используйте: <code>/register COMPUTER_ID</code>\n\n"
                    "Пример: <code>/register A1B2C3D4</code>\n\n"
                    "💡 ID компьютера можно найти в файле computer_config.json "
                    "на вашем компьютере"
                )
                return
            
            computer_id = parts[1].strip().upper()
            user_id = message.from_user.id
            
            # Проверяем, не привязан ли уже этот компьютер к другому пользователю
            existing_user = self.data_manager.get_user_by_computer_id(computer_id)
            if existing_user and existing_user != user_id:
                await message.answer(
                    "❌ Этот компьютер уже привязан к другому пользователю!\n\n"
                    "💡 Каждый компьютер можно привязать только к одному пользователю."
                )
                return
            
            # Регистрируем пользователя
            success = self.data_manager.register_user(
                user_id=user_id,
                computer_id=computer_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            
            if success:
                await message.answer(
                    f"✅ Компьютер <code>{computer_id}</code> успешно привязан!\n\n"
                    "Теперь вы будете получать уведомления когда система обнаружит "
                    "незнакомца за вашим компьютером.\n\n"
                    "Проверить статус: /status\n"
                    "История уведомлений: /alerts"
                )
            else:
                await message.answer("❌ Ошибка привязки компьютера")
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации: {e}")
            await message.answer("❌ Ошибка привязки компьютера")
    
    async def _status_command(self, message: Message):
        """Обработчик команды /status"""
        try:
            user_id = message.from_user.id
            computer_id = self.data_manager.get_computer_by_user_id(user_id)
            
            if computer_id:
                # Получаем историю уведомлений
                user_alerts = self.data_manager.get_alerts_by_computer(computer_id)
                total_alerts = len(user_alerts)
                recent_alerts = user_alerts[-3:]  # Последние 3 уведомления
                
                status_text = (
                    f"📊 <b>Статус вашей системы</b>\n\n"
                    f"💻 Привязанный компьютер: <code>{computer_id}</code>\n"
                    f"👤 Ваш ID: <code>{user_id}</code>\n"
                    f"📨 Всего уведомлений: {total_alerts}\n"
                    f"✅ Система активна и отслеживает незнакомцев"
                )
                
                if recent_alerts:
                    status_text += "\n\n<b>Последние уведомления:</b>\n"
                    for alert in reversed(recent_alerts):
                        status_text += f"• {alert['timestamp'][:16]} - {alert['detection_count']} обнаружений\n"
                
                await message.answer(status_text)
            else:
                await message.answer(
                    "❌ У вас нет привязанных компьютеров.\n\n"
                    "Используйте: <code>/register COMPUTER_ID</code>\n\n"
                    "💡 ID компьютера можно найти в файле computer_config.json "
                    "на вашем компьютере"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки статуса: {e}")
            await message.answer("❌ Ошибка проверки статуса")
    
 
    async def _help_command(self, message: Message):
        """Обработчик команды /help"""
        await message.answer(
            "<b>BlackCat - Помощь</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - начать работу\n"
            "/register COMPUTER_ID - привязать компьютер\n"
            "/stats - статистика системы\n"
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
        """Отправляет уведомление пользователю"""
        try:
            # Находим пользователя по computer_id
            user_chat_id = self.data_manager.get_user_by_computer_id(computer_id)
            
            if not user_chat_id:
                self.logger.error(f"❌ Не найден пользователь для компьютера {computer_id}")
                return False
            
            # Сохраняем уведомление в историю
            self.data_manager.save_alert(computer_id, detection_count, message)
            
            # Формируем сообщение
            alert_message = (
                f"🚨 <b>ОБНАРУЖЕН НЕЗНАКОМЕЦ!</b>\n\n"
                f"💻 Компьютер: <code>{computer_id}</code>\n"
                f"📊 Количество обнаружений: {detection_count}\n"
                f"🕐 Время: {timestamp}\n"
                f"📝 {message}\n\n"
                f"📈 Посмотреть историю: /alerts"
            )
            
            # Отправляем текстовое сообщение
            await self.bot.send_message(chat_id=user_chat_id, text=alert_message)
            
            # Отправляем фото если есть
            if stranger_photo_path and Path(stranger_photo_path).exists():
                try:
                    photo = FSInputFile(stranger_photo_path)
                    await self.bot.send_photo(
                        chat_id=user_chat_id,
                        photo=photo,
                        caption="📸 Обнаруженное лицо"
                    )
                except Exception as e:
                    self.logger.error(f"❌ Ошибка отправки фото: {e}")
            
            # Отправляем скриншот если есть
            if screenshot_path and Path(screenshot_path).exists():
                try:
                    screenshot = FSInputFile(screenshot_path)
                    await self.bot.send_photo(
                        chat_id=user_chat_id,
                        photo=screenshot,
                        caption="🖥️ Скриншот рабочего стола"
                    )
                except Exception as e:
                    self.logger.error(f"❌ Ошибка отправки скриншота: {e}")
            
            self.logger.info(f"✅ Уведомление отправлено пользователю {user_chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки уведомления: {e}")
            return False

# Глобальный экземпляр бота для доступа из app.py
telegram_bot: Optional[TelegramBot] = None

async def create_bot():
    """Создает и возвращает экземпляр бота"""
    global telegram_bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        telegram_bot = TelegramBot(token=token)
    return telegram_bot