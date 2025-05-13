import os
import logging
import asyncio
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Chat,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

import sys

# Если при запуске передали токен, забираем его, иначе — None или какое-то значение по умолчанию
if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    TOKEN = '<ВАШ_ТОКЕН_ПО_УМОЛЧАНИЮ>'  # можно оставить None, если без токена бот не запускается


# --- Конфигурация ---
# BOT_TOKEN берём из переменных окружения, чтобы не хранить его в коде
BOT_TOKEN = os.getenv('CRYPTOBOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError("CRYPTOBOT_TOKEN environment variable is not set")

# Состояния разговора
SELECT_ACTION, SELECT_CURRENCY, WAIT_CONTACT = range(3)

# Клавиатуры
action_markup = ReplyKeyboardMarkup([['Купить', 'Продать']],
                                    one_time_keyboard=True, resize_keyboard=True)
CRYPTO_LIST = [
    'Bitcoin (BTC)',
    'Ethereum (ETH)',
    'Ripple (XRP)',
    'Litecoin (LTC)',
    'Dogecoin (DOGE)',
]
crypto_keyboard = [CRYPTO_LIST[i:i+2] for i in range(0, len(CRYPTO_LIST), 2)]
crypto_markup = ReplyKeyboardMarkup(crypto_keyboard,
                                    one_time_keyboard=True, resize_keyboard=True)

# --- Rate Limiter ---
# простой in-memory лимитер: не более 5 сообщений в минуту на пользователя
USER_RATE = defaultdict(list)
RATE_LIMIT = 5  # сообщений
RATE_PERIOD = timedelta(minutes=1)

def rate_limited(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        now = datetime.utcnow()
        # очистка старых записей
        USER_RATE[user_id] = [t for t in USER_RATE[user_id] if now - t < RATE_PERIOD]
        if len(USER_RATE[user_id]) >= RATE_LIMIT:
            # игнорируем или шлём предупреждение
            return await update.message.reply_text(
                "⚠️ Слишком много запросов. Пожалуйста, подождите минуту и попробуйте снова."
            )
        USER_RATE[user_id].append(now)
        return await func(update, context, *args, **kwargs)
    return wrapper

# --- Обработчики ---

@rate_limited
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Разрешаем работу только в приватных чатах
    if update.effective_chat.type != Chat.PRIVATE:
        return await update.message.reply_text("Этот бот работает только в личных сообщениях.")
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Добро пожаловать в наш CryptoBot.\n"
        "Пожалуйста, выберите, что вы хотите сделать:",
        reply_markup=action_markup
    )
    return SELECT_ACTION

@rate_limited
async def action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    # Вдобавок проверяем, что текст действительно из списка
    if choice not in ('Купить', 'Продать'):
        return await update.message.reply_text("Пожалуйста, выберите одну из кнопок.")
    context.user_data['action'] = choice
    await update.message.reply_html(
        f"📊 Пример операций:\n"
        "- 0.005 BTC за 100 USD\n"
        "- 1 ETH за 2000 USD\n\n"
        f"Вы выбрали: <b>{choice}</b>.\n"
        "Теперь выберите криптовалюту:",
        reply_markup=crypto_markup
    )
    return SELECT_CURRENCY

@rate_limited
async def currency_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    crypto = update.message.text
    if crypto not in CRYPTO_LIST:
        return await update.message.reply_text("Пожалуйста, выберите криптовалюту кнопкой.")
    context.user_data['crypto'] = crypto
    # Заглушка курса → здесь позже подставить реальные данные через API
    await update.message.reply_html(
        f"Вы выбрали: <b>{crypto}</b>\n"
        "Данный курс к USD: <b>???</b>\n\n"
        "Курс будет доступен после авторизации."
    )
    # Запрашиваем контакт, и проверим, что контакт именно того, кто пишет
    contact_button = KeyboardButton(
        text='📞 Отправить мой номер телефона',
        request_contact=True
    )
    kb = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Для продолжения авторизации отправьте, пожалуйста, ваш собственный номер телефона.",
        reply_markup=kb
    )
    return WAIT_CONTACT

@rate_limited
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    user = update.effective_user
    # Защита от подмены чужого контакта:
    if not contact or contact.user_id != user.id:
        return await update.message.reply_text(
            "❌ Пожалуйста, используйте кнопку ☎️, чтобы отправить ваш собственный контакт."
        )
    phone_number = contact.phone_number
    # Никогда не шлём обратно телефон в виде обычного текста
    logging.info(f"[AUTH] User {user.id} ({user.username}) authorized with phone {phone_number}")
    await update.message.reply_text("✅ Вы успешно авторизованы! Спасибо.")
    return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await update.message.reply_text(
        "Пожалуйста, используйте кнопки для управления ботом."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок — чтобы бот не падал."""
    logging.error("Exception while handling an update:", exc_info=context.error)
    # можно уведомить администратора здесь, если нужно

def main() -> None:
    logging.basicConfig(
        format='%(asctime)s — %(name)s — %(levelname)s — %(message)s',
        level=logging.INFO
    )
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчик ошибок
    app.add_error_handler(error_handler)

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, action_choice)],
            SELECT_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_choice)],
            WAIT_CONTACT: [MessageHandler(filters.CONTACT, contact_handler)],
        },
        fallbacks=[MessageHandler(filters.ALL, fallback)],
        allow_reentry=True
    )
    app.add_handler(conv)

    # Не даём бот-апи обрабатывать всё подряд
    # Можно добавить и другие узкоспециализированные хендлеры здесь

    app.run_polling()

if __name__ == '__main__':
    main()
