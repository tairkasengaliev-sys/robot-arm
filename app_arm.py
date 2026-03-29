"""
Веб-приложение для управления роборукой
Запуск: streamlit run app_arm.py
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time
from pathlib import Path
import streamlit as st
from PIL import Image

# Пути
PROJECT_ROOT = Path(__file__).parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "arm_data"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Настройки Arduino
ARDUINO_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1", "COM3", "COM4", "COM5"]

# Инициализация MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class RobotArmController:
    def __init__(self):
        self.arduino = None
        self.connected = False
        self.port = None
        
        self.positions = {
            'thumb': 90, 'index': 90, 'middle': 90, 'ring': 90,
            'pinky': 90, 'wrist': 90, 'elbow': 90, 'shoulder': 90
        }
        
    def connect(self, port, baud=9600):
        try:
            self.arduino = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            self.connected = True
            self.port = port
            return True
        except:
            return False
    
    def disconnect(self):
        if self.arduino:
            self.arduino.close()
        self.connected = False
    
    def send_command(self, command):
        if self.connected and self.arduino:
            self.arduino.write(f"{command}\n".encode())
            return self.arduino.readline().decode().strip()
        return "SIM_OK"
    
    def set_positions(self, **kwargs):
        angles = [
            max(0, min(180, kwargs.get('thumb', 90))),
            max(0, min(180, kwargs.get('index', 90))),
            max(0, min(180, kwargs.get('middle', 90))),
            max(0, min(180, kwargs.get('ring', 90))),
            max(0, min(180, kwargs.get('pinky', 90))),
            max(0, min(180, kwargs.get('wrist', 90))),
            max(0, min(180, kwargs.get('elbow', 90))),
            max(0, min(180, kwargs.get('shoulder', 90)))
        ]
        
        command = f"SET:{','.join(map(str, angles))}"
        self.send_command(command)
        
        self.positions = {
            'thumb': angles[0], 'index': angles[1], 'middle': angles[2],
            'ring': angles[3], 'pinky': angles[4], 'wrist': angles[5],
            'elbow': angles[6], 'shoulder': angles[7]
        }


def calculate_angles(landmarks):
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
    
    def finger_open(tip, pip):
        return np.sqrt((tip.x - pip.x)**2 + (tip.y - pip.y)**2)
    
    base = 30
    max_open = 0.15
    
    return {
        'thumb': int(45 + min(np.sqrt((thumb_tip.x - wrist.x)**2 + **(thumb_tip.y - wrist.y)2) / 0.2, 1) * 90),
        'index': int(base + min(index_open / max_open, 1) * (180 - base)),
        'middle': int(base + min(middle_open / max_open, 1) * (180 - base)),
        'ring': int(base + min(ring_open / max_open, 1) * (180 - base)),
        'pinky': int(base + min(pinky_open / max_open, 1) * (180 - base)),
        'wrist': int(90 + (wrist.y - 0.5) * 60),
        'elbow': int(90 + (wrist.y - 0.5) * 40),
        'shoulder': int(90 + (wrist.x - 0.5) * 60)
    }


# ============================================
# UI ПРИЛОЖЕНИЯ
# ============================================

st.set_page_config(
    page_title="Роборука",
    page_icon="🦾",
    layout="wide"
)

st.title("🦾 Управление роборукой")
st.markdown("---")

# Инициализация контроллера
if 'controller' not in st.session_state:
    st.session_state.controller = RobotArmController()

if 'positions' not in st.session_state:
    st.session_state.positions = {
        'thumb': 90, 'index': 90, 'middle': 90, 'ring': 90,
        'pinky': 90, 'wrist': 90, 'elbow': 90, 'shoulder': 90
    }

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Подключение
    st.subheader("📡 Arduino")
    port = st.selectbox("Порт", ARDUINO_PORTS, index=2)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Подключить", use_container_width=True):
            if st.session_state.controller.connect(port):
                st.success(f"Подключено к {port}")
                st.rerun()
            else:
                st.error("Ошибка!")
    with col2:
        if st.button("Отключить", use_container_width=True):
            st.session_state.controller.disconnect()
            st.rerun()
    
    status = "🟢 CONNECTED" if st.session_state.controller.connected else "🟡 SIMULATION"
    st.info(status)
    
    st.markdown("---")
    
    # Быстрые команды
    st.subheader("🎮 Команды")
    
    if st.button("🏠 Домой", use_container_width=True):
        st.session_state.controller.send_command("HOME")
        st.session_state.positions = {k: 90 for k in st.session_state.positions}
        st.rerun()
    
    if st.button("✊ Захват", use_container_width=True):
        st.session_state.controller.send_command("GRIP")
        st.rerun()
    
    if st.button("🖐️ Открыть", use_container_width=True):
        st.session_state.controller.send_command("OPEN")
        st.rerun()

# Основное окно
tab1, tab2 = st.tabs(["📹 Камера", "🎚️ Ручное управление"])

with tab1:
    st.subheader("Управление через камеру")
    st.markdown("""
    **Инструкция:**
    1. Разрешите доступ к камере
    2. Покажите руку в камеру
    3. Движения руки будут транслироваться на роборуку
    
    **Клавиши:**
    - `H` - домашняя позиция
    - `G` - захват
    - `O` - открыть ладонь
    - `Q` - выход
    """)
    
    st.warning("⚠️ Для работы камеры нужен браузер с поддержкой WebRTC")
    
    # Заглушка для камеры (Streamlit не поддерживает прямую работу с OpenCV)
    st.info("""
    💡 **Для полноценной работы с камерой запустите:**
    
    ```bash
    python execution/robot_arm_control.py
    ```
    
    Это откроет окно с видеопотоком и управлением через жесты.
    """)
    
    # Демонстрация
    demo_img = Image.new('RGB', (640, 480), color=(30, 30, 40))
    st.image(demo_img, caption="Окно камеры откроется в отдельном приложении", use_container_width=True)

with tab2:
    st.subheader("Ручное управление сервоприводами")
    
    # Слайдеры
    cols = st.columns(4)
    
    joints = [
        ('thumb', '👍 Большой'),
        ('index', '☝️ Указательный'),
        ('middle', '🖕 Средний'),
        ('ring', '💍 Безымянный'),
        ('pinky', '🤙 Мизинец'),
        ('wrist', '💫 Запястье'),
        ('elbow', '📐 Локоть'),
        ('shoulder', '📍 Плечо')
    ]
    
    for i, (joint, label) in enumerate(joints):
        col = cols[i % 4]
        with col:
            val = st.slider(
                label,
                0, 180,
                st.session_state.positions.get(joint, 90),
                key=f"slider_{joint}"
            )
            st.session_state.positions[joint] = val
    
    # Применение
    if st.button("💾 Применить позиции", type="primary", use_container_width=True):
        st.session_state.controller.set_positions(**st.session_state.positions)
        st.success("Позиции отправлены!")
    
    # Отображение текущих позиций
    st.markdown("---")
    st.subheader("📊 Текущие позиции")
    
    pos_data = {k: v for k, v in st.session_state.positions.items()}
    st.json(pos_data)

# Информация
st.markdown("---")
st.caption("""
🤖 **Industrial AI Hub | Роборука на Arduino**

Компоненты:
- Arduino Uno/Nano
- 8x Сервоприводов (SG90/MG996R)
- Веб-камера
- Python + MediaPipe + OpenCV
""")
