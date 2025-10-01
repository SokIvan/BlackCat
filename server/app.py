from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Optional
import os
from pathlib import Path
import asyncio

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

async def set_webhook():
    """Устанавливает webhook для Telegram бота"""
    global telegram_bot
    try:
        # Получаем URL приложения
        webhook_url = os.getenv('RENDER_EXTERNAL_URL')
        if not webhook_url:
            # Если переменная не установлена, используем базовый URL Render
            render_app_name = os.getenv('RENDER_APP_NAME')
            if render_app_name:
                webhook_url = f"https://{render_app_name}.onrender.com"
            else:
                logger.error("❌ Не удалось определить URL для webhook")
                return False
        
        webhook_path = f"{webhook_url}/webhook"
        logger.info(f"🔄 Установка webhook: {webhook_path}")
        
        if telegram_bot:
            # Удаляем старый webhook перед установкой нового
            await telegram_bot.bot.delete_webhook()
            
            # Устанавливаем новый webhook
            await telegram_bot.bot.set_webhook(webhook_path)
            logger.info(f"✅ Webhook установлен: {webhook_path}")
            return True
        else:
            logger.error("❌ Бот не инициализирован для установки webhook")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        return False

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
        
        # Устанавливаем webhook при старте
        webhook_success = await set_webhook()
        if webhook_success:
            logger.info("🚀 Webhook успешно настроен")
        else:
            logger.warning("⚠️ Не удалось настроить webhook, бот будет работать в режиме polling")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Обработчик webhook от Telegram"""
    global telegram_bot
    try:
        # Получаем данные запроса
        data = await request.json()
        logger.debug(f"📨 Получен webhook запрос от Telegram")
        
        # Обрабатываем обновление через бота
        if telegram_bot:
            from aiogram.types import Update
            update = Update(**data)
            await telegram_bot.dp.feed_update(telegram_bot.bot, update)
            return JSONResponse(content={"status": "ok"})
        else:
            logger.error("❌ Бот не доступен для обработки webhook")
            return JSONResponse(content={"status": "error", "message": "Bot not available"}, status_code=503)
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.get("/webhook")
async def get_webhook():
    """GET endpoint для проверки webhook"""
    return {
        "status": "webhook_is_ready", 
        "message": "Webhook endpoint is working",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

@app.get("/set-webhook")
async def manual_set_webhook():
    """Ручная установка webhook (для отладки)"""
    try:
        success = await set_webhook()
        if success:
            return {"status": "success", "message": "Webhook set manually"}
        else:
            return {"status": "error", "message": "Failed to set webhook"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/delete-webhook")
async def delete_webhook():
    """Удаление webhook (для отладки)"""
    global telegram_bot
    try:
        if telegram_bot:
            await telegram_bot.bot.delete_webhook()
            return {"status": "success", "message": "Webhook deleted"}
        else:
            return {"status": "error", "message": "Bot not available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/webhook-info")
async def webhook_info():
    """Информация о текущем webhook"""
    global telegram_bot
    try:
        if telegram_bot:
            webhook_info = await telegram_bot.bot.get_webhook_info()
            return {
                "status": "success",
                "webhook_info": {
                    "url": webhook_info.url,
                    "has_custom_certificate": webhook_info.has_custom_certificate,
                    "pending_update_count": webhook_info.pending_update_count,
                    "ip_address": webhook_info.ip_address,
                    "last_error_date": webhook_info.last_error_date,
                    "last_error_message": webhook_info.last_error_message,
                    "max_connections": webhook_info.max_connections,
                    "allowed_updates": webhook_info.allowed_updates
                }
            }
        else:
            return {"status": "error", "message": "Bot not available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ... остальные endpointы без изменений ...

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
    global telegram_bot
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
    global telegram_bot
    bot_status = "active" if telegram_bot else "inactive"
    
    # Получаем информацию о webhook
    webhook_status = "unknown"
    if telegram_bot:
        try:
            webhook_info = await telegram_bot.bot.get_webhook_info()
            webhook_status = "configured" if webhook_info.url else "not_configured"
        except:
            webhook_status = "error"
    
    return {
        "message": "Computer Guard API работает!",
        "version": "1.0",
        "status": "healthy",
        "telegram_bot": bot_status,
        "webhook": webhook_status,
        "endpoints": {
            "webhook": "POST /webhook",
            "webhook_info": "GET /webhook-info",
            "set_webhook": "GET /set-webhook",
            "delete_webhook": "GET /delete-webhook",
            "alert": "POST /api/alert",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    global telegram_bot
    bot_alive = telegram_bot is not None
    return {
        "status": "healthy",
        "telegram_bot": "alive" if bot_alive else "inactive",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)