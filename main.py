import sys
import time
import threading
import json
import os
import keyboard
import mouse
import pyautogui
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSpinBox, QFileDialog, QCheckBox, QTextEdit, QHBoxLayout, QMenu, QSplitter
from PyQt6.QtCore import Qt

class MacroRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grabador de Macros y Auto Clicker")
        self.setGeometry(100, 100, 800, 400)
        
        self.layout = QHBoxLayout()
        
        # Consola izquierda para mostrar las acciones de la macro cargadas
        self.macro_console = QTextEdit()
        self.macro_console.setReadOnly(True)
        self.macro_console.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.macro_console.customContextMenuRequested.connect(self.show_macro_console_context_menu)
        self.layout.addWidget(self.macro_console)
        
        # Layout para los botones y controles
        self.controls_layout = QVBoxLayout()
        
        # Controles de grabación
        self.record_btn = QPushButton("Iniciar Grabación")
        self.record_btn.clicked.connect(self.start_recording)
        self.controls_layout.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("Detener Grabación")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.controls_layout.addWidget(self.stop_btn)
        
        self.play_btn = QPushButton("Reproducir Macro")
        self.play_btn.clicked.connect(self.play_macro)
        self.controls_layout.addWidget(self.play_btn)
        
        self.save_btn = QPushButton("Guardar Macro")
        self.save_btn.clicked.connect(self.save_macro)
        self.controls_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Cargar Macro")
        self.load_btn.clicked.connect(self.load_macro)
        self.controls_layout.addWidget(self.load_btn)
        
        # Control de repeticiones
        self.repeats_label = QLabel("Repeticiones:")
        self.controls_layout.addWidget(self.repeats_label)
        self.repeats_spinbox = QSpinBox()
        self.repeats_spinbox.setRange(1, 9999)
        self.controls_layout.addWidget(self.repeats_spinbox)
        
        # Controles de Auto Clicker
        self.auto_click_label = QLabel("Intervalo de Auto Click (ms):")
        self.controls_layout.addWidget(self.auto_click_label)
        self.auto_click_spinbox = QSpinBox()
        self.auto_click_spinbox.setRange(1, 10000)
        self.controls_layout.addWidget(self.auto_click_spinbox)
        
        self.auto_click_btn = QPushButton("Iniciar Auto Clicker")
        self.auto_click_btn.clicked.connect(self.start_auto_clicker)
        self.controls_layout.addWidget(self.auto_click_btn)
        
        self.stop_auto_click_btn = QPushButton("Detener Auto Clicker")
        self.stop_auto_click_btn.clicked.connect(self.stop_auto_clicker)
        self.controls_layout.addWidget(self.stop_auto_click_btn)
        
        # Definir tecla de acceso rápido para Auto Click
        self.hotkey_label = QLabel("Tecla de Auto Click: Ninguna")
        self.controls_layout.addWidget(self.hotkey_label)
        self.set_hotkey_btn = QPushButton("Definir Tecla de Auto Click")
        self.set_hotkey_btn.clicked.connect(self.set_hotkey)
        self.controls_layout.addWidget(self.set_hotkey_btn)
        
        # Definir tecla de acceso rápido para grabación de macro
        self.record_hotkey_label = QLabel("Tecla de Grabación de Macro: Ninguna")
        self.controls_layout.addWidget(self.record_hotkey_label)
        self.set_record_hotkey_btn = QPushButton("Definir Tecla de Grabación de Macro")
        self.set_record_hotkey_btn.clicked.connect(self.set_record_hotkey)
        self.controls_layout.addWidget(self.set_record_hotkey_btn)
        
        # Definir tecla de acceso rápido para reproducción de macro
        self.play_hotkey_label = QLabel("Tecla de Reproducción de Macro: Ninguna")
        self.controls_layout.addWidget(self.play_hotkey_label)
        self.set_play_hotkey_btn = QPushButton("Definir Tecla de Reproducción de Macro")
        self.set_play_hotkey_btn.clicked.connect(self.set_play_hotkey)
        self.controls_layout.addWidget(self.set_play_hotkey_btn)
        
        # Checkbox para enumerar los pasos de la macro
        self.enumerate_checkbox = QCheckBox("Enumerar pasos de la macro")
        self.enumerate_checkbox.stateChanged.connect(self.update_macro_console)
        self.controls_layout.addWidget(self.enumerate_checkbox)
        
        # Botón de reinicio
        self.reset_btn = QPushButton("Reiniciar")
        self.reset_btn.clicked.connect(self.reset_interface)
        self.controls_layout.addWidget(self.reset_btn)
        
        # Botón de verificación y ajuste de DPI
        self.dpi_btn = QPushButton("Verificar y Ajustar DPI")
        self.dpi_btn.clicked.connect(self.verify_and_adjust_dpi)
        self.controls_layout.addWidget(self.dpi_btn)
        
        # Botón de salida
        self.exit_btn = QPushButton("Salir")
        self.exit_btn.clicked.connect(self.close_application)
        self.controls_layout.addWidget(self.exit_btn)
        
        self.layout.addLayout(self.controls_layout)
        
        # Consola derecha para mostrar el estado de las operaciones
        self.status_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.status_console = QTextEdit()
        self.status_console.setReadOnly(True)
        self.status_splitter.addWidget(self.status_console)
        
        self.realtime_console = QTextEdit()
        self.realtime_console.setReadOnly(True)
        self.status_splitter.addWidget(self.realtime_console)
        
        self.layout.addWidget(self.status_splitter)
        
        self.setLayout(self.layout)
        
        self.recording = False
        self.macro = []
        self.auto_clicking = False
        self.auto_click_hotkey = None
        self.record_hotkey = None
        self.play_hotkey = None
        
        keyboard.on_press(self.on_hotkey_press)
        
        # Crear carpeta "macros" si no existe
        if not os.path.exists("macros"):
            os.makedirs("macros")
        
        # Mostrar información inicial en la consola de estado
        self.show_initial_info()
    
    def show_initial_info(self):
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        scaling_factor = screen.devicePixelRatio()
        resolution = screen.size()
        mouse_sensitivity = mouse.get_position()  # Esto es solo un ejemplo, no obtiene la sensibilidad real del ratón
        
        self.status_console.append(f"Resolución actual: {resolution.width()}x{resolution.height()}")
        self.status_console.append(f"DPI actual: {dpi}")
        self.status_console.append(f"Factor de escalado: {scaling_factor}")
        self.status_console.append(f"Sensibilidad del ratón (posición actual): {mouse_sensitivity}")
        
        # Leer configuraciones del archivo qt.conf
        qt_conf_path = "qt.conf"
        if os.path.exists(qt_conf_path):
            with open(qt_conf_path, "r") as file:
                qt_conf_content = file.read()
            self.status_console.append("Configuraciones en qt.conf:")
            self.status_console.append(qt_conf_content)
        else:
            self.status_console.append("Archivo qt.conf no encontrado.")
    
    def verify_and_adjust_dpi(self):
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        scaling_factor = screen.devicePixelRatio()
        resolution = screen.size()
        
        self.realtime_console.append(f"Verificando DPI...")
        self.realtime_console.append(f"Resolución actual: {resolution.width()}x{resolution.height()}")
        self.realtime_console.append(f"DPI actual: {dpi}")
        self.realtime_console.append(f"Factor de escalado: {scaling_factor}")
        
        # Ajustar DPI si es necesario (esto es solo un ejemplo, Qt maneja esto automáticamente)
        if dpi != 96:
            self.realtime_console.append("Ajustando DPI...")
            # Aquí puedes agregar código para ajustar el DPI si es necesario
            self.realtime_console.append("DPI ajustado.")
        else:
            self.realtime_console.append("DPI no necesita ajuste.")
    
    def start_recording(self):
        self.recording = True
        self.macro = []
        mouse.hook(self.on_mouse_event)
        keyboard.hook(self.on_key_event)
        self.status_console.append("Grabación iniciada.")
        self.realtime_console.append("Grabación iniciada.")
    
    def stop_recording(self):
        self.recording = False
        try:
            mouse.unhook(self.on_mouse_event)
        except ValueError:
            pass  # Ignore if the handler is not in the list
        try:
            keyboard.unhook(self.on_key_event)
        except KeyError:
            pass  # Ignore if the handler is not in the list
        self.status_console.append("Grabación detenida.")
        self.realtime_console.append("Grabación detenida.")
    
    def on_mouse_event(self, event):
        if self.recording:
            if isinstance(event, mouse.ButtonEvent):
                self.macro.append(("mouse", event.button, event.event_type == 'down', time.time()))
                self.realtime_console.append(f"Mouse: {event.button} {'down' if event.event_type == 'down' else 'up'}")
            elif isinstance(event, mouse.MoveEvent):
                self.macro.append(("mouse_move", event.x, event.y, time.time()))
                self.realtime_console.append(f"Mouse Move: ({event.x}, {event.y})")
    
    def on_key_event(self, event):
        if self.recording:
            self.macro.append(("keyboard", event.name, time.time()))
            self.realtime_console.append(f"Keyboard: {event.name}")
    
    def play_macro(self):
        if not self.macro:
            self.status_console.append("No hay macro cargada para reproducir.")
            self.realtime_console.append("No hay macro cargada para reproducir.")
            return
        
        repetitions = self.repeats_spinbox.value()
        self.status_console.append(f"Reproduciendo macro {repetitions} veces.")
        self.realtime_console.append(f"Reproduciendo macro {repetitions} veces.")
        for _ in range(repetitions):
            for action in self.macro:
                if action[0] == "mouse":
                    _, button, pressed, timestamp = action
                    if pressed:
                        pyautogui.click(button=button)
                        self.realtime_console.append(f"Mouse: {button} click")
                elif action[0] == "mouse_move":
                    _, x, y, timestamp = action
                    pyautogui.moveTo(x, y)
                    self.realtime_console.append(f"Mouse Move: ({x}, {y})")
                elif action[0] == "keyboard":
                    _, key, timestamp = action
                    pyautogui.press(key)
                    self.realtime_console.append(f"Keyboard: {key}")
                time.sleep(0.1)
        self.status_console.append("Reproducción de macro completada.")
        self.realtime_console.append("Reproducción de macro completada.")
    
    def save_macro(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Macro", "macros/", "Archivos JSON (*.json)")
        if filename:
            with open(filename, "w") as file:
                json.dump(self.macro, file)
            self.status_console.append(f"Macro guardada en {filename}.")
            self.realtime_console.append(f"Macro guardada en {filename}.")
    
    def load_macro(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Cargar Macro", "macros/", "Archivos JSON (*.json)")
        if filename:
            with open(filename, "r") as file:
                self.macro = json.load(file)
            self.status_console.append(f"Macro cargada desde {filename}.")
            self.realtime_console.append(f"Macro cargada desde {filename}.")
            self.update_macro_console()
    
    def update_macro_console(self):
        self.macro_console.clear()
        for i, action in enumerate(self.macro):
            if action[0] == "mouse":
                _, button, pressed, timestamp = action
                step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                self.macro_console.append(f"{step}Mouse: {button} {'down' if pressed else 'up'} at {timestamp}")
            elif action[0] == "mouse_move":
                _, x, y, timestamp = action
                step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                self.macro_console.append(f"{step}Mouse Move: ({x}, {y}) at {timestamp}")
            elif action[0] == "keyboard":
                _, key, timestamp = action
                step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                self.macro_console.append(f"{step}Keyboard: {key} at {timestamp}")
    
    def show_macro_console_context_menu(self, position):
        menu = QMenu()
        export_action = menu.addAction("Exportar a .txt")
        action = menu.exec(self.macro_console.mapToGlobal(position))
        if action == export_action:
            self.export_macro_to_txt()
    
    def export_macro_to_txt(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar Macro", "macros/", "Archivos de Texto (*.txt)")
        if filename:
            with open(filename, "w") as file:
                for i, action in enumerate(self.macro):
                    if action[0] == "mouse":
                        _, button, pressed, timestamp = action
                        step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                        file.write(f"{step}Mouse: {button} {'down' if pressed else 'up'} at {timestamp}\n")
                    elif action[0] == "mouse_move":
                        _, x, y, timestamp = action
                        step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                        file.write(f"{step}Mouse Move: ({x}, {y}) at {timestamp}\n")
                    elif action[0] == "keyboard":
                        _, key, timestamp = action
                        step = f"Paso {i+1}: " if self.enumerate_checkbox.isChecked() else ""
                        file.write(f"{step}Keyboard: {key} at {timestamp}\n")
            self.status_console.append(f"Macro exportada a {filename}.")
            self.realtime_console.append(f"Macro exportada a {filename}.")
    
    def start_auto_clicker(self):
        if not self.auto_clicking:
            interval = self.auto_click_spinbox.value() / 1000
            self.auto_clicking = True
            threading.Thread(target=self.auto_clicker_thread, args=(interval,), daemon=True).start()
            self.status_console.append("Auto Clicker iniciado.")
            self.realtime_console.append("Auto Clicker iniciado.")
    
    def stop_auto_clicker(self):
        self.auto_clicking = False
        self.status_console.append("Auto Clicker detenido.")
        self.realtime_console.append("Auto Clicker detenido.")
    
    def auto_clicker_thread(self, interval):
        while self.auto_clicking:
            pyautogui.click()
            self.realtime_console.append("Auto Click")
            time.sleep(interval)
    
    def set_hotkey(self):
        self.hotkey_label.setText("Presiona una tecla...")
        keyboard.hook(self.on_hotkey_set)
    
    def on_hotkey_set(self, event):
        self.auto_click_hotkey = event.name
        self.hotkey_label.setText(f"Tecla de Auto Click: {event.name}")
        keyboard.unhook(self.on_hotkey_set)
    
    def set_record_hotkey(self):
        self.record_hotkey_label.setText("Presiona una tecla...")
        keyboard.hook(self.on_record_hotkey_set)
    
    def on_record_hotkey_set(self, event):
        self.record_hotkey = event.name
        self.record_hotkey_label.setText(f"Tecla de Grabación de Macro: {event.name}")
        keyboard.unhook(self.on_record_hotkey_set)
    
    def set_play_hotkey(self):
        self.play_hotkey_label.setText("Presiona una tecla...")
        keyboard.hook(self.on_play_hotkey_set)
    
    def on_play_hotkey_set(self, event):
        self.play_hotkey = event.name
        self.play_hotkey_label.setText(f"Tecla de Reproducción de Macro: {event.name}")
        keyboard.unhook(self.on_play_hotkey_set)
    
    def on_hotkey_press(self, event):
        if event.name == self.auto_click_hotkey:
            if self.auto_clicking:
                self.stop_auto_clicker()
            else:
                self.start_auto_clicker()
        elif event.name == self.record_hotkey:
            if self.recording:
                self.stop_recording()
            else:
                self.start_recording()
        elif event.name == self.play_hotkey:
            self.play_macro()
    
    def reset_interface(self):
        self.macro = []
        self.recording = False
        self.auto_clicking = False
        self.auto_click_hotkey = None
        self.record_hotkey = None
        self.play_hotkey = None
        self.macro_console.clear()
        self.status_console.clear()
        self.realtime_console.clear()
        self.status_console.append("Interfaz reiniciada.")
        self.realtime_console.append("Interfaz reiniciada.")
        self.show_initial_info()
    
    def close_application(self):
        self.close()
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MacroRecorder()
    window.show()
    sys.exit(app.exec())