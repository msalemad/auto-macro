import sys
import time
import threading
import json
from pynput import mouse, keyboard
import pyautogui
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSpinBox, QFileDialog, QCheckBox
from PyQt6.QtCore import Qt

class MacroRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Recorder & Auto Clicker")
        self.setGeometry(100, 100, 400, 350)
        
        self.layout = QVBoxLayout()
        
        # Recording Controls
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.start_recording)
        self.layout.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.layout.addWidget(self.stop_btn)
        
        self.play_btn = QPushButton("Play Macro")
        self.play_btn.clicked.connect(self.play_macro)
        self.layout.addWidget(self.play_btn)
        
        self.save_btn = QPushButton("Save Macro")
        self.save_btn.clicked.connect(self.save_macro)
        self.layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load Macro")
        self.load_btn.clicked.connect(self.load_macro)
        self.layout.addWidget(self.load_btn)
        
        # Repetition Control
        self.repeats_label = QLabel("Repetitions:")
        self.layout.addWidget(self.repeats_label)
        self.repeats_spinbox = QSpinBox()
        self.repeats_spinbox.setRange(1, 9999)
        self.layout.addWidget(self.repeats_spinbox)
        
        # Auto Clicker Controls
        self.auto_click_label = QLabel("Auto Click Interval (ms):")
        self.layout.addWidget(self.auto_click_label)
        self.auto_click_spinbox = QSpinBox()
        self.auto_click_spinbox.setRange(1, 10000)
        self.layout.addWidget(self.auto_click_spinbox)
        
        self.auto_click_btn = QPushButton("Start Auto Clicker")
        self.auto_click_btn.clicked.connect(self.start_auto_clicker)
        self.layout.addWidget(self.auto_click_btn)
        
        self.stop_auto_click_btn = QPushButton("Stop Auto Clicker")
        self.stop_auto_click_btn.clicked.connect(self.stop_auto_clicker)
        self.layout.addWidget(self.stop_auto_click_btn)
        
        # Define Auto Click Hotkey
        self.hotkey_label = QLabel("Auto Click Hotkey: None")
        self.layout.addWidget(self.hotkey_label)
        self.set_hotkey_btn = QPushButton("Set Auto Click Hotkey")
        self.set_hotkey_btn.clicked.connect(self.set_hotkey)
        self.layout.addWidget(self.set_hotkey_btn)
        
        # Exit Button
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.close_application)
        self.layout.addWidget(self.exit_btn)
        
        self.setLayout(self.layout)
        
        self.recording = False
        self.macro = []
        self.auto_clicking = False
        self.auto_click_hotkey = None
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_hotkey_press)
        self.keyboard_listener.start()
    
    def start_recording(self):
        self.recording = True
        self.macro = []
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.mouse_listener.start()
        self.keyboard_listener.start()
    
    def stop_recording(self):
        self.recording = False
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
    
    def on_mouse_click(self, x, y, button, pressed):
        if self.recording:
            self.macro.append(("mouse", x, y, str(button), pressed, time.time()))
    
    def on_key_press(self, key):
        if self.recording:
            self.macro.append(("keyboard", str(key), time.time()))
    
    def play_macro(self):
        repetitions = self.repeats_spinbox.value()
        for _ in range(repetitions):
            for action in self.macro:
                if action[0] == "mouse":
                    _, x, y, button, pressed, timestamp = action
                    pyautogui.click(x, y) if pressed else None
                elif action[0] == "keyboard":
                    _, key, timestamp = action
                    pyautogui.press(key.replace("'", ""))
                time.sleep(0.1)
    
    def save_macro(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Macro", "", "JSON Files (*.json)")
        if filename:
            with open(filename, "w") as file:
                json.dump(self.macro, file)
    
    def load_macro(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Macro", "", "JSON Files (*.json)")
        if filename:
            with open(filename, "r") as file:
                self.macro = json.load(file)
    
    def start_auto_clicker(self):
        interval = self.auto_click_spinbox.value() / 1000
        self.auto_clicking = True
        threading.Thread(target=self.auto_clicker_thread, args=(interval,), daemon=True).start()
    
    def stop_auto_clicker(self):
        self.auto_clicking = False
    
    def auto_clicker_thread(self, interval):
        while self.auto_clicking:
            pyautogui.click()
            time.sleep(interval)
    
    def set_hotkey(self):
        self.hotkey_label.setText("Press a key...")
        listener = keyboard.Listener(on_press=self.on_hotkey_set)
        listener.start()
    
    def on_hotkey_set(self, key):
        self.auto_click_hotkey = key
        self.hotkey_label.setText(f"Auto Click Hotkey: {key}")
        return False
    
    def on_hotkey_press(self, key):
        if key == self.auto_click_hotkey:
            self.start_auto_clicker()
    
    def close_application(self):
        self.close()
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MacroRecorder()
    window.show()
    sys.exit(app.exec())
