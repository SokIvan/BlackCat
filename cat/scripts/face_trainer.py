import cv2
import os
import logging
import numpy as np
from pathlib import Path
import json

class FaceTrainer:
    """Обучает систему на датасете известных лиц используя OpenCV LBPH"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    def train_from_dataset(self, dataset_path="face_dataset"):
        """
        Обучает систему на датасете известных лиц
        Возвращает True если обучение успешно
        """
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            self.logger.error(f"❌ Папка с датасетом не найдена: {dataset_path}")
            return False
        
        faces = []
        labels = []
        label_map = {}
        current_label = 0
        known_face_names = []
        
        self.logger.info("🎯 Начинаем обучение на датасете...")
        
        # Проходим по всем персонажам в датасете
        for person_dir in dataset_path.iterdir():
            if not person_dir.is_dir():
                continue
                
            person_name = person_dir.name
            self.logger.info(f"👤 Обрабатываем: {person_name}")
            
            # Назначаем метку для этого человека
            label_map[current_label] = person_name
            known_face_names.append(person_name)
            
            image_count = 0
            
            # ИСПРАВЛЕНИЕ: Правильно объединяем генераторы
            image_files = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png")) + list(person_dir.glob("*.jpeg"))
            
            for img_path in image_files:
                try:
                    # Загружаем изображение
                    image = cv2.imread(str(img_path))
                    
                    if image is None:
                        self.logger.warning(f"  ⚠️ Не удалось загрузить: {img_path.name}")
                        continue
                    
                    # Конвертируем в grayscale
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    
                    # Изменяем размер для стандартизации
                    gray = cv2.resize(gray, (100, 100))
                    
                    # Добавляем в данные для обучения
                    faces.append(gray)
                    labels.append(current_label)
                    image_count += 1
                    
                    self.logger.debug(f"  ✅ Обработано: {img_path.name}")
                        
                except Exception as e:
                    self.logger.error(f"  ❌ Ошибка обработки {img_path}: {e}")
                    continue
            
            self.logger.info(f"  📊 Для {person_name} обработано изображений: {image_count}")
            
            if image_count == 0:
                self.logger.warning(f"  ⚠️ В папке {person_name} не найдено подходящих изображений!")
            else:
                current_label += 1
        
        if len(faces) == 0:
            self.logger.error("❌ Не найдено ни одного лица в датасете!")
            return False
        
        # Обучаем модель
        self.logger.info("🧠 Обучаем модель LBPH...")
        self.recognizer.train(faces, np.array(labels))
        
        # Сохраняем модель и метки
        db_path = Path("known_faces_db")
        db_path.mkdir(exist_ok=True)
        
        # Сохраняем модель
        self.recognizer.save(str(db_path / "face_model.yml"))
        
        # Сохраняем метки
        labels_data = {
            'names': known_face_names,
            'label_map': label_map,
            'total_samples': len(faces),
            'unique_persons': len(known_face_names)
        }
        
        with open(db_path / "labels.json", 'w', encoding='utf-8') as f:
            json.dump(labels_data, f, indent=2, ensure_ascii=False)
        
        # Сохраняем метаданные
        import datetime
        metadata = {
            'total_faces': len(faces),
            'unique_persons': len(known_face_names),
            'trained_at': str(datetime.datetime.now()),
            'model_used': 'OpenCV_LBPH'
        }
        
        with open(db_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Обучение завершено успешно!")
        self.logger.info(f"📊 Всего образцов: {len(faces)}")
        self.logger.info(f"👥 Уникальных персонажей: {len(known_face_names)}")
        
        return True

def main():
    """Главная функция обучения"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🎯 ОБУЧЕНИЕ СИСТЕМЫ РАСПОЗНАВАНИЯ ЛИЦ (OpenCV LBPH)")
    print("=" * 50)
    
    # Проверяем наличие OpenCV с модулем face
    try:
        import cv2
        cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        print("❌ Ошибка: В вашей версии OpenCV нет модуля face!")
        print("💡 Решение: Установите opencv-contrib-python:")
        print("   pip uninstall opencv-python")
        print("   pip install opencv-contrib-python")
        return
    
    trainer = FaceTrainer()
    
    # Проверяем наличие датасета
    if not Path("face_dataset").exists():
        print("❌ Папка 'face_dataset' не найдена!")
        print("📁 Создайте структуру:")
        print("face_dataset/")
        print("├── owner/       # Ваши фото (10-15 штук)")
        print("├── person1/     # Другие известные люди")
        print("└── ...")
        print("\n💡 Советы по фото:")
        print("- Хорошее освещение")
        print("- Разные ракурсы")
        print("- Разные выражения лица")
        print("- Размер фото: минимум 100x100 пикселей")
        return
    
    # Проверяем, есть ли фото в папках
    has_images = False
    for person_dir in Path("face_dataset").iterdir():
        if person_dir.is_dir():
            images = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png")) + list(person_dir.glob("*.jpeg"))
            if images:
                has_images = True
                print(f"📁 {person_dir.name}: {len(images)} изображений")
    
    if not has_images:
        print("❌ В папках датасета не найдено изображений!")
        print("💡 Добавьте фото в формате JPG, PNG или JPEG")
        return
    
    # Запускаем обучение
    success = trainer.train_from_dataset()
    
    if success:
        print("\n✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
        print("💡 Теперь можно запустить систему охраны:")
        print("   python main.py")
    else:
        print("\n❌ ОБУЧЕНИЕ НЕ УДАЛОСЬ!")

if __name__ == "__main__":
    main()