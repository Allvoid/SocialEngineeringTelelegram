import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel,
    QLineEdit, QMessageBox, QTextEdit, QGridLayout
)
from PyQt6.QtCore import QProcess, Qt

from constants import BOT_SCRIPTS
from config_manager import ConfigManager


class BotController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Управление ботами')
        self.resize(800, 520)

        self.config = ConfigManager()
        self.processes = {}

        self.token_inputs = {}
        self.save_buttons = {}
        self.clear_buttons = {}
        self.start_buttons = {}

        self._build_ui()

    def _build_ui(self):
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

        # Строки с ботами
        for row, (name, script) in enumerate(BOT_SCRIPTS.items(), start=1):
            # Название бота
            grid.addWidget(QLabel(name), row, 0)

            # Поле ввода токена
            inp = QLineEdit()
            inp.setPlaceholderText('Введите токен')
            inp.setText(self.config.get(name))
            inp.textChanged.connect(lambda txt, n=name: self._on_token_change(n, txt))
            self.token_inputs[name] = inp
            grid.addWidget(inp, row, 1)

            # Кнопка Сохранить
            btn_save = QPushButton('Сохранить')
            btn_save.setEnabled(bool(inp.text().strip()))
            btn_save.clicked.connect(lambda _, n=name: self._save_token(n))
            self.save_buttons[name] = btn_save
            grid.addWidget(btn_save, row, 2)

            # Кнопка Очистить
            btn_clear = QPushButton('Очистить')
            btn_clear.setEnabled(bool(self.config.get(name)))
            btn_clear.clicked.connect(lambda _, n=name: self._clear_token(n))
            self.clear_buttons[name] = btn_clear
            grid.addWidget(btn_clear, row, 3)

            # Кнопка Запустить/Остановить
            btn_start = QPushButton('Запустить')
            btn_start.setCheckable(True)
            btn_start.setEnabled(bool(inp.text().strip()))
            btn_start.clicked.connect(lambda checked, n=name, s=script, b=btn_start: self._toggle_bot(n, s, b))
            self.start_buttons[name] = btn_start
            grid.addWidget(btn_start, row, 4)

        # Настройка растяжения колонок
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(4, 1)
        main_layout.addLayout(grid)

        # Кнопка «Запустить всех» / «Остановить всех»
        self.all_button = QPushButton('Запустить всех')
        self.all_button.setEnabled(any(btn.isEnabled() for btn in self.start_buttons.values()))
        self.all_button.clicked.connect(self._toggle_all)
        main_layout.addWidget(self.all_button)

        # Блок логов
        main_layout.addWidget(QLabel('Логи:'))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        main_layout.addWidget(self.log)

        # Первоначальная проверка текста кнопки «Запустить всех»
        self._update_all_button_label()

    def _on_token_change(self, name, text):
        nonempty = bool(text.strip())
        self.save_buttons[name].setEnabled(nonempty)
        if not self.start_buttons[name].isChecked():
            self.start_buttons[name].setEnabled(nonempty)
        self._update_all_button_label()

    def _save_token(self, name):
        tok = self.token_inputs[name].text().strip()
        if not tok:
            QMessageBox.warning(self, 'Ошибка', 'Токен не может быть пустым')
            return
        try:
            self.config.set(name, tok)
            QMessageBox.information(self, 'Успешно', f'Токен для "{name}" сохранён')
            self.save_buttons[name].setEnabled(False)
            self.clear_buttons[name].setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', str(e))
        self._update_all_button_label()

    def _clear_token(self, name):
        self.token_inputs[name].clear()
        try:
            self.config.clear(name)
            QMessageBox.information(self, 'Успешно', f'Токен для "{name}" удалён')
            self.save_buttons[name].setEnabled(False)
            self.clear_buttons[name].setEnabled(False)
            self.start_buttons[name].setEnabled(False)
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', str(e))
        self._update_all_button_label()

    def _toggle_bot(self, name, script, button):
        if button.isChecked():
            button.setText('Остановить')
            self.token_inputs[name].setEnabled(False)
            self.save_buttons[name].setEnabled(False)
            self.clear_buttons[name].setEnabled(False)

            proc = QProcess(self)
            path = os.path.join(os.path.dirname(__file__), script)
            tok = self.token_inputs[name].text().strip()
            proc.setProgram(sys.executable)
            proc.setArguments([path, tok])
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(lambda n=name, p=proc: self._handle_output(n, p))
            proc.start()
            self.processes[name] = proc
        else:
            button.setText('Запустить')
            self.token_inputs[name].setEnabled(True)
            txt = self.token_inputs[name].text().strip()
            self.save_buttons[name].setEnabled(bool(txt))
            self.clear_buttons[name].setEnabled(bool(self.config.get(name)))
            button.setEnabled(bool(txt))

            proc = self.processes.pop(name, None)
            if proc:
                proc.terminate()
                proc.waitForFinished(3000)

        self._update_all_button_label()

    def _toggle_all(self):
        # Если все боты запущены, останавливаем их, иначе запускаем всех, у кого есть токен
        all_running = all(btn.isChecked() for btn in self.start_buttons.values())
        if all_running:
            for name, btn in self.start_buttons.items():
                if btn.isChecked():
                    btn.click()  # вызывает _toggle_bot для остановки
        else:
            for name, btn in self.start_buttons.items():
                if not btn.isChecked() and btn.isEnabled():
                    btn.click()  # вызывает _toggle_bot для запуска
        self._update_all_button_label()

    def _update_all_button_label(self):
        # Если количество запущенных кнопок равно числу всех ботов, считаем, что все запущены
        total = len(self.start_buttons)
        running = sum(1 for btn in self.start_buttons.values() if btn.isChecked())
        if running == total:
            self.all_button.setText('Остановить всех')
        else:
            self.all_button.setText('Запустить всех')
        # Кнопка «Запустить всех» доступна, если хотя бы один бот может быть запущен или работает
        self.all_button.setEnabled(any(btn.isEnabled() or btn.isChecked() for btn in self.start_buttons.values()))

    def _handle_output(self, name, proc):
        out = proc.readAllStandardOutput().data().decode('utf-8').strip()
        for line in out.splitlines():
            self.log.append(f'«{line}», была получена от бота «{name}»')
