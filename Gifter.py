
import logging
import time
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --------------------------- CONFIG ---------------------------

import sys

# Если при запуске передали токен, забираем его, иначе — None или какое-то значение по умолчанию
if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    TOKEN = '<ВАШ_ТОКЕН_ПО_УМОЛЧАНИЮ>'  # можно оставить None, если без токена бот не запускается


BUTTON_TEXT = "📲 Отправить мой номер"
WELCOME_TEXT = (
    "🎉 <b>Добро пожаловать в розыгрыш!</b>\n\n"
    "Чтобы стать участником, достаточно один раз отправить свой номер телефона.\n"
    "Нажмите кнопку ниже — Telegram предложит безопасно поделиться номером."
)
THANKS_TEMPLATE = (
    "✅ Спасибо, <b>{name}</b>!\n\n"
    "Ваш номер <b>{phone}</b> получен. Вы зарегистрированы {date}.\n"
    "Удачи в розыгрыше!"
)
ERROR_TEXT = (
    "❗️ Не удалось получить номер телефона.\n"
    "Пожалуйста, нажмите кнопку ещё раз либо проверьте настройки приватности."
)

# --------------------------- HANDLERS ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send greeting and show contact request button."""
    keyboard = [[KeyboardButton(text=BUTTON_TEXT, request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_html(WELCOME_TEXT, reply_markup=markup)


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle received phone number, print it to console, thank user."""
    contact = update.message.contact
    if contact and contact.phone_number:
        phone = contact.phone_number
        logging.info("New participant: %s (tg id %s)", phone, contact.user_id)

        confirm = THANKS_TEMPLATE.format(
            name=update.effective_user.first_name,
            phone=phone,
            date=datetime.now().strftime("%d.%m.%Y"),
        )
        await update.message.reply_html(confirm, reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(ERROR_TEXT)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logging.error("Exception while handling an update: %s", update, exc_info=context.error)


# --------------------------- MAIN ---------------------------

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_error_handler(error_handler)

    # Polling loop with auto‑restart on crash
    while True:
        try:
            application.run_polling()
        except Exception:
            logging.exception("Bot crashed, restarting in 5 seconds...")
            time.sleep(5)
        else:
            break


if __name__ == "__main__":
    main()
