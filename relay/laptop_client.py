"""
Роборука - Клиент для Relay сервера
Подключается к Arduino через USB и к Relay через WebSocket
"""

import serial
import time
import websocket
import json
import threading
import sys

# Настройки
ARDUINO_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600
RELAY_URL = "wss://твой-relay.railway.app"  # ЗАМЕНИТЬ ПОСЛЕ ДЕПЛОЯ!


class ArduinoClient:
    def __init__(self, port=ARDUINO_PORT, baud=BAUD_RATE):
        self.arduino = None
        self.port = port
        self.baud = baud
        self.connected = False
        self.ws = None
        self.ws_ready = False
        
    def connect_arduino(self):
        """Подключение к Arduino через USB."""
        for p in [self.port, "/dev/ttyUSB0", "/dev/ttyACM0", "COM3"]:
            if not p:
                continue
            try:
                self.arduino = serial.Serial(p, self.baud, timeout=1)
                time.sleep(2)
                self.connected = True
                self.port = p
                print(f"✓ Arduino: {p}")
                return True
            except Exception as e:
                print(f"✗ {p}: {e}")
        print("⚠ Arduino не найдена")
        return False
    
    def connect_relay(self):
        """Подключение к Relay серверу."""
        def on_open(ws):
            print("✓ Relay: подключено")
            ws.send(json.dumps({"type": "register", "role": "arduino"}))
            self.ws_ready = True
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                cmd_type = data.get("type")
                
                if cmd_type == "command":
                    cmd = data.get("command")
                    print(f"← Команда: {cmd}")
                    self.send_to_arduino(cmd)
                
                elif cmd_type == "set":
                    positions = data.get("positions", [])
                    cmd = f"SET:{','.join(map(str, positions[:5]))}"
                    print(f"← Позиции: {positions}")
                    self.send_to_arduino(cmd)
                    
            except Exception as e:
                print(f"⚠ Ошибка парсинга: {e}")
        
        def on_close(ws, code, reason):
            print("✗ Relay: отключено")
            self.ws_ready = False
        
        def on_error(ws, error):
            print(f"⚠ Relay ошибка: {error}")
        
        self.ws = websocket.WebSocketApp(
            RELAY_URL,
            on_open=on_open,
            on_message=on_message,
            on_close=on_close,
            on_error=on_error
        )
        
        # Запуск в отдельном потоке
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
        time.sleep(2)  # Ждём подключения
    
    def send_to_arduino(self, cmd):
        """Отправка команды на Arduino."""
        if self.connected and self.arduino:
            try:
                self.arduino.write(f"{cmd}\n".encode())
                self.arduino.flush()
                print(f"→ Arduino: {cmd}")
            except Exception as e:
                print(f"✗ Ошибка отправки: {e}")
                self.connected = False
    
    def run(self):
        """Основной цикл."""
        print("="*50)
        print("🖐️ Роборука - Relay Клиент")
        print("="*50)
        print(f"\nRelay: {RELAY_URL}")
        print(f"Arduino: {ARDUINO_PORT}\n")
        
        # Подключения
        if not self.connect_arduino():
            print("⚠ Запуск без Arduino (режим отладки)")
        
        self.connect_relay()
        
        print("\n✓ Готово! Ожидание команд...\n")
        
        # Основной цикл
        try:
            while True:
                # Чтение от Arduino (если нужно)
                if self.connected and self.arduino and self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if response:
                        print(f"← Arduino: {response}")
                        
                        # Отправить статус веб-клиентам
                        if self.ws and self.ws_ready:
                            self.ws.send(json.dumps({
                                "type": "arduino_status",
                                "connected": True,
                                "response": response
                            }))
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nВыход...")
        finally:
            if self.ws:
                self.ws.close()
            if self.arduino:
                self.arduino.close()


if __name__ == "__main__":
    client = ArduinoClient()
    client.run()
