#!/usr/bin/env python3
# main.py
import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QLineEdit, QMessageBox, QTextEdit, QGridLayout
)
from PyQt6.QtCore import QProcess, Qt

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'tokens.json')

class BotController(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = {}
        self.token_inputs = {}
        self.start_buttons = {}
        self.save_buttons = {}
        self.clear_buttons = {}
        self.saved_tokens = {}
        self.load_tokens()
        # Красивые названия ботов
        self.bots = {
            'Тест IQ': 'iq-test.py',
            'Регистрация': 'Reg.py',
            'Крипто-Бот': 'CryptoBot.py',
            'Подарочный Бот': 'Gifter.py'
        }
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Управление ботами')
        self.resize(800, 480)

        main_layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        # Заголовки столбцов
        headers = ['Бот', 'Токен', 'Сохранить', 'Очистить', 'Запустить']
        for col, text in enumerate(headers):
            lbl = QLabel(f'<b>{text}</b>')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, 0, col)

        for row, (name, script) in enumerate(self.bots.items(), start=1):
            # Label
            lbl = QLabel(name)
            grid.addWidget(lbl, row, 0)

            # Token input
            token_input = QLineEdit()
            token_input.setPlaceholderText('Введите токен')
            token_input.setText(self.saved_tokens.get(name, ''))
            token_input.textChanged.connect(lambda text, n=name: self.on_token_changed(n, text))
            self.token_inputs[name] = token_input
            grid.addWidget(token_input, row, 1)

            # Save button
            save_btn = QPushButton('Сохранить')
            save_btn.setEnabled(bool(token_input.text().strip()))
            save_btn.clicked.connect(lambda _, n=name: self.save_token(n))
            self.save_buttons[name] = save_btn
            grid.addWidget(save_btn, row, 2)

            # Clear button
            clear_btn = QPushButton('Очистить')
            clear_btn.setEnabled(bool(self.saved_tokens.get(name, '')))
            clear_btn.clicked.connect(lambda _, n=name: self.clear_token(n))
            self.clear_buttons[name] = clear_btn
            grid.addWidget(clear_btn, row, 3)

            # Start/Stop button
            start_btn = QPushButton('Запустить')
            start_btn.setEnabled(bool(token_input.text().strip()))
            start_btn.setCheckable(True)
            start_btn.clicked.connect(lambda checked, n=name, s=script, b=start_btn: self.toggle_bot(n, s, b))
            self.start_buttons[name] = start_btn
            grid.addWidget(start_btn, row, 4)

        # Настройка растяжения колонок
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(4, 1)

        main_layout.addLayout(grid)

        # Логи
        log_label = QLabel('Логи:')
        main_layout.addWidget(log_label)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        main_layout.addWidget(self.log_output)

    def load_tokens(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.saved_tokens = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.saved_tokens = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.saved_tokens, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить конфигурацию:\n{e}')

    def save_token(self, name):
        token = self.token_inputs[name].text().strip()
        if not token:
            QMessageBox.warning(self, 'Ошибка', 'Токен не может быть пустым')
            return
        self.saved_tokens[name] = token
        self.save_config()
        QMessageBox.information(self, 'Успешно', f'Токен для "{name}" сохранён')
        self.save_buttons[name].setEnabled(False)
        self.clear_buttons[name].setEnabled(True)

    def clear_token(self, name):
        self.token_inputs[name].clear()
        if name in self.saved_tokens:
            del self.saved_tokens[name]
            self.save_config()
        QMessageBox.information(self, 'Успешно', f'Токен для "{name}" очищен')
        self.save_buttons[name].setEnabled(False)
        self.clear_buttons[name].setEnabled(False)
        self.start_buttons[name].setEnabled(False)

    def on_token_changed(self, name, text):
        is_nonempty = bool(text.strip())
        if name in self.save_buttons:
            self.save_buttons[name].setEnabled(is_nonempty)
        if name in self.start_buttons:
            if not self.start_buttons[name].isChecked():
                self.start_buttons[name].setEnabled(is_nonempty)
        if name in self.clear_buttons:
            self.clear_buttons[name].setEnabled(bool(self.saved_tokens.get(name, '')))

    def toggle_bot(self, name, script, button):
        if button.isChecked():
            button.setText('Остановить')
            self.token_inputs[name].setEnabled(False)
            self.save_buttons[name].setEnabled(False)
            self.clear_buttons[name].setEnabled(False)

            proc = QProcess(self)
            script_path = os.path.join(os.path.dirname(__file__), script)
            args = [script_path, self.token_inputs[name].text().strip()]
            proc.setProgram(sys.executable)
            proc.setArguments(args)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(lambda n=name, p=proc: self.handle_output(n, p))
            proc.start()
            self.processes[name] = proc
        else:
            button.setText('Запустить')
            self.token_inputs[name].setEnabled(True)
            text = self.token_inputs[name].text().strip()
            self.save_buttons[name].setEnabled(bool(text))
            self.clear_buttons[name].setEnabled(bool(self.saved_tokens.get(name, '')))
            button.setEnabled(bool(text))

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
