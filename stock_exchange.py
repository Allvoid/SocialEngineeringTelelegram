import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# Состояния разговора
SELECT_ACTION, SELECT_CURRENCY, WAIT_CONTACT = range(3)

# Кнопки для выбора действия
action_keyboard = [['Купить', 'Продать']]
action_markup = ReplyKeyboardMarkup(action_keyboard, one_time_keyboard=True, resize_keyboard=True)

# Список поддерживаемых криптовалют
CRYPTO_LIST = [
    'Bitcoin (BTC)',
    'Ethereum (ETH)',
    'Ripple (XRP)',
    'Litecoin (LTC)',
    'Dogecoin (DOGE)',
    # при желании добавьте ещё
]
crypto_keyboard = [CRYPTO_LIST[i:i+2] for i in range(0, len(CRYPTO_LIST), 2)]
crypto_markup = ReplyKeyboardMarkup(crypto_keyboard, one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 1: Приветствие и выбор действия (купить/продать)."""
    user_name = update.effective_user.first_name or "пользователь"
    text = (
        f"👋 Привет, <b>{user_name}</b>!\n\n"
        "Добро пожаловать в наш CryptoBot.\n"
        "Пожалуйста, выберите, что вы хотите сделать:"
    )
    await update.message.reply_html(text, reply_markup=action_markup)
    return SELECT_ACTION

async def action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 2: Пользователь выбрал купить или продать."""
    choice = update.message.text
    context.user_data['action'] = choice  # сохраним выбор
    # Пара примеров покупки/продажи
    examples = (
        "📊 Пример операций:\n"
        "- 0.005 BTC за 100 USD\n"
        "- 1 ETH за 2000 USD\n\n"
        f"Вы выбрали: <b>{choice}</b>.\n"
        "Теперь выберите криптовалюту:"
    )
    await update.message.reply_html(examples, reply_markup=crypto_markup)
    return SELECT_CURRENCY

async def currency_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 3: Пользователь выбрал криптовалюту."""
    crypto = update.message.text
    context.user_data['crypto'] = crypto
    # Здесь можно подставить реальный курс, но по ТЗ ставим заглушку
    text = (
        f"Вы выбрали: <b>{crypto}</b>\n"
        "Данный курс к USD: <b>???</b>\n\n"
        "Курс будет доступен после авторизации."
    )
    await update.message.reply_html(text)
    # Запрашиваем контакт для авторизации
    contact_button = KeyboardButton(text='📞 Отправить мой номер телефона', request_contact=True)
    contact_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Для продолжения авторизации отправьте, пожалуйста, номер телефона.",
        reply_markup=contact_markup
    )
    return WAIT_CONTACT

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 4: Обработка полученного номера — авторизация."""
    contact = update.message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        # Логируем номер, но не отвечаем пользователю (по ТЗ)
        logging.info(f"Авторизован пользователь с номером: {phone_number}")
    # Завершаем разговор (далее бот не реагирует)
    return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик на всякий случай, если пользователь уходит в неожиданный ввод."""
    await update.message.reply_text("Пожалуйста, используйте кнопки для управления ботом.")
    return

def main() -> None:
    """Запуск бота."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [
                MessageHandler(
                    filters.Regex('^(Купить|Продать)$'),
                    action_choice
                )
            ],
            SELECT_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, currency_choice)
            ],
            WAIT_CONTACT: [
                MessageHandler(filters.CONTACT, contact_handler)
            ],
        },
        fallbacks=[MessageHandler(filters.ALL, fallback)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()