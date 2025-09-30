import logging
from typing import Dict, Optional, List
import os
from datetime import datetime
import requests
import json

class SupabaseStorage:
    """Хранилище данных в Supabase через REST API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Получаем ключи из переменных окружения
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            self.logger.error("❌ SUPABASE_URL или SUPABASE_KEY не установлены!")
            raise ValueError("Требуются переменные окружения Supabase")
        
        # Настраиваем заголовки для REST API
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        self.logger.info("✅ Supabase REST API клиент инициализирован")
        self._test_connection()
    
    def _test_connection(self):
        """Проверяет подключение к Supabase"""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/users?select=id&limit=1",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Подключение к Supabase успешно")
            else:
                self.logger.error(f"❌ Ошибка подключения: {response.status_code}")
                raise ConnectionError(f"Supabase вернул статус {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения к Supabase: {e}")
            raise
    
    def _make_request(self, method, endpoint, data=None):
        """Выполняет запрос к Supabase REST API"""
        try:
            url = f"{self.url}/rest/v1/{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Неизвестный метод: {method}")
            
            if response.status_code in [200, 201, 204]:
                return response.json() if response.content else True
            else:
                self.logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка запроса к Supabase: {e}")
            return None
    
    def register_user(self, user_id: int, computer_id: str, username: str = None, first_name: str = None) -> bool:
        """Регистрирует пользователя и привязывает компьютер"""
        try:
            # Проверяем, не занят ли computer_id другим пользователем
            existing_user = self._make_request(
                'GET', 
                f"users?computer_id=eq.{computer_id}&select=user_id"
            )
            
            if existing_user and existing_user[0]['user_id'] != user_id:
                self.logger.warning(f"⚠️ Computer {computer_id} уже привязан к другому пользователю")
                return False
            
            # Данные пользователя
            user_data = {
                'user_id': user_id,
                'computer_id': computer_id,
                'username': username,
                'first_name': first_name,
                'registered_at': datetime.now().isoformat()
            }
            
            # Используем upsert через ON CONFLICT
            response = self._make_request(
                'POST',
                'users',
                user_data
            )
            
            if response:
                self.logger.info(f"✅ Пользователь {user_id} привязал компьютер {computer_id}")
                return True
            else:
                # Пробуем обновить если пользователь уже существует
                update_response = self._make_request(
                    'PUT',
                    f"users?user_id=eq.{user_id}",
                    user_data
                )
                
                if update_response:
                    self.logger.info(f"✅ Данные пользователя {user_id} обновлены")
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
            response = self._make_request(
                'GET',
                f"users?computer_id=eq.{computer_id}&select=user_id"
            )
            
            if response and len(response) > 0:
                return response[0]['user_id']
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска пользователя: {e}")
            return None
    
    def get_computer_by_user_id(self, user_id: int) -> Optional[str]:
        """Находит computer_id по user_id"""
        try:
            response = self._make_request(
                'GET',
                f"users?user_id=eq.{user_id}&select=computer_id"
            )
            
            if response and len(response) > 0:
                return response[0]['computer_id']
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска компьютера: {e}")
            return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        try:
            response = self._make_request(
                'GET',
                f"users?user_id=eq.{user_id}"
            )
            
            if response and len(response) > 0:
                return response[0]
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
            
            response = self._make_request('POST', 'alerts', alert_data)
            
            if response:
                self.logger.info(f"📊 Сохранено уведомление для {computer_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения уведомления: {e}")
            return False
    
    def get_alerts_by_computer(self, computer_id: str, limit: int = 10) -> List[Dict]:
        """Получает уведомления для компьютера"""
        try:
            response = self._make_request(
                'GET',
                f"alerts?computer_id=eq.{computer_id}&order=created_at.desc&limit={limit}"
            )
            
            return response if response else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения уведомлений: {e}")
            return []
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Получает последние уведомления"""
        try:
            response = self._make_request(
                'GET',
                f"alerts?order=created_at.desc&limit={limit}"
            )
            
            return response if response else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения последних уведомлений: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """Получает всех пользователей"""
        try:
            response = self._make_request('GET', 'users')
            return response if response else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения пользователей: {e}")
            return []
    
    def get_all_computers(self) -> List[Dict]:
        """Получает все компьютеры"""
        try:
            response = self._make_request('GET', 'users?select=computer_id,user_id,username,registered_at')
            return response if response else []
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения компьютеров: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Получает статистику системы"""
        try:
            # Получаем количество пользователей
            users_response = self._make_request('GET', 'users?select=id')
            users_count = len(users_response) if users_response else 0
            
            # Получаем количество уведомлений
            alerts_response = self._make_request('GET', 'alerts?select=id')
            alerts_count = len(alerts_response) if alerts_response else 0
            
            return {
                "total_users": users_count,
                "total_computers": users_count,  # Один пользователь = один компьютер
                "total_alerts": alerts_count,
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
            response = self._make_request('DELETE', f"users?user_id=eq.{user_id}")
            return response is not None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка удаления пользователя: {e}")
            return False