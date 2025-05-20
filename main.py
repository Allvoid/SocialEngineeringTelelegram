#!/usr/bin/env python3
# main.py
import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QHBoxLayout, QTextEdit, QLineEdit, QMessageBox
)
from PyQt6.QtCore import QProcess

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'tokens.json')

class BotController(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = {}
        self.token_inputs = {}
        self.start_buttons = {}
        self.saved_tokens = {}
        self.load_tokens()
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
        self.resize(600, 450)
        layout = QVBoxLayout()

        # Панель кнопок и ввода токена
        for name, script in self.bots.items():
            hbox = QHBoxLayout()
            label = QLabel(name)

            token_input = QLineEdit()
            token_input.setPlaceholderText('Токен (обязательно)')
            # Если был сохранён токен, подставляем его
            token_input.setText(self.saved_tokens.get(name, ''))
            token_input.textChanged.connect(lambda text, n=name: self.on_token_changed(n, text))
            self.token_inputs[name] = token_input

            button = QPushButton('Запустить')
            button.setEnabled(bool(token_input.text().strip()))
            button.setCheckable(True)
            button.clicked.connect(lambda checked, n=name, s=script, b=button: self.toggle_bot(n, s, b))
            self.start_buttons[name] = button

            hbox.addWidget(label)
            hbox.addWidget(token_input)
            hbox.addStretch(1)
            hbox.addWidget(button)
            layout.addLayout(hbox)

        # Кнопка сохранения токенов
        save_btn = QPushButton('Сохранить токены')
        save_btn.clicked.connect(self.save_tokens)
        layout.addWidget(save_btn)

        # Окно для логов
        log_label = QLabel('Логи:')
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(log_label)
        layout.addWidget(self.log_output)
        self.setLayout(layout)

    def load_tokens(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.saved_tokens = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.saved_tokens = {}

    def save_tokens(self):
        # Собираем все токены
        tokens = {name: inp.text().strip() for name, inp in self.token_inputs.items() if inp.text().strip()}
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, 'Успешно', 'Токены сохранены')
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить токены:\n{e}')

    def on_token_changed(self, name, text):
        button = self.start_buttons.get(name)
        if button and not button.isChecked():
            button.setEnabled(bool(text.strip()))

    def toggle_bot(self, name, script, button):
        if button.isChecked():
            button.setText('Остановить')
            self.token_inputs[name].setEnabled(False)

            proc = QProcess(self)
            script_path = os.path.join(os.path.dirname(__file__), script)
            args = [script_path]
            token = self.token_inputs[name].text().strip()
            args.append(token)
            proc.setProgram(sys.executable)
            proc.setArguments(args)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(lambda n=name, p=proc: self.handle_output(n, p))
            proc.start()
            self.processes[name] = proc
        else:
            button.setText('Запустить')
            self.token_inputs[name].setEnabled(True)
            current_text = self.token_inputs[name].text().strip()
            button.setEnabled(bool(current_text))

            proc = self.processes.pop(name, None)
            if proc:
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
