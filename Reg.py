import logging
import time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

BOT_TOKEN = 'YOUR_BOT_TOKEN'
BUTTON_TEXT = '📞 Отправить мой номер телефона'

# 1) Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton(text=BUTTON_TEXT, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    welcome_text = (
        f"👋 Привет, <b>{update.effective_user.first_name}</b>!\n\n"
        "Добро пожаловать в сервис <b>SocialIng</b>.\n"
        "Чтобы продолжить работу, нужно пройти быструю регистрацию.\n\n"
        "Нажмите кнопку ниже, чтобы безопасно отправить свой номер телефона."
    )
    await update.message.reply_html(welcome_text, reply_markup=reply_markup)

# 2) Обработка контакта
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
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

# 3) Глобальный обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логируем любые непойманные исключения внутри хендлеров"""
    logging.error("Ошибка в обработчике:", exc_info=context.error)
    # опционально — уведомить админа или написать в чат, где появилась проблема:
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла внутренняя ошибка, но я продолжаю работать."
            )
    except Exception:
        pass  # на случай, если даже отправка сообщения упадёт

def main() -> None:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # регистрируем хендлеры
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    # регистрируем общий error handler
    app.add_error_handler(error_handler)

    # 4) Запускаем polling в петле с автоперезапуском
    while True:
        try:
            logging.info("Bot polling started")
            app.run_polling()
        except Exception as e:
            logging.error("Polling упал с ошибкой, перезапускаем через 5 сек.", exc_info=e)
            time.sleep(5)

if __name__ == '__main__':
    main()