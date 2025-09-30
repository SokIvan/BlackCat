from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Optional
import os
from pathlib import Path
import asyncio
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Computer Guard API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальная переменная для бота
telegram_bot = None

def start_bot_polling():
    """Запускает поллинг бота в отдельном потоке"""
    try:
        from bot.telegram_bot import TelegramBot
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            return
        
        bot = TelegramBot(token=token)
        
        # Запускаем поллинг в event loop
        import asyncio
        asyncio.run(bot.start_polling())
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    global telegram_bot
    
    try:
        from bot.telegram_bot import TelegramBot
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
            return
        
        telegram_bot = TelegramBot(token=token)
        logger.info("✅ Telegram бот инициализирован при старте")
        
        # Запускаем поллинг в фоновом потоке
        bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
        bot_thread.start()
        logger.info("🚀 Поллинг бота запущен в фоновом режиме")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")

async def process_alert_background(
    computer_id: str,
    command: str,
    timestamp: str,
    detection_count: int,
    message: str,
    stranger_photo_path: Optional[str] = None,
    screenshot_path: Optional[str] = None
):
    """Фоновая обработка уведомления"""
    try:
        if telegram_bot:
            success = await telegram_bot.send_alert_to_user(
                computer_id=computer_id,
                message=message,
                detection_count=detection_count,
                timestamp=timestamp,
                stranger_photo_path=stranger_photo_path,
                screenshot_path=screenshot_path
            )
            if success:
                logger.info(f"✅ Уведомление отправлено для компьютера {computer_id}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление для компьютера {computer_id}")
        else:
            logger.warning("⚠️ Telegram бот не доступен, уведомление не отправлено")
            
    except Exception as e:
        logger.error(f"❌ Ошибка фоновой обработки: {e}")
    finally:
        # Удаляем временные файлы
        for file_path in [stranger_photo_path, screenshot_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"🗑️ Удален временный файл: {file_path}")
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления файла {file_path}: {e}")

@app.post("/api/alert")
async def receive_alert(
    background_tasks: BackgroundTasks,
    computer_id: str = Form(...),
    command: str = Form(...),
    timestamp: str = Form(...),
    detection_count: int = Form(...),
    message: str = Form(...),
    stranger_photo: Optional[UploadFile] = File(None),
    screenshot: Optional[UploadFile] = File(None)
):
    """
    Endpoint для получения уведомлений от клиентов
    """
    try:
        logger.info(f"📨 Получено уведомление от компьютера {computer_id}")
        
        # Сохраняем файлы временно
        saved_files = {}
        
        if stranger_photo:
            stranger_path = f"temp_stranger_{computer_id}.jpg"
            with open(stranger_path, "wb") as f:
                content = await stranger_photo.read()
                f.write(content)
            saved_files['stranger_photo'] = stranger_path
            logger.info(f"📸 Сохранено фото незнакомца: {stranger_path}")
        
        if screenshot:
            screenshot_path = f"temp_screenshot_{computer_id}.png"
            with open(screenshot_path, "wb") as f:
                content = await screenshot.read()
                f.write(content)
            saved_files['screenshot'] = screenshot_path
            logger.info(f"🖥️ Сохранен скриншот: {screenshot_path}")
        
        # Запускаем фоновую задачу для отправки уведомления
        background_tasks.add_task(
            process_alert_background,
            computer_id=computer_id,
            command=command,
            timestamp=timestamp,
            detection_count=detection_count,
            message=message,
            stranger_photo_path=saved_files.get('stranger_photo'),
            screenshot_path=saved_files.get('screenshot')
        )
        
        return {
            "status": "success", 
            "message": "Уведомление принято в обработку",
            "computer_id": computer_id
        }
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки уведомления: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    bot_status = "active" if telegram_bot else "inactive"
    return {
        "message": "Computer Guard API работает!",
        "version": "1.0",
        "status": "healthy",
        "telegram_bot": bot_status,
        "endpoints": {
            "alert": "POST /api/alert",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)