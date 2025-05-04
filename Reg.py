import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = 'YOUR_BOT_TOKEN'
# Текст кнопки можно изменить здесь:
BUTTON_TEXT = '📞 Отправить мой номер телефона'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие и запрос номера телефона пользователя."""
    keyboard = [[KeyboardButton(text=BUTTON_TEXT, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    welcome_text = (
        f"👋 Привет, <b>{update.effective_user.first_name}</b>!\n\n"
        "Добро пожаловать в сервис <b>SocialIng</b>.\n"
        "Чтобы продолжить работу, нужно пройти быструю регистрацию.\n\n"
        "Нажмите кнопку ниже, чтобы безопасно отправить свой номер телефона."
    )

    await update.message.reply_html(welcome_text, reply_markup=reply_markup)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка полученного номера телефона."""
    contact = update.message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        # Вывод номера телефона в консоль
        print(f"Получен номер телефона: {phone_number}")

        confirm_text = (
            f"✅ Спасибо, <b>{update.effective_user.first_name}</b>!\n\n"
            f"Ваш номер <b>{phone_number}</b> сохранён. Регистрация завершена, можете пользоваться сервисом."
        )
        await update.message.reply_html(confirm_text)
    else:
        await update.message.reply_text(
            "Не удалось получить номер телефона. Попробуйте ещё раз, нажав кнопку ниже."
        )


def main() -> None:
    """Запуск бота."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
