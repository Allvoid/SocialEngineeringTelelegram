import os

# Файл, где хранятся токены по именам ботов
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'tokens.json')

# Названия ботов и соответствующие скрипты
BOT_SCRIPTS = {
    'Тест IQ': 'iq-test.py',
    'Регистрация': 'Reg.py',
    'Крипто-Бот': 'CryptoBot.py',
    'Подарочный Бот': 'Gifter.py'
}
