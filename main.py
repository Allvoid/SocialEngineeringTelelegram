#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from bot_controller import BotController

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BotController()
    window.show()
    sys.exit(app.exec())
