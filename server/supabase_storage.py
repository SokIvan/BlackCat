import logging
from typing import Dict, Optional, List
from supabase import create_client, Client
import os
from datetime import datetime

class SupabaseStorage:
    """Хранилище данных в Supabase"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Получаем ключи из переменных окружения
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            self.logger.error("❌ SUPABASE_URL или SUPABASE_KEY не установлены!")
            raise ValueError("Требуются переменные окружения Supabase")
        
        try:
            self.client: Client = create_client(self.url, self.key)
            self.logger.info("✅ Supabase клиент инициализирован")
            
            # Проверяем подключение
            response = self.client.from_('users').select('count', count='exact').limit(1).execute()
            self.logger.info("✅ Подключение к Supabase успешно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения к Supabase: {e}")
            raise
    
    def register_user(self, user_id: int, computer_id: str, username: str = None, first_name: str = None) -> bool:
        """Регистрирует пользователя и привязывает компьютер"""
        try:
            # Проверяем, не занят ли computer_id другим пользователем
            existing_user = self.client.from_('users')\
                .select('user_id')\
                .eq('computer_id', computer_id)\
                .execute()
            
            if existing_user.data and existing_user.data[0]['user_id'] != user_id:
                self.logger.warning(f"⚠️ Computer {computer_id} уже привязан к другому пользователю")
                return False
            
            # Вставляем или обновляем пользователя
            user_data = {
                'user_id': user_id,
                'computer_id': computer_id,
                'username': username,
                'first_name': first_name,
                'registered_at': datetime.now().isoformat()
            }
            
            # Используем upsert (вставка или обновление)
            response = self.client.from_('users')\
                .upsert(user_data, on_conflict='user_id')\
                .execute()
            
            if response.data:
                self.logger.info(f"✅ Пользователь {user_id} привязал компьютер {computer_id}")
                return True
            else:
                self.logger.error("❌ Ошибка регистрации пользователя")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка регистрации пользователя: {e}")
            return False
    
    def get_user_by_computer_id(self, computer_id: str) -> Optional[int]:
        """Находит user_id по computer_id"""
        try:
            response = self.client.from_('users')\
                .select('user_id')\
                .eq('computer_id', computer_id)\
                .execute()
            
            if response.data:
                return response.data[0]['user_id']
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска пользователя: {e}")
            return None
    
    def get_computer_by_user_id(self, user_id: int) -> Optional[str]:
        """Находит computer_id по user_id"""
        try:
            response = self.client.from_('users')\
                .select('computer_id')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data:
                return response.data[0]['computer_id']
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска компьютера: {e}")
            return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        try:
            response = self.client.from_('users')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения информации о пользователе: {e}")
            return None
    
    def save_alert(self, computer_id: str, detection_count: int, message: str = None) -> bool:
        """Сохраняет уведомление в базу"""
        try:
            alert_data = {
                'computer_id': computer_id,
                'detection_count': detection_count,
                'message': message,
                'created_at': datetime.now().isoformat()
            }
            
            response = self.client.from_('alerts')\
                .insert(alert_data)\
                .execute()
            
            if response.data:
                self.logger.info(f"📊 Сохранено уведомление для {computer_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения уведомления: {e}")
            return False
    
    def get_alerts_by_computer(self, computer_id: str, limit: int = 10) -> List[Dict]:
        """Получает уведомления для компьютера"""
        try:
            response = self.client.from_('alerts')\
                .select('*')\
                .eq('computer_id', computer_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения уведомлений: {e}")
            return []
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Получает последние уведомления"""
        try:
            response = self.client.from_('alerts')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения последних уведомлений: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """Получает всех пользователей"""
        try:
            response = self.client.from_('users')\
                .select('*')\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения пользователей: {e}")
            return []
    
    def get_all_computers(self) -> List[Dict]:
        """Получает все компьютеры"""
        try:
            response = self.client.from_('users')\
                .select('computer_id, user_id, username, registered_at')\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения компьютеров: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Получает статистику системы"""
        try:
            # Получаем количество пользователей
            users_response = self.client.from_('users')\
                .select('id', count='exact')\
                .execute()
            
            # Получаем количество компьютеров
            computers_response = self.client.from_('users')\
                .select('computer_id', count='exact')\
                .execute()
            
            # Получаем количество уведомлений
            alerts_response = self.client.from_('alerts')\
                .select('id', count='exact')\
                .execute()
            
            return {
                "total_users": users_response.count or 0,
                "total_computers": computers_response.count or 0,
                "total_alerts": alerts_response.count or 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                "total_users": 0,
                "total_computers": 0,
                "total_alerts": 0,
                "last_updated": datetime.now().isoformat()
            }
    
    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя (для админки)"""
        try:
            response = self.client.from_('users')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка удаления пользователя: {e}")
            return False