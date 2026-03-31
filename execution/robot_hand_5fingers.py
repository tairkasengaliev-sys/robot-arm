"""
Роборука - 5 пальцев
Управление через камеру + Arduino Uno
Работает с mediapipe 0.10.30+
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time


class RobotHandController:
    def __init__(self, port="/dev/ttyUSB0", baud=9600):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        self.positions = [90] * 5
        
    def connect(self):
        for p in [self.port, "/dev/ttyUSB0", "/dev/ttyACM0", "COM3"]:
            if not p: continue
            try:
                self.arduino = serial.Serial(p, self.baud, timeout=1)
                time.sleep(2)
                self.connected = True
                print(f"✓ {p}")
                return True
            except: pass
        print("⚠ SIM")
        return False
    
    def disconnect(self):
        if self.arduino: self.arduino.close()
        self.connected = False
    
    def send(self, cmd):
        if self.connected and self.arduino:
            self.arduino.write(f"{cmd}\n".encode())
            return self.arduino.readline().decode().strip()
        print(f"[SIM] {cmd}")
        return "OK"
    
    def set_pos(self, pos):
        return self.send(f"SET:{','.join(map(str, [max(0,min(180,int(p))) for p in pos[:5]]))}")
    
    def open_hand(self): return self.send("OPEN")
    def grip(self): return self.set_pos([45,20,20,20,20])


def calc_angles(lm):
    """Расчёт углов 5 пальцев из landmarks"""
    if len(lm) < 21: return [90]*5
    
    def dist(a, b):
        return np.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
    base = 40
    
    def finger_openness(tip, pip):
        return min(dist(tip, pip) / 0.12, 1.0)
    
    # Большой палец (от запястья)
    thumb_angle = 45 + min(dist(lm[4], lm[0]) / 0.15, 1.0) * 90
    
    # Остальные пальцы
    angles = [
        int(np.clip(thumb_angle, 0, 180)),
        int(np.clip(base + finger_openness(lm[8], lm[6]) * (180 - base), 0, 180)),
        int(np.clip(base + finger_openness(lm[12], lm[10]) * (180 - base), 0, 180)),
        int(np.clip(base + finger_openness(lm[16], lm[14]) * (180 - base), 0, 180)),
        int(np.clip(base + finger_openness(lm[20], lm[18]) * (180 - base), 0, 180))
    ]
    return angles


def main():
    print("="*50)
    print("🖐️ Роборука - 5 пальцев")
    print("="*50)
    print("\nПодключение серво:")
    print("  D3👍 D5☝️ D6🖕 D9💍 D10🤙")
    print("\n⚠ Питание: БП 5V 3A!")
    print()
    
    ctrl = RobotHandController()
    
    # Инициализация MediaPipe Hands
    use_new_api = False
    detector = None
    
    try:
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from mediapipe.tasks.python.core.base_options import BaseOptions
        
        model_path = 'hand_landmarker.task'
        base_options = BaseOptions(model_asset_path=model_path)
        options = HandLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_hands=1
        )
        detector = HandLandmarker.create_from_options(options)
        use_new_api = True
        print("✓ MediaPipe новый API")
    except Exception as e:
        print(f"⚠ Новый API: {e}")
    
    if not use_new_api:
        try:
            import mediapipe as mp
            detector = mp.solutions.hands.Hands(
                static_image_mode=False, max_num_hands=1,
                min_detection_confidence=0.7, min_tracking_confidence=0.5
            )
            print("✓ MediaPipe классический API")
        except Exception as e:
            print(f"✗ Ошибка MediaPipe: {e}")
            return
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("✗ Нет камеры")
        return
    
    last_pos = None
    fc = 0
    last_t = time.time()
    
    print("✓ Готово!")
    print("Клавиши: C-подключить, O-открыть, G-захват, Q-выход\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Обработка
        if use_new_api:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect(mp_image)
            
            if result.hand_landmarks:
                for lm_list in result.hand_landmarks:
                    # Рисуем
                    for i, lm in enumerate(lm_list):
                        x, y = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
                    
                    angles = calc_angles(lm_list)
                    fc += 1
                    if fc % 3 == 0 and angles != last_pos:
                        ctrl.set_pos(angles)
                        last_pos = angles
            else:
                fc += 1
        else:
            # Fallback без детекции - просто симуляция
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = detector.process(rgb)
            
            if result.multi_hand_landmarks:
                for lm_list in result.multi_hand_landmarks:
                    lm = lm_list.landmark
                    angles = calc_angles(lm)
                    fc += 1
                    if fc % 3 == 0 and angles != last_pos:
                        ctrl.set_pos(angles)
                        last_pos = angles
            else:
                fc += 1
        
        # FPS
        if fc % 30 == 0:
            fps = 30 / max(0.001, time.time() - last_t)
            last_t = time.time()
            cv2.putText(frame, f"FPS:{fps:.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # UI панель
        cv2.rectangle(frame, (w-180, 10), (w-10, 180), (0, 0, 0), -1)
        status = "ON" if ctrl.connected else "OFF"
        cv2.putText(frame, f"Robot Hand [{status}]", (w-170, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        icons = ['👍', '☝️', '🖕', '💍', '🤙']
        for i, (pos, icon) in enumerate(zip(ctrl.positions, icons)):
            cv2.putText(frame, f"{icon} {pos}°", (w-170, 60 + i*28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.putText(frame, "Q-Exit O-Open G-Grip C-Connect", (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Robot Hand", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('o'):
            ctrl.open_hand()
            print("→ Open")
        elif key == ord('g'):
            ctrl.grip()
            print("→ Grip")
        elif key == ord('c'):
            ctrl.connect()
        elif key == ord('s'):
            print(f"→ {ctrl.send('STATUS')}")
    
    cap.release()
    cv2.destroyAllWindows()
    ctrl.disconnect()
    print("\n✓ Завершено")


if __name__ == "__main__":
    main()
