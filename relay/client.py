# client.py — запускать на ноутбуке с Arduino
# Деплой: railway.app → New Project → GitHub → robot-arm-relay

import serial
import asyncio
import websockets
import json
import time
import threading

# ===== НАСТРОЙКИ =====
RELAY_URL = "wss://robot-arm-relay-production.up.railway.app"
ARDUINO_PORT = "/dev/ttyUSB0"   # Windows: COM3 | Linux: /dev/ttyUSB0 или /dev/ttyACM0
BAUD_RATE = 9600
# =====================


class Arduino:
    def __init__(self):
        self.ser = None
        self._lock = threading.Lock()

    def connect(self):
        """Подключение к Arduino."""
        for p in [ARDUINO_PORT, "/dev/ttyUSB0", "/dev/ttyACM0", "COM4", "COM5"]:
            try:
                self.ser = serial.Serial(p, BAUD_RATE, timeout=1)
                time.sleep(2)
                print(f"✅ Arduino: {p}")
                return True
            except Exception as e:
                pass
        print("⚠️  Симуляция (Arduino не найдено)")
        return False

    def send(self, cmd):
        """Отправка команды на Arduino."""
        with self._lock:
            if self.ser and self.ser.is_open:
                self.ser.write(f"{cmd}\n".encode())
                self.ser.flush()
                try:
                    return self.ser.readline().decode().strip()
                except:
                    return "OK"
            print(f"[SIM] {cmd}")
            return "OK"

    def set_pos(self, pos):
        """Установка позиций пальцев."""
        angles = [max(0, min(180, int(p))) for p in pos[:5]]
        return self.send(f"SET:{','.join(map(str, angles))}")

    def open_hand(self):
        return self.send("OPEN")

    def grip(self):
        return self.set_pos([45, 20, 20, 20, 20])

    def home(self):
        return self.send("HOME")


async def run():
    """Основной цикл."""
    print("="*50)
    print("🖐️ Роборука - Relay Клиент")
    print("="*50)
    print(f"\nRelay: {RELAY_URL}")
    print(f"Arduino: {ARDUINO_PORT}\n")
    
    arduino = Arduino()
    arduino.connect()
    
    print(f"🔌 Подключаемся к Relay...")
    
    while True:
        try:
            async with websockets.connect(RELAY_URL) as ws:
                # Регистрация как Arduino клиент
                await ws.send(json.dumps({"type": "register", "role": "arduino"}))
                print("✅ Онлайн! Жду команды с сайта...")
                print("   (Открой web_control.html в браузере)\n")
                
                # Обработка команд
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        data_type = data.get("type")
                        
                        if data_type == "set":
                            positions = data.get("positions", [90]*5)
                            result = arduino.set_pos(positions)
                            print(f"→ SET {positions} → {result}")
                        
                        elif data_type == "command":
                            cmd = data.get("command", "")
                            if cmd == "OPEN" or cmd == "HOME":
                                result = arduino.open_hand()
                            elif cmd == "GRIP":
                                result = arduino.grip()
                            else:
                                result = arduino.send(cmd)
                            print(f"→ {cmd} → {result}")
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("❌ Соединение разорвано")
        except Exception as e:
            print(f"❌ {e}")
        
        print("🔄 Переподключение через 3 сек...")
        await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\n👋 Выход...")
