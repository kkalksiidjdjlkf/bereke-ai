import cv2
from ultralytics import YOLO
from deepface import DeepFace
import logging

# Отключаем лишние логи от DeepFace, чтобы не спамили в консоль
logging.disable(logging.SET_LEVEL)

# 1. Загружаем модель YOLOv8 (ищет людей)
model = YOLO('yolov8n.pt') 

cap = cv2.VideoCapture(0)

print("Система запущена. Нажми 'q' для выхода.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # 2. YOLO ищет и отслеживает людей (трекинг)
    results = model.track(frame, persist=True, classes=[0], verbose=False)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.int().cpu().tolist()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = box
            
            # ВЫРЕЗАЕМ КРОП ЧЕЛОВЕКА
            person_crop = frame[max(0, y1):y2, max(0, x1):x2]
            
            emotion_text = "Scanning..."
            
            # --- БЛОК АНАЛИЗА ЭМОЦИЙ ---
            try:
                # DeepFace анализирует вырезанную область
                # enforce_detection=False позволяет не "падать", если лицо нечеткое
                analysis = DeepFace.analyze(person_crop, actions=['emotion'], enforce_detection=False, silent=True)
                
                # Берем доминирующую эмоцию
                emotion_text = analysis[0]['dominant_emotion']
            except Exception as e:
                emotion_text = "Error"
            # ---------------------------

            # РИСУЕМ РЕЗУЛЬТАТ
            # Рамка вокруг человека
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Фон для текста (черная плашка)
            cv2.rectangle(frame, (x1, y1 - 35), (x1 + 220, y1), (0, 0, 0), -1)
            
            # Текст с ID и эмоцией
            display_info = f"ID:{track_id} | {emotion_text.upper()}"
            cv2.putText(frame, display_info, (x1 + 5, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Показываем общее кол-во людей
    count = len(results[0].boxes) if results[0].boxes.id is not None else 0
    cv2.putText(frame, f"People in room: {count}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("YOLO + Emotion AI", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()