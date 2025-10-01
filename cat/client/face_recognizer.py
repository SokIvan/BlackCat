import cv2
import pickle
import os
import logging
import numpy as np
from pathlib import Path
import json

class FaceRecognizer:
    """Распознавание лиц используя LBPH из OpenCV"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)  # ДОБАВЬТЕ ЭТУ СТРОКУ
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.known_face_names = []
        self.label_map = {}
        self.load_trained_model()
    
    def load_trained_model(self):
        """Загружает обученную модель"""
        model_path = Path("known_faces_db/face_model.yml")
        labels_path = Path("known_faces_db/labels.json")
        
        if not model_path.exists() or not labels_path.exists():
            self.logger.error("❌ Модель не найдена! Сначала обучите систему.")
            return False
        
        try:
            # Загружаем модель
            self.recognizer.read(str(model_path))
            
            # Загружаем метки
            with open(labels_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.known_face_names = data['names']
                self.label_map = data['label_map']
            
            self.logger.info(f"✅ Загружена модель для {len(self.known_face_names)} лиц")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели: {e}")
            return False
    
    def is_stranger(self, face_image):
        """
        Проверяет, является ли лицо незнакомцем
        Возвращает True если лицо НЕ найдено в базе известных
        """
        if not self.known_face_names:
            self.logger.warning("Модель не загружена - все лица считаются незнакомцами")
            return True
        
        try:
            # Преобразуем в grayscale
            gray_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Изменяем размер для стандартизации
            gray_face = cv2.resize(gray_face, (100, 100))
            
            # Пытаемся распознать лицо
            label, confidence = self.recognizer.predict(gray_face)
            
            # confidence < 50 - хорошее совпадение, > 80 - плохое
            if confidence < 70:  # Пороговое значение
                name = self.known_face_names[label]
                self.logger.debug(f"✅ Распознан: {name} (уверенность: {confidence:.1f})")
                return False
            else:
                self.logger.info(f"👤 Обнаружен незнакомец! (уверенность: {confidence:.1f})")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка распознавания лица: {e}")
            return True