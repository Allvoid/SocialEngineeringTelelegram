import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --------------------------- CONFIG ---------------------------
BOT_TOKEN = ""  # ← paste bot token here

BUTTON_TEXT = "📲 Отправить мой номер"
WELCOME_TEXT = (
    "🎉 <b>Добро пожаловать в розыгрыш!</b>\n\n"
    "Чтобы стать участником, достаточно один раз отправить свой номер телефона.\n"
    "Нажмите кнопку ниже — Telegram предложит безопасно поделиться номером."
)
THANKS_TEMPLATE = (
    "✅ Спасибо, <b>{name}</b>!\n\n"
    "Ваш номер <b>{phone}</b> получен. Вы зарегистрированы «{date}».\n"
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


# --------------------------- MAIN ---------------------------

def main() -> None:
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
