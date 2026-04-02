#!/usr/bin/env python3
"""
Роборука - Локальное управление (без Relay)
Прямое подключение к Arduino через USB
"""

import serial
import time

ARDUINO_PORT = "/dev/ttyUSB1"
BAUD_RATE = 9600

def connect():
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"✓ Подключено к {ARDUINO_PORT}")
        return arduino
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return None

def send(arduino, cmd):
    arduino.write(f"{cmd}\n".encode())
    arduino.flush()
    time.sleep(0.5)
    
    # Чтение ответа
    while arduino.in_waiting > 0:
        response = arduino.readline().decode().strip()
        if response:
            print(f"← {response}")

def set_pos(arduino, positions):
    cmd = f"SET:{','.join(map(str, positions))}"
    print(f"→ {cmd}")
    send(arduino, cmd)

def main():
    print("="*50)
    print("🖐️ Роборука - Локальное управление")
    print("="*50)
    
    arduino = connect()
    if not arduino:
        return
    
    print("\nКоманды:")
    print("  o - Открыть 🖐")
    print("  g - Захват ✊")
    print("  h - Домой 🏠")
    print("  t - Тест")
    print("  s - Статус")
    print("  0-4 - Двигать палец (0=большой, 4=мизинец)")
    print("  q - Выход")
    print()
    
    positions = [90, 90, 90, 90, 90]
    
    while True:
        cmd = input("> ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'o':
            print("→ OPEN")
            send(arduino, "OPEN")
            positions = [90, 90, 90, 90, 90]
        elif cmd == 'g':
            print("→ GRIP")
            send(arduino, "GRIP")
            positions = [45, 20, 20, 20, 20]
        elif cmd == 'h':
            print("→ HOME")
            send(arduino, "HOME")
            positions = [90, 90, 90, 90, 90]
        elif cmd == 't':
            print("→ TEST")
            send(arduino, "TEST")
        elif cmd == 's':
            print("→ STATUS")
            send(arduino, "STATUS")
        elif cmd in '01234':
            finger = int(cmd)
            print(f"Палец {finger} (90/0/180):")
            angle = input("> ").strip()
            if angle in ['90', '0', '180']:
                positions[finger] = int(angle)
                set_pos(arduino, positions)
        elif cmd == 'set':
            print("Введи 5 углов через запятую (90,45,30,30,30):")
            angles = input("> ").strip()
            set_pos(arduino, [int(x) for x in angles.split(',')])
        else:
            print("Неизвестная команда")
    
    arduino.close()
    print("\n✓ Завершено")

if __name__ == "__main__":
    main()
