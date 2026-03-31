"""
Роборука - 5 пальцев (кисть)
Управление через камеру
Arduino Uno + 5 сервоприводов SG90
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import vision
from mediapipe import solutions
import numpy as np
import serial
import time
from pathlib import Path
import os

# Настройки
ARDUINO_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600


class RobotHandController:
    """Контроллер роборуки - 5 пальцев"""
    
    def __init__(self, port=ARDUINO_PORT, baud=BAUD_RATE):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        
        # 5 пальцев: Большой, Указательный, Средний, Безымянный, Мизинец
        self.positions = [90, 90, 90, 90, 90]
        self.names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
        self.icons = ['👍', '☝️', '🖕', '💍', '🤙']
        
    def connect(self, port=None):
        """Подключение к Arduino."""
        ports_to_try = [
            port,
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
            "/dev/ttyACM0",
            "/dev/rfcomm0",
            "COM3", "COM4", "COM5"
        ]
        
        for p in ports_to_try:
            if p is None:
                continue
            try:
                self.arduino = serial.Serial(p, self.baud, timeout=1)
                time.sleep(2)
                self.connected = True
                self.port = p
                print(f"✓ Подключено к {p}")
                return True
            except Exception as e:
                print(f"✗ {p}: {e}")
        
        print("⚠ Режим симуляции")
        return False
    
    def disconnect(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.connected = False
    
    def send_command(self, cmd):
        """Отправка команды."""
        if self.connected and self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(f"{cmd}\n".encode())
                self.arduino.flush()
                response = self.arduino.readline().decode().strip()
                return response
            except Exception as e:
                return f"ERR: {e}"
        else:
            print(f"[SIM] {cmd}")
            return "SIM_OK"
    
    def set_positions(self, positions):
        """Установка позиций 5 пальцев."""
        angles = [max(0, min(180, int(p))) for p in positions[:5]]
        cmd = f"SET:{','.join(map(str, angles))}"
        result = self.send_command(cmd)
        
        if result in ["OK", "SET_OK", "SIM_OK"]:
            self.positions = angles
        
        return result
    
    def set_finger(self, finger_num, angle):
        """Установка одного пальца."""
        if 0 <= finger_num < 5:
            angle = max(0, min(180, int(angle)))
            cmd = f"FINGER:{finger_num},{angle}"
            result = self.send_command(cmd)
            self.positions[finger_num] = angle
            return result
        return "ERR: Invalid finger"
    
    def open_hand(self):
        """Открыть ладонь."""
        return self.send_command("OPEN")
    
    def grip(self):
        """Захват."""
        grip_positions = [45, 20, 20, 20, 20]
        return self.set_positions(grip_positions)
    
    def wave(self):
        """Помахать рукой."""
        return self.send_command("WAVE")
    
    def get_status(self):
        """Текущие позиции."""
        return self.send_command("STATUS")


def calculate_finger_angles(landmarks):
    """
    Расчёт углов 5 пальцев из позиции руки.
    landmarks: список из 21 точки
    """
    if len(landmarks) < 21:
        return [90, 90, 90, 90, 90]
    
    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]
    
    def dist(a, b):
        return np.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
    def finger_openness(tip, pip, max_open=0.12):
        d = dist(tip, pip)
        return min(d / max_open, 1.0)
    
    # Базовый угол (слегка согнутые пальцы)
    base_angle = 40
    
    # 5 пальцев
    index_angle = base_angle + finger_openness(index_tip, index_pip) * (180 - base_angle)
    middle_angle = base_angle + finger_openness(middle_tip, middle_pip) * (180 - base_angle)
    ring_angle = base_angle + finger_openness(ring_tip, ring_pip) * (180 - base_angle)
    pinky_angle = base_angle + finger_openness(pinky_tip, pinky_pip) * (180 - base_angle)
    
    # Большой палец (от запястья)
    thumb_open = dist(thumb_tip, wrist)
    thumb_angle = 45 + min(thumb_open / 0.15, 1.0) * 90
    
    return [
        int(np.clip(thumb_angle, 0, 180)),
        int(np.clip(index_angle, 0, 180)),
        int(np.clip(middle_angle, 0, 180)),
        int(np.clip(ring_angle, 0, 180)),
        int(np.clip(pinky_angle, 0, 180))
    ]


def draw_ui(frame, positions, names, icons, fps=0, connected=False):
    """Отрисовка интерфейса."""
    h, w = frame.shape[:2]
    
    # Панель UI
    ui_w = 260
    ui_h = 30 + len(names) * 35 + 50
    
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + ui_h), (0, 0, 0), -1)
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + ui_h), (0, 255, 0), 2)
    
    # Заголовок
    cv2.putText(frame, "ROBOT HAND", (w - ui_w, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Статус
    status = "CONNECTED" if connected else "OFFLINE"
    color = (0, 255, 0) if connected else (0, 0, 255)
    cv2.putText(frame, status, (w - 120, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 60, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Позиции пальцев
    for i, (pos, name, icon) in enumerate(zip(positions, names, icons)):
        y = 55 + i * 35
        bar_color = (0, 255, 0) if pos > 100 else (0, 255, 255)
        
        # Прогресс бар
        bar_w = int((pos / 180) * (ui_w - 70))
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - 35, y + 18), (30, 30, 30), -1)
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - ui_w + bar_w, y + 18), bar_color, -1)
        
        # Текст
        cv2.putText(frame, f"{icon} {name[:7]}", (w - ui_w + 5, y + 14), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"{pos}°", (w - 55, y + 14), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Подсказки
    hints = [
        "Q - Выход",
        "O - Открыть", 
        "G - Захват",
        "W - Махать",
        "C - Подключить"
    ]
    
    for i, hint in enumerate(hints):
        cv2.putText(frame, hint, (10, h - 15 - i * 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    return frame


def main():
    """Основной цикл."""
    print("=" * 50)
    print("🖐️ Роборука - 5 пальцев (кисть)")
    print("=" * 50)
    print()
    print("Подключение сервоприводов:")
    print("  D3  → Большой палец 👍")
    print("  D5  → Указательный ☝️")
    print("  D6  → Средний 🖕")
    print("  D9  → Безымянный 💍")
    print("  D10 → Мизинец 🤙")
    print()
    print("⚠ Питание: БП 5V 3A для серво!")
    print()
    
    # Контроллер
    controller = RobotHandController()
    
    # Инициализация MediaPipe Hands
    print("Загрузка модели MediaPipe...")
    
    base_options = vision.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    try:
        detector = vision.HandLandmarker.create_from_options(options)
        print("✓ Модель загружена")
    except Exception as e:
        print(f"✗ Ошибка загрузки модели: {e}")
        print("  Скачайте: hand_landmarker.task")
        return
    
    # Камера
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("✗ Не удалось открыть камеру")
        return
    
    last_positions = None
    frame_count = 0
    last_time = time.time()
    fps = 0
    
    print("\n📹 Камера запущена")
    print("Покажите руку в камеру")
    print("Нажмите 'c' для подключения к Arduino")
    print("Нажмите 'q' для выхода")
    print()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Обработка MediaPipe
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        detection_result = detector.detect(mp_image)
        
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                # Отрисовка
                solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    solutions.hands.HAND_CONNECTIONS,
                    solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=3),
                    solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                # Расчёт углов
                angles = calculate_finger_angles(hand_landmarks)
                
                # Отправка (каждые 3 кадра)
                frame_count += 1
                if frame_count % 3 == 0 and angles != last_positions:
                    controller.set_positions(angles)
                    last_positions = angles.copy()
        else:
            frame_count += 1
        
        # FPS
        if frame_count % 30 == 0:
            fps = 30 / max(0.001, time.time() - last_time)
            last_time = time.time()
        
        # UI
        frame = draw_ui(
            frame, 
            controller.positions, 
            controller.names, 
            controller.icons, 
            fps, 
            controller.connected
        )
        
        cv2.imshow("Robot Hand - 5 Fingers", frame)
        
        # Клавиши
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('o'):
            controller.open_hand()
            print("→ Открыть")
        elif key == ord('g'):
            controller.grip()
            print("→ Захват")
        elif key == ord('w'):
            controller.wave()
            print("→ Махать")
        elif key == ord('c'):
            if controller.connect():
                print("✓ Подключено")
            else:
                print("✗ Не подключено")
        elif key == ord('s'):
            status = controller.get_status()
            print(f"→ Статус: {status}")
    
    # Очистка
    cap.release()
    cv2.destroyAllWindows()
    controller.disconnect()
    
    print("\n✓ Завершено")


if __name__ == "__main__":
    main()
