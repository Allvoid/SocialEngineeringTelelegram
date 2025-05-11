#!/usr/bin/env python3
# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import QProcess

class BotController(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = {}
        # Названия ботов и соответствующие скрипты
        self.bots = {
            'IQ Test': 'iq-test.py',
            'Reg': 'Reg.py',
            'CryptoBot': 'CryptoBot.py',
            'Gifter': 'Gifter.py'
        }
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Bot Controller')
        layout = QVBoxLayout()

        for name, script in self.bots.items():
            hbox = QHBoxLayout()
            label = QLabel(name)
            button = QPushButton('Start')
            button.setCheckable(True)
            # Замыкаем текущие name, script и кнопку
            button.clicked.connect(lambda checked, n=name, s=script, b=button: self.toggle_bot(n, s, b))
            hbox.addWidget(label)
            hbox.addStretch(1)
            hbox.addWidget(button)
            layout.addLayout(hbox)

        self.setLayout(layout)

    def toggle_bot(self, name, script, button):
        if button.isChecked():
            button.setText('Stop')
            proc = QProcess(self)
            script_path = os.path.join(os.path.dirname(__file__), script)
            proc.start(sys.executable, [script_path])
            self.processes[name] = proc
        else:
            button.setText('Start')
            proc = self.processes.pop(name, None)
            if proc is not None:
                proc.terminate()
                proc.waitForFinished(3000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BotController()
    window.show()
    sys.exit(app.exec())
