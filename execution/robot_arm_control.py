"""
Управление роборукой через камеру
Использует MediaPipe для трекинга руки и отправляет команды на Arduino
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
PROJECT_ROOT = Path(__file__).parent
ARDUINO_PORT = "/dev/ttyUSB0"  # или COM3 для Windows
BAUD_RATE = 9600

# Инициализация MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Границы углов сервоприводов
MIN_ANGLE = 0
MAX_ANGLE = 180


class RobotArmController:
    def __init__(self, port=ARDUINO_PORT, baud=BAUD_RATE):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        
        # Текущие позиции
        self.positions = {
            'thumb': 90,
            'index': 90,
            'middle': 90,
            'ring': 90,
            'pinky': 90,
            'wrist': 90,
            'elbow': 90,
            'shoulder': 90
        }
        
    def connect(self):
        """Подключение к Arduino."""
        try:
            self.arduino = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Ждём инициализацию
            self.connected = True
            print(f"✓ Подключено к {self.port}")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            print("  Запуск в режиме симуляции...")
            return False
    
    def disconnect(self):
        """Отключение от Arduino."""
        if self.arduino and self.connected:
            self.arduino.close()
            self.connected = False
    
    def send_command(self, command):
        """Отправка команды на Arduino."""
        if self.connected and self.arduino:
            self.arduino.write(f"{command}\n".encode())
            response = self.arduino.readline().decode().strip()
            return response
        else:
            print(f"[SIM] Команда: {command}")
            return "SIM_OK"
    
    def set_positions(self, thumb, index, middle, ring, pinky, wrist, elbow, shoulder):
        """Установка позиций всех сервоприводов."""
        # Ограничение углов
        angles = [
            max(MIN_ANGLE, min(MAX_ANGLE, thumb)),
            max(MIN_ANGLE, min(MAX_ANGLE, index)),
            max(MIN_ANGLE, min(MAX_ANGLE, middle)),
            max(MIN_ANGLE, min(MAX_ANGLE, ring)),
            max(MIN_ANGLE, min(MAX_ANGLE, pinky)),
            max(MIN_ANGLE, min(MAX_ANGLE, wrist)),
            max(MIN_ANGLE, min(MAX_ANGLE, elbow)),
            max(MIN_ANGLE, min(MAX_ANGLE, shoulder))
        ]
        
        command = f"SET:{','.join(map(str, angles))}"
        response = self.send_command(command)
        
        if response in ["OK", "SIM_OK"]:
            self.positions = {
                'thumb': angles[0],
                'index': angles[1],
                'middle': angles[2],
                'ring': angles[3],
                'pinky': angles[4],
                'wrist': angles[5],
                'elbow': angles[6],
                'shoulder': angles[7]
            }
        
        return response
    
    def home(self):
        """Домашняя позиция."""
        return self.send_command("HOME")
    
    def grip(self):
        """Захват."""
        return self.send_command("GRIP")
    
    def open_hand(self):
        """Открыть ладонь."""
        return self.send_command("OPEN")
    
    def get_status(self):
        """Получить текущий статус."""
        return self.send_command("STATUS")


def calculate_angles_from_hand(landmarks, frame_height):
    """
    Расчёт углов сервоприводов на основе позиции руки.
    
    landmarks: координаты关键点 руки от MediaPipe
    """
    # Извлечение关键点
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]
    
    wrist = landmarks[0]
    index_pip = landmarks[6]
    middle_pip = landmarks[10]
    ring_pip = landmarks[14]
    pinky_pip = landmarks[18]
    
    # Пальцы - расстояние от кончика до основания
    def finger_openness(tip, pip):
        return np.sqrt((tip.x - pip.x)**2 + (tip.y - pip.y)**2)
    
    index_open = finger_openness(index_tip, index_pip)
    middle_open = finger_openness(middle_tip, middle_pip)
    ring_open = finger_openness(ring_tip, ring_pip)
    pinky_open = finger_openness(pinky_tip, pinky_pip)
    
    # Преобразование в углы (0 = закрыт, 180 = открыт)
    base_angle = 30
    max_open = 0.15
    
    index_angle = base_angle + min(index_open / max_open, 1) * (180 - base_angle)
    middle_angle = base_angle + min(middle_open / max_open, 1) * (180 - base_angle)
    ring_angle = base_angle + min(ring_open / max_open, 1) * (180 - base_angle)
    pinky_angle = base_angle + min(pinky_open / max_open, 1) * (180 - base_angle)
    
    # Большой палец - угол от запястья
    thumb_open = np.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
    thumb_angle = 45 + min(thumb_open / 0.2, 1) * 90
    
    # Запястье - угол наклона
    wrist_angle = 90 + (wrist.y - 0.5) * 60
    
    # Локоть - высота руки в кадре
    elbow_angle = 90 + (wrist.y - 0.5) * 40
    
    # Плечо - позиция X руки
    shoulder_angle = 90 + (wrist.x - 0.5) * 60
    
    return {
        'thumb': int(thumb_angle),
        'index': int(index_angle),
        'middle': int(middle_angle),
        'ring': int(ring_angle),
        'pinky': int(pinky_angle),
        'wrist': int(wrist_angle),
        'elbow': int(elbow_angle),
        'shoulder': int(shoulder_angle)
    }


def main():
    """Основной цикл."""
    print("=" * 50)
    print("🤖 Управление роборукой через камеру")
    print("=" * 50)
    
    # Подключение к Arduino
    controller = RobotArmController()
    controller.connect()
    
    # Открытие камеры
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    last_positions = None
    frame_count = 0
    
    print("\n📹 Камера запущена. Покажите руку в камеру.")
    print("Нажмите 'q' для выхода, 'h' - домашняя позиция, 'g' - захват")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # Отрисовка
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Расчёт углов
                angles = calculate_angles_from_hand(
                    hand_landmarks.landmark, 
                    frame.shape[0]
                )
                
                # Отправка на Arduino (каждые 5 кадров для плавности)
                frame_count += 1
                if frame_count % 5 == 0:
                    if angles != last_positions:
                        controller.set_positions(**angles)
                        last_positions = angles.copy()
                
                # Отображение углов на экране
                y_offset = 30
                for joint, angle in angles.items():
                    cv2.putText(frame, f"{joint}: {angle}°", (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 25
        else:
            cv2.putText(frame, "Рука не обнаружена", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Статус подключения
        status = "CONNECTED" if controller.connected else "SIMULATION"
        color = (0, 255, 0) if controller.connected else (0, 128, 255)
        cv2.putText(frame, status, (frame.shape[1] - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.imshow("Robot Arm Control", frame)
        
        # Обработка клавиш
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('h'):
            controller.home()
            print("→ Домашняя позиция")
        elif key == ord('g'):
            controller.grip()
            print("→ Захват")
        elif key == ord('o'):
            controller.open_hand()
            print("→ Открыть ладонь")
    
    # Очистка
    cap.release()
    cv2.destroyAllWindows()
    controller.disconnect()
    print("\n✓ Завершено")


if __name__ == "__main__":
    main()
