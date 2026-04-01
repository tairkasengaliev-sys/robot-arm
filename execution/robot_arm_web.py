"""
Роборука - 5 пальцев
Веб-сервер для управления через браузер + Arduino через USB
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time
import asyncio
from aiohttp import web
import json

# Настройки
ARDUINO_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600
WEB_PORT = 8080


class RobotHandController:
    def __init__(self, port=ARDUINO_PORT, baud=BAUD_RATE):
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
                self.port = p
                print(f"✓ {p}")
                return True
            except: pass
        print("⚠ SIM режим")
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
    if len(lm) < 21: return [90]*5
    def dist(a,b): return np.sqrt((a.x-b.x)**2+(a.y-b.y)**2)
    base = 40
    def f_open(tip,pip): return min(dist(tip,pip)/0.12, 1.0)
    return [
        int(np.clip(45+min(dist(lm[4],lm[0])/0.15,1.0)*90,0,180)),
        int(np.clip(base+f_open(lm[8],lm[6])*(180-base),0,180)),
        int(np.clip(base+f_open(lm[12],lm[10])*(180-base),0,180)),
        int(np.clip(base+f_open(lm[16],lm[14])*(180-base),0,180)),
        int(np.clip(base+f_open(lm[20],lm[18])*(180-base),0,180))
    ]


# Глобальный контроллер
ctrl = None
last_angles = None


async def handle_index(request):
    return web.FileResponse('web_control.html')


async def handle_connect(request):
    if ctrl.connect():
        return web.json_response({"status": "connected", "port": ctrl.port})
    return web.json_response({"status": "failed"}, status=400)


async def handle_disconnect(request):
    ctrl.disconnect()
    return web.json_response({"status": "disconnected"})


async def handle_status(request):
    return web.json_response({
        "connected": ctrl.connected,
        "positions": ctrl.positions
    })


async def handle_set(request):
    data = await request.json()
    positions = data.get('positions', [90]*5)
    result = ctrl.set_pos(positions)
    return web.json_response({"status": "ok", "result": result})


async def handle_command(request):
    data = await request.json()
    cmd = data.get('command', '')
    
    if cmd == 'OPEN':
        result = ctrl.open_hand()
    elif cmd == 'GRIP':
        result = ctrl.grip()
    elif cmd == 'HOME':
        result = ctrl.send('HOME')
    else:
        result = 'Unknown command'
    
    return web.json_response({"status": "ok", "result": result})


async def handle_camera(request):
    """Потоковое видео с камеры"""
    response = web.StreamResponse()
    response.content_type = 'multipart/x-mixed-replace; boundary=frame'
    await response.prepare(request)
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    hands = mp.solutions.hands.Hands(
        static_image_mode=False, max_num_hands=1,
        min_detection_confidence=0.7, min_tracking_confidence=0.5
    )
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            
            global last_angles
            if result.multi_hand_landmarks:
                for lm_list in result.multi_hand_landmarks:
                    last_angles = calc_angles(lm_list.landmark)
                    ctrl.set_pos(last_angles)
            
            # Кодируем JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            await response.write(
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            await asyncio.sleep(0.03)  # ~30 FPS
    except Exception as e:
        print(f"Camera error: {e}")
    finally:
        cap.release()
    
    return response


async def handle_angles(request):
    """Получить текущие углы"""
    return web.json_response({"angles": last_angles or [90]*5})


def create_app():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_post('/connect', handle_connect)
    app.router.add_post('/disconnect', handle_disconnect)
    app.router.add_get('/status', handle_status)
    app.router.add_post('/set', handle_set)
    app.router.add_post('/command', handle_command)
    app.router.add_get('/video', handle_camera)
    app.router.add_get('/angles', handle_angles)
    return app


if __name__ == "__main__":
    print("="*50)
    print("🖐️ Роборука - Веб-сервер")
    print("="*50)
    print("\nПодключение серво: D3👍 D5☝️ D6🖕 D9💍 D10🤙")
    print("⚠ БП 5V 3A!\n")
    
    ctrl = RobotHandController()
    
    # Авто-подключение
    print("🔌 Подключение к Arduino...")
    ctrl.connect()
    
    print(f"\n🌐 Веб-интерфейс: http://localhost:{WEB_PORT}")
    print("📹 Видео: http://localhost:{WEB_PORT}/video")
    print("\nНажми Ctrl+C для выхода\n")
    
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=WEB_PORT, print=None)
