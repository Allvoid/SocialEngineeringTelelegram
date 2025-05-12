#!/usr/bin/env python3
# main.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QHBoxLayout, QTextEdit, QScrollArea
)
from PyQt6.QtCore import QProcess, Qt

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
        self.resize(600, 400)
        layout = QVBoxLayout()

        # Панель кнопок
        for name, script in self.bots.items():
            hbox = QHBoxLayout()
            label = QLabel(name)
            button = QPushButton('Запустить')
            button.setCheckable(True)
            button.clicked.connect(lambda checked, n=name, s=script, b=button: self.toggle_bot(n, s, b))
            hbox.addWidget(label)
            hbox.addStretch(1)
            hbox.addWidget(button)
            layout.addLayout(hbox)

        # Окно для логов
        log_label = QLabel('Логи:')
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(log_label)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def toggle_bot(self, name, script, button):
        if button.isChecked():
            button.setText('Остановить')
            proc = QProcess(self)
            script_path = os.path.join(os.path.dirname(__file__), script)
            proc.setProgram(sys.executable)
            proc.setArguments([script_path])
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(lambda n=name, p=proc: self.handle_output(n, p))
            proc.start()
            self.processes[name] = proc
        else:
            button.setText('Запустить')
            proc = self.processes.pop(name, None)
            if proc is not None:
                proc.terminate()
                proc.waitForFinished(3000)

    def handle_output(self, name, process):
        data = process.readAllStandardOutput().data().decode('utf-8').strip()
        for line in data.splitlines():
            message = f'«{line}», была получена от бота «{name}»'
            self.log_output.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BotController()
    window.show()
    sys.exit(app.exec())
