"""
Роборука - Управление через камеру на Android (Termux)
Запуск: python robot_arm_mobile.py
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time
import json
from pathlib import Path

# Пути
DATA_DIR = Path(__file__).parent.parent / ".tmp" / "arm_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Настройки
ARDUINO_PORT = "/dev/ttyUSB0"  # Для Android: /dev/ttyACM0 или Bluetooth
BAUD_RATE = 9600

# MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class RobotArmController:
    def __init__(self, port=None, baud=BAUD_RATE):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        
        self.positions = [90] * 8
        self.names = ['thumb', 'index', 'middle', 'ring', 'pinky', 'wrist', 'elbow', 'shoulder']
        
    def connect(self, port=None):
        """Подключение к Arduino."""
        ports_to_try = [
            port,
            "/dev/ttyUSB0",
            "/dev/ttyACM0", 
            "/dev/ttyS0",
            "/dev/rfcomm0",  # Bluetooth
            "COM3",
            "COM4"
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
                continue
        
        print("✗ Не удалось подключиться. Режим симуляции.")
        return False
    
    def disconnect(self):
        if self.arduino:
            self.arduino.close()
        self.connected = False
    
    def send_command(self, cmd):
        """Отправка команды."""
        if self.connected and self.arduino:
            self.arduino.write(f"{cmd}\n".encode())
            return self.arduino.readline().decode().strip()
        else:
            print(f"[SIM] {cmd}")
            return "SIM_OK"
    
    def set_positions(self, positions):
        """Установка позиций сервоприводов."""
        angles = [max(0, min(180, p)) for p in positions[:8]]
        cmd = f"SET:{','.join(map(str, angles))}"
        result = self.send_command(cmd)
        
        if result in ["OK", "SIM_OK"]:
            self.positions = angles + [90] * (8 - len(angles))
        
        return result
    
    def home(self):
        return self.send_command("HOME")
    
    def grip(self):
        return self.send_command("GRIP")
    
    def open_hand(self):
        return self.send_command("OPEN")


def calculate_angles(landmarks, frame_h):
    """Расчёт углов из позиции руки."""
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
    
    base = 30
    max_open = 0.15
    
    # Пальцы
    index_angle = base + min(dist(index_tip, index_pip) / max_open, 1) * (180 - base)
    middle_angle = base + min(dist(middle_tip, middle_pip) / max_open, 1) * (180 - base)
    ring_angle = base + min(dist(ring_tip, ring_pip) / max_open, 1) * (180 - base)
    pinky_angle = base + min(dist(pinky_tip, pinkyPip) / max_open, 1) * (180 - base)
    
    # Большой палец
    thumb_open = dist(thumb_tip, wrist)
    thumb_angle = 45 + min(thumb_open / 0.2, 1) * 90
    
    # Запястье, локоть, плечо
    wrist_angle = 90 + (wrist.y - 0.5) * 60
    elbow_angle = 90 + (wrist.y - 0.5) * 40
    shoulder_angle = 90 + (wrist.x - 0.5) * 60
    
    return [
        int(np.clip(thumb_angle, 0, 180)),
        int(np.clip(index_angle, 0, 180)),
        int(np.clip(middle_angle, 0, 180)),
        int(np.clip(ring_angle, 0, 180)),
        int(np.clip(pinky_angle, 0, 180)),
        int(np.clip(wrist_angle, 0, 180)),
        int(np.clip(elbow_angle, 0, 180)),
        int(np.clip(shoulder_angle, 0, 180))
    ]


def draw_ui(frame, positions, names, fps=0):
    """Отрисовка интерфейса."""
    h, w = frame.shape[:2]
    
    # Фон для UI
    ui_w = 280
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + 30 + len(names) * 35), 
                  (0, 0, 0), -1)
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + 30 + len(names) * 35), 
                  (0, 255, 0), 2)
    
    # Заголовок
    cv2.putText(frame, "🦾 РОБОРУКА", (w - ui_w, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 100, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Позиции
    icons = ['👍', '☝️', '🖕', '💍', '🤙', '💫', '📐', '📍']
    
    for i, (pos, name) in enumerate(zip(positions[:8], names)):
        y = 55 + i * 35
        color = (0, 255, 0) if pos > 100 else (0, 255, 255)
        
        # Прогресс бар
        bar_w = int((pos / 180) * (ui_w - 60))
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - 20, y + 18), (30, 30, 30), -1)
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - ui_w + bar_w, y + 18), color, -1)
        
        # Текст
        cv2.putText(frame, f"{icons[i]} {name[:8]}", (w - ui_w + 5, y + 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"{pos}°", (w - 55, y + 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Подсказки
    hints = [
        "Q - Выход",
        "H - Домой", 
        "G - Захват",
        "O - Открыть",
        "C - Подключить"
    ]
    
    for i, hint in enumerate(hints):
        cv2.putText(frame, hint, (10, h - 15 - i * 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    return frame


def main():
    """Основной цикл."""
    print("=" * 50)
    print("🦾 Роборука - Android (Termux)")
    print("=" * 50)
    
    # Контроллер
    controller = RobotArmController()
    
    # Камера
    # Для Android: использовать ID 0 или 1 (фронтальная/тыловая)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("✗ Не удалось открыть камеру")
        print("Попробуйте изменить ID камеры: cv2.VideoCapture(1)")
        return
    
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    names = controller.names
    last_positions = None
    frame_count = 0
    last_time = time.time()
    fps = 0
    
    print("\n📹 Камера запущена")
    print("Покажите руку в камеру")
    print("Нажмите 'c' для подключения к Arduino")
    print("Нажмите 'q' для выхода")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Обработка
        results = hands.process(frame_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Отрисовка скелета руки
                mp_drawing.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=3),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                # Расчёт углов
                angles = calculate_angles(hand_landmarks.landmark, frame.shape[0])
                
                # Отправка (каждые 3 кадра для плавности)
                frame_count += 1
                if frame_count % 3 == 0 and angles != last_positions:
                    controller.set_positions(angles)
                    last_positions = angles.copy()
        
        # FPS
        frame_count += 1
        if frame_count % 30 == 0:
            fps = 30 / (time.time() - last_time)
            last_time = time.time()
        
        # UI
        frame = draw_ui(frame, controller.positions, names, fps)
        
        # Статус подключения
        status = "CONNECTED" if controller.connected else "OFFLINE"
        color = (0, 255, 0) if controller.connected else (0, 0, 255)
        cv2.putText(frame, status, (frame.shape[1] - 120, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.imshow("Robot Arm", frame)
        
        # Клавиши
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('h'):
            controller.home()
            print("→ Домой")
        elif key == ord('g'):
            controller.grip()
            print("→ Захват")
        elif key == ord('o'):
            controller.open_hand()
            print("→ Открыть")
        elif key == ord('c'):
            controller.connect()
    
    # Очистка
    cap.release()
    cv2.destroyAllWindows()
    controller.disconnect()
    
    print("\n✓ Завершено")


if __name__ == "__main__":
    main()
