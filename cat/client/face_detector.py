import cv2
import mediapipe as mp
import logging
import numpy as np

class FaceDetector:
    """Детектор лиц используя MediaPipe - находит ЛЮБЫЕ лица"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Инициализация MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0 для ближних лиц, 1 для дальних
            min_detection_confidence=0.5
        )
        
        self.logger.info("✅ Детектор лиц (MediaPipe) инициализирован")
    
    def detect_faces(self, image):
        """
        Находит все лица на изображении используя MediaPipe
        Возвращает список bounding boxes: [(x, y, width, height), ...]
        """
        try:
            # Конвертируем BGR в RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Детектируем лица
            results = self.face_detection.process(rgb_image)
            
            faces = []
            if results.detections:
                for detection in results.detections:
                    # Получаем bounding box
                    bboxC = detection.location_data.relative_bounding_box
                    h, w, _ = image.shape
                    
                    # Конвертируем в абсолютные координаты
                    x = int(bboxC.xmin * w)
                    y = int(bboxC.ymin * h)
                    width = int(bboxC.width * w)
                    height = int(bboxC.height * h)
                    
                    faces.append((x, y, width, height))
            
            return faces
            
        except Exception as e:
            self.logger.error(f"Ошибка детекции лиц: {e}")
            return []
    
    def __del__(self):
        """Закрываем ресурсы MediaPipe"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()