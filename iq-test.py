import logging
import time
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

import sys

TOKEN = sys.argv[1]

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
DOB, CONTACT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        await update.message.reply_text(
            "Добро пожаловать на *IQ-тест*!",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(
            "Привет! Чтобы подготовить тест для вас, укажи дату рождения.\n"
            "Формат: ДД.MM.ГГГГ"
        )
        return DOB
    except Exception as e:
        logger.exception("Error in start handler")
        # ничего не ломаем — завершаем разговор
        return ConversationHandler.END

async def dob_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        text = update.message.text.strip()
        dob = datetime.strptime(text, "%d.%m.%Y")
        context.user_data['dob'] = text

        button = KeyboardButton("☎️ Отправить номер", request_contact=True)
        markup = ReplyKeyboardMarkup(
            [[button]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Спасибо! Остался последний шаг для доступа к тестированию.\n"
            "Нажми кнопку 👇, чтобы безопасно передать свой номер телефона для регистрации.",
            reply_markup=markup
        )
        return CONTACT
    except ValueError:
        await update.message.reply_text(
            "Неверный формат. Пожалуйста, укажи дату в формате ДД.MM.ГГГГ"
        )
        return DOB
    except Exception as e:
        logger.exception("Error in dob_handler")
        return ConversationHandler.END

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        contact = update.message.contact
        if not contact or not contact.phone_number:
            # непредвиденный формат сообщения
            await update.message.reply_text("Не удалось получить контакт. Попробуйте ещё раз.")
            return CONTACT

        phone = contact.phone_number
        dob = context.user_data.get('dob', 'не указан')

        # Логируем (или обрабатываем) данные
        logger.info(f"User ID: {update.effective_user.id}, DOB: {dob}, Phone: {phone}")

        await update.message.reply_text(
            "Спасибо! Данные получены.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    except Exception as e:
        logger.exception("Error in contact_handler")
        await update.message.reply_text("Произошла ошибка при получении контакта.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        await update.message.reply_text(
            "Регистрация отменена.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception:
        pass
    return ConversationHandler.END

# общий обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    # если можем — предупредить пользователя
    if hasattr(update, "message") and update.message:
        try:
            await update.message.reply_text(
                "Упс! Что-то пошло не так. Пожалуйста, попробуйте снова позже."
            )
        except Exception:
            pass

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, dob_handler)],
            CONTACT: [MessageHandler(filters.CONTACT, contact_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    # Защита от падений: при исключении в run_polling автоматом перезапустим через 5 сек
    while True:
        try:
            app.run_polling()
        except Exception:
            logger.exception("Polling crashed — restarting in 5 seconds")
            time.sleep(5)

if __name__ == '__main__':
    main()
