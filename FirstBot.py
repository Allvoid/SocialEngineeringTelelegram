import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Замените 'YOUR_BOT_TOKEN' на токен бота
BOT_TOKEN = 'YOUR_BOT_TOKEN'
# Текст кнопки можно изменить здесь:
BUTTON_TEXT = 'Отправить мой номер телефона'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Кнопка для запроса контакта пользователя с настраиваемым текстом
    keyboard = [[KeyboardButton(text=BUTTON_TEXT, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        text="Привет! Пожалуйста, подтвердите ваш номер телефона:",
        reply_markup=reply_markup
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        # Вывод номера телефона в консоль
        print(f"Получен номер телефона: {phone_number}")
        await update.message.reply_text(f"Спасибо! Ваш номер {phone_number} получен.")
    else:
        await update.message.reply_text("Не удалось получить номер телефона.")


def main() -> None:
    # Включаем логирование
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Создаем приложение бота
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Запускаем бота
    app.run_polling()

if __name__ == '__main__':
    main()
