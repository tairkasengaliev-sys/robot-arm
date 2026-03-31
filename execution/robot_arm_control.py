"""
Роборука - Управление через камеру
Arduino Uno R3 + Sensor Shield V5.0 + HC-05
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Настройки
PROJECT_ROOT = Path(__file__).parent.parent
ARDUINO_PORT = "/dev/ttyUSB0"  # Linux: /dev/ttyUSB0, Windows: COM3
BAUD_RATE = 9600

# MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class RobotArmController:
    """Контроллер роборуки на Arduino Uno + Shield V5.0"""
    
    def __init__(self, port=ARDUINO_PORT, baud=BAUD_RATE):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        
        # Позиции сервоприводов (8 каналов)
        # Shield V5.0: D3, D5, D6, D9, D10, D11, A0, A1
        self.positions = [90] * 8
        self.names = [
            'Thumb',      # D3  - Большой
            'Index',      # D5  - Указательный
            'Middle',     # D6  - Средний
            'Ring',       # D9  - Безымянный
            'Pinky',      # D10 - Мизинец
            'Wrist',      # D11 - Запястье
            'Elbow',      # A0  - Локоть
            'Shoulder'    # A1  - Плечо
        ]
        
    def connect(self, port=None):
        """Подключение к Arduino через USB или Bluetooth."""
        ports_to_try = [
            port,
            "/dev/ttyUSB0",      # Linux USB
            "/dev/ttyUSB1",
            "/dev/ttyACM0",      # Arduino Uno
            "/dev/rfcomm0",      # Bluetooth Linux
            "COM3",              # Windows
            "COM4",
            "COM5"
        ]
        
        for p in ports_to_try:
            if p is None:
                continue
            try:
                self.arduino = serial.Serial(p, self.baud, timeout=1)
                time.sleep(2)  # Ждём инициализацию Arduino
                self.connected = True
                self.port = p
                print(f"✓ Подключено к {p}")
                return True
            except Exception as e:
                print(f"✗ {p}: {e}")
                continue
        
        print("⚠ Не удалось подключиться. Режим симуляции.")
        return False
    
    def disconnect(self):
        """Отключение от Arduino."""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.connected = False
    
    def send_command(self, cmd):
        """Отправка команды на Arduino."""
        if self.connected and self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(f"{cmd}\n".encode())
                self.arduino.flush()
                response = self.arduino.readline().decode().strip()
                return response
            except Exception as e:
                print(f"Ошибка отправки: {e}")
                return f"ERR: {e}"
        else:
            print(f"[SIM] {cmd}")
            return "SIM_OK"
    
    def set_positions(self, positions):
        """Установка позиций всех 8 сервоприводов."""
        angles = [max(0, min(180, int(p))) for p in positions[:8]]
        cmd = f"SET:{','.join(map(str, angles))}"
        result = self.send_command(cmd)
        
        if result in ["OK", "SET_OK", "SIM_OK"]:
            self.positions = angles
        
        return result
    
    def set_servo(self, channel, angle):
        """Установка одного сервопривода."""
        if 0 <= channel < 8:
            angle = max(0, min(180, int(angle)))
            self.positions[channel] = angle
            return self.set_positions(self.positions)
        return "ERR: Invalid channel"
    
    def home(self):
        """Домашняя позиция (все в 90°)."""
        return self.send_command("HOME")
    
    def grip(self):
        """Захват (сжать пальцы)."""
        grip_positions = [45, 30, 30, 30, 30, 90, 120, 90]
        return self.set_positions(grip_positions)
    
    def open_hand(self):
        """Открыть ладонь."""
        return self.send_command("OPEN")
    
    def get_status(self):
        """Получить текущие позиции."""
        return self.send_command("STATUS")
    
    def test_servos(self):
        """Тест сервоприводов."""
        return self.send_command("TEST")


def calculate_angles(landmarks, frame_h):
    """
    Расчёт углов сервоприводов из позиции руки.
    
    landmarks: 21 точка руки от MediaPipe
    """
    if len(landmarks) < 21:
        return [90] * 8
    
    # Ключевые точки
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
    
    # Расстояние между точками
    def dist(a, b):
        return np.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
    # Открытость пальцев (0 = сжат, 1 = разжат)
    def finger_openness(tip, pip, max_open=0.15):
        d = dist(tip, pip)
        return min(d / max_open, 1.0)
    
    # Базовый угол для сжатого пальца
    base_angle = 30
    
    # Пальцы
    index_angle = base_angle + finger_openness(index_tip, index_pip) * (180 - base_angle)
    middle_angle = base_angle + finger_openness(middle_tip, middle_pip) * (180 - base_angle)
    ring_angle = base_angle + finger_openness(ring_tip, ring_pip) * (180 - base_angle)
    pinky_angle = base_angle + finger_openness(pinky_tip, pinky_pip) * (180 - base_angle)
    
    # Большой палец (от запястья)
    thumb_open = dist(thumb_tip, wrist)
    thumb_angle = 45 + min(thumb_open / 0.2, 1.0) * 90
    
    # Запястье (наклон руки)
    wrist_angle = 90 + (wrist.y - 0.5) * 60
    
    # Локоть (высота руки)
    elbow_angle = 90 + (wrist.y - 0.5) * 40
    
    # Плечо (позиция X руки)
    shoulder_angle = 90 + (wrist.x - 0.5) * 60
    
    # Ограничение 0-180
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


def draw_ui(frame, positions, names, fps=0, connected=False):
    """Отрисовка интерфейса на кадре."""
    h, w = frame.shape[:2]
    
    # Панель UI
    ui_w = 280
    ui_h = 30 + len(names) * 32 + 50
    
    # Фон
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + ui_h), (0, 0, 0), -1)
    cv2.rectangle(frame, (w - ui_w - 10, 10), (w - 10, 10 + ui_h), (0, 255, 0), 2)
    
    # Заголовок
    cv2.putText(frame, "ROBOT ARM", (w - ui_w, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Статус
    status = "CONNECTED" if connected else "OFFLINE"
    color = (0, 255, 0) if connected else (0, 0, 255)
    cv2.putText(frame, status, (w - 120, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 60, 32), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Позиции сервоприводов
    icons = ['👍', '☝️', '🖕', '💍', '🤙', '💫', '📐', '📍']
    
    for i, (pos, name) in enumerate(zip(positions, names)):
        y = 52 + i * 32
        color = (0, 255, 0) if pos > 100 else (0, 255, 255)
        
        # Прогресс бар
        bar_w = int((pos / 180) * (ui_w - 80))
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - 30, y + 16), (30, 30, 30), -1)
        cv2.rectangle(frame, (w - ui_w, y - 5), (w - ui_w + bar_w, y + 16), color, -1)
        
        # Текст
        cv2.putText(frame, f"{icons[i]} {name[:8]}", (w - ui_w + 5, y + 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(frame, f"{pos}°", (w - 55, y + 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
    
    # Подсказки
    hints = [
        "Q - Выход",
        "H - Домой", 
        "G - Захват",
        "O - Открыть",
        "C - Подключить",
        "T - Тест"
    ]
    
    for i, hint in enumerate(hints):
        cv2.putText(frame, hint, (10, h - 15 - i * 22), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    
    return frame


def main():
    """Основной цикл программы."""
    print("=" * 50)
    print("🦾 Роборука - Arduino Uno + Shield V5.0")
    print("=" * 50)
    print()
    print("Подключение сервоприводов:")
    print("  D3  → Большой палец")
    print("  D5  → Указательный")
    print("  D6  → Средний")
    print("  D9  → Безымянный")
    print("  D10 → Мизинец")
    print("  D11 → Запястье")
    print("  A0  → Локоть")
    print("  A1  → Плечо")
    print()
    
    # Контроллер
    controller = RobotArmController()
    
    # Камера
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("✗ Не удалось открыть камеру")
        print("Попробуйте: cv2.VideoCapture(1) для фронтальной")
        return
    
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
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
        
        # Обработка руки
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
                
                # Отправка на Arduino (каждые 3 кадра)
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
        frame = draw_ui(frame, controller.positions, controller.names, fps, controller.connected)
        
        cv2.imshow("Robot Arm - Uno Shield V5.0", frame)
        
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
            if controller.connect():
                print("✓ Подключено")
            else:
                print("✗ Не подключено")
        elif key == ord('t'):
            controller.test_servos()
            print("→ Тест серво")
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
